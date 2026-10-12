"""Run Clanklin's voice, AI, speech, and movement loop."""

from ai_engine import AIEngine
from audio_pipeline import AudioPipeline
from comms_manager import CommsManager
from config import Config


def main() -> None:
    config = Config.from_env()
    ai = AIEngine(config)
    audio = AudioPipeline(config)
    comms = CommsManager(config.robot_host, config.robot_port, config.robot_timeout)
    print(f"Clanklin is ready. Robot endpoint: {config.robot_host}:{config.robot_port}")

    try:
        while True:
            try:
                transcript = audio.listen_and_transcribe(ai.client)
                print(f"You: {transcript}")
                reply = ai.respond(transcript)
                audio.speak(reply.response)
                comms.send_action(reply.action, reply.steps)
            except (OSError, RuntimeError, ValueError) as exc:
                print(f"Could not complete that turn: {exc}")
    except KeyboardInterrupt:
        print("\nStopping Clanklin.")
    finally:
        try:
            comms.send_action("IDLE")
        except OSError as exc:
            print(f"Could not send the shutdown idle command: {exc}")


if __name__ == "__main__":
    main()