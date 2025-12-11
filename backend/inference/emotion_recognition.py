import os
import numpy as np
import joblib
import librosa

from backend.features.yamnet_extract import extract_yamnet_embedding

# === 路径 ===
MODEL_PATH = "backend/models/emotion_model.pkl"

# === 加载模型 ===
emotion_model = joblib.load(MODEL_PATH)

# === 你自己的标签顺序 ===
emotion_labels = [
    "angry",
    "funny",
    "happy",
    "sad",
    "scary",
    "tender"
]


def predict_emotion(audio_path: str):
    """
    输入音频路径，返回:
        emotion_label: str
        prob_dict: dict[label -> prob]
    """

    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # 1. 提取 YAMNet embedding
    embedding = extract_yamnet_embedding(audio_path)

    # 2. 平均多帧（训练一致）
    if len(embedding.shape) > 1:
        embedding = embedding.mean(axis=0)

    embedding = embedding.reshape(1, -1)

    # 3. 预测类别
    pred_idx = emotion_model.predict(embedding)[0]
    emotion = emotion_labels[pred_idx]

    # 4. 预测概率（XGBoost / sklearn 模型支持 predict_proba）
    try:
        prob = emotion_model.predict_proba(embedding)[0]
        prob_dict = {emotion_labels[i]: float(prob[i]) for i in range(len(emotion_labels))}
    except Exception:
        # 万一模型没有 prob 能力（不太可能）
        prob_dict = {emotion_labels[i]: (1.0 if i == pred_idx else 0.0) for i in range(len(emotion_labels))}

    return emotion, prob_dict


if __name__ == "__main__":
    test_audio = "backend/test_audio.wav"

    print("🔍 正在分析情绪...")
    emotion, prob = predict_emotion(test_audio)
    print(f"🎵 识别结果：{emotion}")
    print(f"概率分布：{prob}")
