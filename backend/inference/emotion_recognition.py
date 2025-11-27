<<<<<<< HEAD
<<<<<<< HEAD
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
    """输入音频路径，返回情绪名称"""

    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # 1. 提取 YAMNet embedding
    embedding = extract_yamnet_embedding(audio_path)

    # 2. 有些 embedding 是多帧，取平均（训练时也是这么做的）
    if len(embedding.shape) > 1:
        embedding = embedding.mean(axis=0)

    embedding = embedding.reshape(1, -1)

    # 3. 模型预测
    pred_idx = emotion_model.predict(embedding)[0]
    emotion = emotion_labels[pred_idx]

    return emotion


if __name__ == "__main__":
    test_audio = "backend/test_audio.wav"

    print("🔍 正在分析情绪...")
    emotion = predict_emotion(test_audio)
    print(f"🎵 识别结果：{emotion}")
=======
import os
import numpy as np
=======
>>>>>>> 368ab93 (need_test_try)
import joblib
import librosa
import numpy as np

MODEL_PATH = "backend/models/emotion_model.pkl"
model = joblib.load(MODEL_PATH)


def extract_emotion_features(path):
    y, sr = librosa.load(path, sr=None, mono=True)
    mel = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=40)
    return mel.mean(axis=1).reshape(1, -1)


<<<<<<< HEAD
if __name__ == "__main__":
    test_audio = "backend/test_audio.wav"

    print("🔍 正在分析情绪...")
    emotion, prob = predict_emotion(test_audio)
    print(f"🎵 识别结果：{emotion}")
    print(f"概率分布：{prob}")
>>>>>>> 0cf27b1 (failed_v4)
=======
def predict_emotion(path):
    feat = extract_emotion_features(path)
    prob = model.predict_proba(feat)[0]
    idx = np.argmax(prob)
    emo = model.classes_[idx]
    return emo, prob.tolist()
>>>>>>> 368ab93 (need_test_try)
