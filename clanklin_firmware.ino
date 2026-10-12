#include <Arduino.h>
#include <ArduinoJson.h>
#include <Adafruit_PWMServoDriver.h>
#include <WiFi.h>
#include <Wire.h>

namespace {
constexpr char AP_SSID[] = "Clanklin-Robot";
constexpr char AP_PASSWORD[] = "change-this-password";
constexpr uint16_t TCP_PORT = 8765;
constexpr uint8_t SERVO_COUNT = 12;
constexpr uint16_t SERVO_MIN_US = 500;
constexpr uint16_t SERVO_MAX_US = 2500;
constexpr uint8_t SERVO_FREQUENCY = 50;
constexpr uint16_t INTERPOLATION_MS = 20;
constexpr uint16_t MOVE_MS = 350;
constexpr uint8_t MAX_STEPS = 20;

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(0x40);
WiFiServer server(TCP_PORT);
int currentPose[SERVO_COUNT] = {
    90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90};

uint16_t pulseForAngle(int angle) {
  const int bounded = constrain(angle, 0, 180);
  const uint32_t pulseUs = SERVO_MIN_US +
      (static_cast<uint32_t>(bounded) * (SERVO_MAX_US - SERVO_MIN_US)) / 180;
  return static_cast<uint16_t>((pulseUs * 4096UL * SERVO_FREQUENCY) / 1000000UL);
}

void writePose(const int pose[SERVO_COUNT]) {
  for (uint8_t channel = 0; channel < SERVO_COUNT; ++channel) {
    const int angle = constrain(pose[channel], 0, 180);
    pwm.setPWM(channel, 0, pulseForAngle(angle));
  }
}

void moveTo(const int target[SERVO_COUNT], uint16_t durationMs = MOVE_MS) {
  const uint16_t requestedFrames = durationMs / INTERPOLATION_MS;
  const uint16_t frames = requestedFrames == 0 ? 1 : requestedFrames;
  int start[SERVO_COUNT];
  memcpy(start, currentPose, sizeof(start));

  for (uint16_t frame = 1; frame <= frames; ++frame) {
    int interpolated[SERVO_COUNT];
    for (uint8_t channel = 0; channel < SERVO_COUNT; ++channel) {
      interpolated[channel] = start[channel] +
          (static_cast<int>(target[channel]) - start[channel]) * frame / frames;
      currentPose[channel] = interpolated[channel];
    }
    writePose(interpolated);
    delay(INTERPOLATION_MS);
  }
}

void stand() {
  const int pose[SERVO_COUNT] = {
      90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90};
  moveTo(pose);
}

void walk(const String& direction, uint8_t steps) {
  int strideByLeg[4] = {1, 1, 1, 1};
  if (direction == "backward") {
    for (int& stride : strideByLeg) stride = -1;
  } else if (direction == "left") {
    strideByLeg[0] = strideByLeg[2] = -1;
  } else if (direction == "right") {
    strideByLeg[1] = strideByLeg[3] = -1;
  }

  for (uint8_t step = 0; step < steps; ++step) {
    for (uint8_t leg = 0; leg < 4; ++leg) {
      int lifted[SERVO_COUNT];
      memcpy(lifted, currentPose, sizeof(lifted));
      const uint8_t base = leg * 3;
      const int swing = strideByLeg[leg];
      lifted[base] = 90 + 20 * swing;
      lifted[base + 1] = 65;
      moveTo(lifted, MOVE_MS / 2);

      int planted[SERVO_COUNT];
      memcpy(planted, currentPose, sizeof(planted));
      planted[base] = 90 - 20 * swing;
      planted[base + 1] = 90;
      moveTo(planted, MOVE_MS / 2);
    }
  }
  stand();
}

void wave() {
  int seated[SERVO_COUNT] = {
      90, 90, 90, 90, 90, 90, 90, 125, 120, 90, 125, 120};
  moveTo(seated);

  int raised[SERVO_COUNT];
  memcpy(raised, seated, sizeof(raised));
  raised[1] = 55;
  raised[2] = 125;
  moveTo(raised);
  for (uint8_t count = 0; count < 3; ++count) {
    int wavePose[SERVO_COUNT];
    memcpy(wavePose, raised, sizeof(wavePose));
    wavePose[0] = count % 2 == 0 ? 70 : 110;
    moveTo(wavePose, 220);
  }
  stand();
}

void executeCommand(const char* json) {
  StaticJsonDocument<256> document;
  if (deserializeJson(document, json)) {
    Serial.println("Rejected malformed JSON");
    return;
  }

  String action = document["action"] | "";
  action.toLowerCase();
  if (action == "walk") {
    String direction = document["direction"] | "";
    direction.toLowerCase();
    if (direction != "forward" && direction != "backward" &&
        direction != "left" && direction != "right") {
      Serial.println("Rejected invalid walk direction");
      return;
    }
    const int requestedSteps = document["steps"] | 1;
    if (requestedSteps < 1 || requestedSteps > MAX_STEPS) {
      Serial.println("Rejected invalid step count");
      return;
    }
    walk(direction, static_cast<uint8_t>(requestedSteps));
  } else if (action == "idle") {
    stand();
  } else if (action == "wave") {
    wave();
  } else if (action == "forward" || action == "backward" ||
             action == "left" || action == "right") {
    const int requestedSteps = document["steps"] | 1;
    if (requestedSteps < 1 || requestedSteps > MAX_STEPS) return;
    walk(action, static_cast<uint8_t>(requestedSteps));
  } else {
    Serial.println("Rejected unknown action");
  }
}

void handleClient(WiFiClient& client) {
  char line[256];
  size_t length = 0;
  const uint32_t startedAt = millis();
  bool complete = false;
  while (client.connected() && millis() - startedAt < 1500 && !complete) {
    while (client.available()) {
      const char character = static_cast<char>(client.read());
      if (character == '\n') {
        complete = true;
        break;
      }
      if (length < sizeof(line) - 1) line[length++] = character;
    }
    delay(1);
  }
  if (complete && length > 0) {
    line[length] = '\0';
    executeCommand(line);
  }
  client.stop();
}
}  // namespace

void setup() {
  Serial.begin(115200);
  Wire.begin();
  pwm.begin();
  pwm.setPWMFreq(SERVO_FREQUENCY);
  delay(10);
  writePose(currentPose);

  WiFi.mode(WIFI_AP);
  if (!WiFi.softAP(AP_SSID, AP_PASSWORD)) {
    Serial.println("Failed to start robot access point");
    while (true) delay(1000);
  }
  server.begin();
  Serial.print("Robot Wi-Fi ready at ");
  Serial.println(WiFi.softAPIP());
  stand();
}

void loop() {
  WiFiClient client = server.available();
  if (client) handleClient(client);
}