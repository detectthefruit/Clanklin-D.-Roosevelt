"""Groq chat integration and strict validation of the model response."""

from dataclasses import dataclass
import json


ALLOWED_ACTIONS = {"FORWARD", "BACKWARD", "LEFT", "RIGHT", "WAVE", "IDLE"}
SYSTEM_PROMPT = (
    "You are Clanklin D. Roosevelt, a witty quadruped robot. Reply with one brief, "
    "conversational sentence and exactly one movement command chosen from FORWARD, "
    "BACKWARD, LEFT, RIGHT, WAVE, IDLE. Return only a JSON object with keys "
    '"response" (a string) and "action" (one allowed command). You may include '
    '"steps" (an integer from 1 to 20) for movement actions. Never return other keys.'
)


@dataclass(frozen=True)
class RobotReply:
    response: str
    action: str
    steps: int = 1


def parse_reply(content: str) -> RobotReply:
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError("AI response was not valid JSON") from exc
    if not isinstance(data, dict):
        raise ValueError("AI response must be a JSON object")

    response = data.get("response")
    action = data.get("action")
    steps = data.get("steps", 1)
    if not isinstance(response, str) or not response.strip() or len(response) > 240:
        raise ValueError("AI response text must contain 1 to 240 characters")
    if not isinstance(action, str) or action.upper() not in ALLOWED_ACTIONS:
        raise ValueError("AI movement action is not allowed")
    if isinstance(steps, bool) or not isinstance(steps, int) or not 1 <= steps <= 20:
        raise ValueError("AI movement steps must be an integer from 1 to 20")
    return RobotReply(response=response.strip(), action=action.upper(), steps=steps)


class AIEngine:
    def __init__(self, config):
        if not config.groq_api_key:
            raise ValueError("Set GROQ_API_KEY before starting the voice assistant")
        try:
            from groq import Groq
        except ImportError as exc:
            raise RuntimeError("Install Groq with `python -m pip install -r requirements.txt`.") from exc
        self._client = Groq(api_key=config.groq_api_key)
        self._model = config.groq_model

    @property
    def client(self):
        return self._client

    def respond(self, transcript: str) -> RobotReply:
        completion = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": transcript},
            ],
            response_format={"type": "json_object"},
            temperature=0.6,
            max_tokens=160,
        )
        return parse_reply(completion.choices[0].message.content or "")