"""Local microphone capture and speech playback, with Groq transcription."""


class AudioPipeline:
    def __init__(self, config):
        try:
            import pyttsx3
            import speech_recognition as sr
        except ImportError as exc:
            raise RuntimeError(
                "Install the audio dependencies with `python -m pip install -r requirements.txt`."
            ) from exc

        self._sr = sr
        self._recognizer = sr.Recognizer()
        self._recognizer.energy_threshold = config.audio_energy_threshold
        self._audio_timeout = config.audio_timeout
        self._phrase_limit = config.audio_phrase_limit
        self._transcription_model = config.transcription_model
        self._tts = pyttsx3.init()

    def listen_and_transcribe(self, groq_client) -> str:
        try:
            with self._sr.Microphone() as microphone:
                print("Listening...")
                self._recognizer.adjust_for_ambient_noise(microphone, duration=0.4)
                audio = self._recognizer.listen(
                    microphone,
                    timeout=self._audio_timeout,
                    phrase_time_limit=self._phrase_limit,
                )
        except self._sr.WaitTimeoutError:
            raise RuntimeError("No speech detected; listening again") from None

        wav_data = audio.get_wav_data()
        result = groq_client.audio.transcriptions.create(
            file=("clanklin-input.wav", wav_data),
            model=self._transcription_model,
            response_format="text",
        )
        transcript = result if isinstance(result, str) else result.text
        transcript = transcript.strip()
        if not transcript:
            raise ValueError("Speech transcription was empty")
        return transcript

    def speak(self, text: str) -> None:
        self._tts.say(text)
        self._tts.runAndWait()