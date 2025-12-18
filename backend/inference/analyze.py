<<<<<<< HEAD
<<<<<<< HEAD
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
=======
# backend/inference/analyze.py

from pathlib import Path
=======
>>>>>>> 368ab93 (need_test_try)
from .emotion_recognition import predict_emotion
from .style_recognition import predict_style
from .melody_extractor import MelodyExtractor


class Analyzer:

    def __init__(self):
        self.melody_extractor = MelodyExtractor()

    def analyze_melody(self, path):
        return self.melody_extractor.extract(path)

    def analyze(self, path):
        style, style_prob = predict_style(path)
        emotion, emotion_prob = predict_emotion(path)
        melody = self.analyze_melody(path)

        return {
            "style": style,
            "style_prob": style_prob,
            "emotion": emotion,
            "emotion_prob": emotion_prob,
            "melody": melody
        }
<<<<<<< HEAD


# 全局单例
analyzer = Analyzer()
>>>>>>> 0cf27b1 (failed_v4)
=======
>>>>>>> 368ab93 (need_test_try)
