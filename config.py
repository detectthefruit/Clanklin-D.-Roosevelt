"""Environment-backed configuration for the Clanklin host."""

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Config:
    groq_api_key: str
    groq_model: str
    transcription_model: str
    robot_host: str
    robot_port: int
    robot_timeout: float
    audio_energy_threshold: int
    audio_timeout: float
    audio_phrase_limit: float

    @classmethod
    def from_env(cls) -> "Config":
        config = cls(
            groq_api_key=os.getenv("GROQ_API_KEY", ""),
            groq_model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            transcription_model=os.getenv(
                "GROQ_TRANSCRIPTION_MODEL", "whisper-large-v3-turbo"
            ),
            robot_host=os.getenv("ROBOT_HOST", "192.168.4.1"),
            robot_port=int(os.getenv("ROBOT_PORT", "8765")),
            robot_timeout=float(os.getenv("ROBOT_TIMEOUT", "3")),
            audio_energy_threshold=int(os.getenv("AUDIO_ENERGY_THRESHOLD", "300")),
            audio_timeout=float(os.getenv("AUDIO_TIMEOUT", "5")),
            audio_phrase_limit=float(os.getenv("AUDIO_PHRASE_LIMIT", "12")),
        )
        if not 1 <= config.robot_port <= 65535:
            raise ValueError("ROBOT_PORT must be between 1 and 65535")
        if config.robot_timeout <= 0 or config.audio_timeout <= 0:
            raise ValueError("Timeouts must be greater than zero")
        if config.audio_phrase_limit <= 0 or config.audio_energy_threshold < 0:
            raise ValueError("Audio limits must be positive")
        return config