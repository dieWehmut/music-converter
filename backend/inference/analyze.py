<<<<<<< HEAD
# backend/inference/analyze.py

from pathlib import Path
from .emotion_recognition import predict_emotion
from .style_recognition import predict_style


class Analyzer:
    def __init__(self):
        self.root = Path(__file__).resolve().parent.parent

    def analyze(self, audio_path: str) -> dict:
        audio_path = str(audio_path)

        try:
            # 风格、概率
            style, style_prob = predict_style(audio_path)

            # 情绪、概率
            emotion, emotion_prob = predict_emotion(audio_path)

            # Ensure all probabilities and array-like values are converted to plain Python types
            def _normalize_prob(d):
                out = {}
                for k, v in (d or {}).items():
                    # if it's a numpy scalar or array, try to convert
                    try:
                        if hasattr(v, "tolist"):
                            vv = v.tolist()
                        else:
                            vv = v
                        # if vv is a list/tuple/ndarray, convert elements to float
                        if isinstance(vv, (list, tuple)):
                            out[k] = [float(x) for x in vv]
                        else:
                            out[k] = float(vv)
                    except Exception:
                        # fallback to string representation
                        out[k] = v
                return out

            style_prob_clean = _normalize_prob(style_prob)
            emotion_prob_clean = _normalize_prob(emotion_prob)

            return {
                "style": str(style),
                "emotion": str(emotion),
                "style_prob": style_prob_clean,
                "emotion_prob": emotion_prob_clean
            }

        except Exception as e:
            # Return an error-like dict so API can convey the issue
            return {"error": f"analyze failed: {e}"}


# 全局单例
analyzer = Analyzer()
=======
# backend/inference/analyze.py

from pathlib import Path
from .emotion_recognition import predict_emotion
from .style_recognition import predict_style


class Analyzer:
    def __init__(self):
        self.root = Path(__file__).resolve().parent.parent

    def analyze(self, audio_path: str) -> dict:
        audio_path = str(audio_path)

        # 风格、概率
        style, style_prob = predict_style(audio_path)

        # 情绪、概率
        emotion, emotion_prob = predict_emotion(audio_path)

        return {
            "style": style,
            "emotion": emotion,
            "style_prob": style_prob,
            "emotion_prob": emotion_prob
        }


# 全局单例
analyzer = Analyzer()
>>>>>>> 0cf27b1 (failed_v4)
