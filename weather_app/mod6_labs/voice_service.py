"""Voice recognition and text-to-speech service for the Weather App."""
import asyncio
import threading
from typing import Optional, Callable
try:
    import speech_recognition as sr
    import pyttsx3
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False
    sr = None
    pyttsx3 = None


class VoiceServiceError(Exception):
    """Custom exception for voice service errors."""
    pass


class VoiceService:
    """Service for voice recognition and text-to-speech."""
    
    def __init__(self):
        if not VOICE_AVAILABLE:
            raise VoiceServiceError(
                "Voice services not available. Install: pip install SpeechRecognition pyttsx3 pyaudio"
            )
        
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 4000
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        
        # Initialize TTS engine in a separate thread
        self.tts_engine = None
        self._init_tts()
    
    def _init_tts(self):
        """Initialize text-to-speech engine."""
        try:
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 150)  # Speed
            self.tts_engine.setProperty('volume', 0.9)  # Volume
        except Exception as e:
            print(f"TTS initialization warning: {e}")
    
    async def listen_for_city(self, timeout: int = 5) -> str:
        """Listen for city name via microphone.
        
        Args:
            timeout: Maximum time to wait for speech (seconds).
        
        Returns:
            Recognized city name as string.
        
        Raises:
            VoiceServiceError: If recognition fails or times out.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._listen_sync, timeout)
    
    def _listen_sync(self, timeout: int) -> str:
        """Synchronous listening implementation."""
        try:
            with sr.Microphone() as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # Listen for audio
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=5)
                
                # Recognize speech using Google Speech Recognition
                text = self.recognizer.recognize_google(audio)
                return text.strip()
                
        except sr.WaitTimeoutError:
            raise VoiceServiceError("No speech detected. Please try again.")
        except sr.UnknownValueError:
            raise VoiceServiceError("Could not understand audio. Please speak clearly.")
        except sr.RequestError as e:
            raise VoiceServiceError(f"Speech recognition service error: {e}")
        except Exception as e:
            raise VoiceServiceError(f"Microphone error: {str(e)}")
    
    async def speak(self, text: str):
        """Speak text using text-to-speech.
        
        Args:
            text: Text to speak.
        """
        if not self.tts_engine:
            return
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._speak_sync, text)
    
    def _speak_sync(self, text: str):
        """Synchronous speech implementation."""
        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            print(f"TTS error: {e}")
    
    def test_microphone(self) -> bool:
        """Test if microphone is available.
        
        Returns:
            True if microphone is accessible, False otherwise.
        """
        try:
            with sr.Microphone() as source:
                return True
        except Exception:
            return False
    
    @staticmethod
    def is_available() -> bool:
        """Check if voice services are available."""
        return VOICE_AVAILABLE
    
    def format_weather_speech(self, data: dict, unit: str = "metric") -> str:
        """Format weather data for speech output.
        
        Args:
            data: Weather data dictionary.
            unit: Temperature unit ('metric' or 'imperial').
        
        Returns:
            Formatted speech text.
        """
        city = data.get("name", "Unknown")
        temp = data.get("main", {}).get