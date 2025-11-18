import os
import joblib
import numpy as np
from pathlib import Path
import librosa
import scipy.signal

# 修复 hann
if not hasattr(scipy.signal, "hann"):
    scipy.signal.hann = scipy.signal.windows.hann

# === 引入你上传的 emotion & style 代码 ===
from backend.features.yamnet_extract import extract_yamnet_embedding
from .style_recognition import extract_style_features  # 保证 68 维一致


class Analyzer:
    """后端统一分析器：负责 Emotion + Style 推理，模型只加载一次"""

    def __init__(self):
        ROOT = Path(__file__).resolve().parent.parent

        # ===== Emotion =====
        self.emotion_model_path = ROOT / "models" / "emotion_model.pkl"
        self.emotion_labels = [
            "angry",
            "funny",
            "happy",
            "sad",
            "scary",
            "tender"
        ]

        print("🔍 正在加载 Emotion 模型...")
        self.emotion_model = joblib.load(self.emotion_model_path)
        print("Emotion 模型加载完成！")

        # ===== Style =====
        self.style_model_path = ROOT / "models" / "style_model.pkl"
        self.style_encoder_path = ROOT / "models" / "style_label_encoder.pkl"

        print("🎸 正在加载 Style 模型与标签编码器...")
        self.style_model = joblib.load(self.style_model_path)
        self.style_encoder = joblib.load(self.style_encoder_path)
        print("Style 模型加载完成！")

    # ------------------------------------------------
    # Emotion 预测
    # ------------------------------------------------
    def predict_emotion(self, audio_path: str) -> str:
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio not found: {audio_path}")

        emb = extract_yamnet_embedding(audio_path)

        if len(emb.shape) > 1:
            emb = emb.mean(axis=0)

        emb = emb.reshape(1, -1)

        pred_idx = self.emotion_model.predict(emb)[0]
        return self.emotion_labels[pred_idx]

    # ------------------------------------------------
    # Style 预测
    # ------------------------------------------------
    def predict_style(self, audio_path: str) -> str:
        feat = extract_style_features(audio_path)
        pred = self.style_model.predict(feat)[0]
        return self.style_encoder.inverse_transform([pred])[0]

    # ------------------------------------------------
    # 总接口：一次返回两者
    # ------------------------------------------------
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
