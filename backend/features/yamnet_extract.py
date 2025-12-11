# backend/features/yamnet_extract.py

import os
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
import librosa

# ==============================
# 🔥 YAMNet 模型句柄 (智能判断)
# ==============================
def get_yamnet_handle():
    """
    优先查找本地模型，如果不存在则使用在线 URL
    本地路径应为: backend/models/yamnet/
    """
    # 1. 计算本地模型目录的绝对路径
    # 当前文件在 backend/features/，所以模型在 ../models/yamnet
    current_dir = os.path.dirname(os.path.abspath(__file__))
    local_model_path = os.path.abspath(os.path.join(current_dir, "../models/yamnet"))
    
    # 2. 在线 URL (作为备选)
    online_url = "https://tfhub.dev/google/yamnet/1"

    # 3. 检查本地是否存在 saved_model.pb (TensorFlow 模型的标志文件)
    if os.path.exists(os.path.join(local_model_path, "saved_model.pb")):
        print(f"[YAMNet] ✅ Found local model at: {local_model_path}")
        return local_model_path
    else:
        print(f"[YAMNet] ⚠️ Local model not found at {local_model_path}")
        print(f"[YAMNet] 🔄 Fallback to online URL: {online_url}")
        return online_url

# 获取最终的路径或URL
YAMNET_MODEL_HANDLE = get_yamnet_handle()

_yamnet = None


def load_yamnet():
    """
    懒加载 YAMNet（只加载一次）
    """
    global _yamnet
    if _yamnet is None:
        print(f"Loading YAMNet model from: {YAMNET_MODEL_HANDLE} ...")
        try:
            _yamnet = hub.load(YAMNET_MODEL_HANDLE)
            print("YAMNet loaded successfully!")
        except Exception as e:
            print(f"❌ Failed to load YAMNet: {e}")
            # 如果是本地加载失败，可能是文件损坏，或者环境问题
            raise e
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
    # 确保路径存在
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

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
    # 计算 test_audio.wav 的绝对路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_audio = os.path.abspath(
        os.path.join(current_dir, "..", "test_audio.wav")
    )

    print("使用的音频路径：", test_audio)
    
    # 如果没有测试文件，创建一个假的，防止报错
    if not os.path.exists(test_audio):
        print("⚠️ 测试音频不存在，生成静音文件用于测试...")
        import soundfile as sf
        dummy_audio = np.zeros(16000*3) # 3秒静音
        sf.write(test_audio, dummy_audio, 16000)

    try:
        emb = extract_yamnet_embedding(test_audio)
        print("Embedding shape:", emb.shape)
        print("✅ 测试成功！")
    except Exception as e:
        print(f"❌ 测试失败: {e}")