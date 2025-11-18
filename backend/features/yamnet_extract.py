# backend/features/yamnet_extract.py

import os
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
import librosa

# ==============================
# 🔥 YAMNet 模型（懒加载）
# ==============================
YAMNET_MODEL_HANDLE = "https://tfhub.dev/google/yamnet/1"
_yamnet = None


def load_yamnet():
    """
    懒加载 YAMNet（只加载一次）
    """
    global _yamnet
    if _yamnet is None:
        print("🎧 Loading YAMNet model ...")
        _yamnet = hub.load(YAMNET_MODEL_HANDLE)
        print("✅ YAMNet loaded successfully!")
    return _yamnet


# ==============================
# 🔥 提取 YAMNet embedding（最终统一版）
# ==============================
def extract_yamnet_embedding(audio_path, target_sr=16000):
    """
    输入：音频路径（wav/mp3）
    输出：长度为 1024 的 embedding（np.array）
    工作流程：
        1. librosa 读取音频（自动转 mono）
        2. 重采样到 16kHz
        3. YAMNet 输出多帧 embedding
        4. 对所有帧取平均（稳定输入）
    """

    yamnet = load_yamnet()

    # ---------------------------
    # ① 使用 librosa 读取音频
    # ---------------------------
    y, sr = librosa.load(audio_path, sr=target_sr, mono=True)

    # ---------------------------
    # ② 转为 Tensor
    # ---------------------------
    waveform = tf.constant(y, dtype=tf.float32)

    # ---------------------------
    # ③ 调用 YAMNet
    #     outputs = (scores, embeddings, spectrogram)
    # ---------------------------
    _, embeddings, _ = yamnet(waveform)

    # shape = (时间帧数, 1024)
    embeddings = embeddings.numpy()

    # ---------------------------
    # ④ 对所有帧求平均，得到固定维度 embedding
    # ---------------------------
    emb = np.mean(embeddings, axis=0)

    return emb  # np.array shape=(1024,)


# ==============================
# 🔥 单文件测试
# ==============================

if __name__ == "__main__":
    # 计算 test_audio.wav 的绝对路径（你当前的真实位置）
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_audio = os.path.abspath(
        os.path.join(current_dir, "..", "test_audio.wav")
    )

    print("使用的音频路径：", test_audio)
    print("是否存在：", os.path.exists(test_audio))

    emb = extract_yamnet_embedding(test_audio)
    print("Embedding shape:", emb.shape)

