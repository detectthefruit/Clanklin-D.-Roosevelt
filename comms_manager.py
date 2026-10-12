"""TCP command transport for the ESP32 firmware."""

import json
import socket


class CommsManager:
    def __init__(self, host: str, port: int, timeout: float = 3):
        self.host = host
        self.port = port
        self.timeout = timeout

    @staticmethod
    def build_payload(action: str, steps: int = 1) -> dict:
        normalized = action.upper()
        if normalized not in {"FORWARD", "BACKWARD", "LEFT", "RIGHT", "WAVE", "IDLE"}:
            raise ValueError(f"Unsupported movement action: {action}")
        if isinstance(steps, bool) or not isinstance(steps, int) or not 1 <= steps <= 20:
            raise ValueError("steps must be an integer from 1 to 20")
        if normalized in {"FORWARD", "BACKWARD", "LEFT", "RIGHT"}:
            return {
                "action": "walk",
                "direction": normalized.lower(),
                "steps": steps,
            }
        return {"action": normalized.lower()}

    def send_action(self, action: str, steps: int = 1) -> None:
        payload = self.build_payload(action, steps)
        wire_data = (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")
        with socket.create_connection((self.host, self.port), self.timeout) as connection:
            connection.sendall(wire_data)