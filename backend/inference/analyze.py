# backend/inference/analyze.py

from pathlib import Path
from .emotion_recognition import predict_emotion
from .style_recognition import predict_style


class Analyzer:
    def __init__(self):
        self.root = Path(__file__).resolve().parent.parent

    def analyze(self, audio_path: str) -> dict:
        emotion = self.predict_emotion(audio_path)
        style = self.predict_style(audio_path)

        return {
            "emotion": emotion,
            "style": style
        }


# ================================================
#   单例：给 FastAPI 使用
# ================================================
analyzer = Analyzer()
