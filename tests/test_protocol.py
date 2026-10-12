import json
import unittest

from ai_engine import parse_reply
from comms_manager import CommsManager


class ParseReplyTests(unittest.TestCase):
    def test_accepts_allowed_command_and_limits_steps(self):
        reply = parse_reply(
            '{"response":"Forward, with purpose!","action":"forward","steps":3}'
        )
        self.assertEqual(reply.action, "FORWARD")
        self.assertEqual(reply.steps, 3)

    def test_rejects_unknown_command_and_unbounded_steps(self):
        for body in (
            '{"response":"Hi","action":"dance"}',
            '{"response":"Hi","action":"WAVE","steps":21}',
        ):
            with self.subTest(body=body), self.assertRaises(ValueError):
                parse_reply(body)


class CommsPayloadTests(unittest.TestCase):
    def test_walk_command_matches_firmware_contract(self):
        payload = CommsManager.build_payload("LEFT", 2)
        self.assertEqual(
            json.dumps(payload, separators=(",", ":")),
            '{"action":"walk","direction":"left","steps":2}',
        )

    def test_non_walk_command_has_no_step_count(self):
        self.assertEqual(CommsManager.build_payload("WAVE"), {"action": "wave"})

    def test_rejects_invalid_steps(self):
        with self.assertRaises(ValueError):
            CommsManager.build_payload("FORWARD", 0)


if __name__ == "__main__":
    unittest.main()