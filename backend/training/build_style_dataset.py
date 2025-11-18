import os
import json
import librosa
import numpy as np
import scipy.signal

# ========= 修复 scipy.signal.hann 被移除的问题 =========
if not hasattr(scipy.signal, "hann"):
    scipy.signal.hann = scipy.signal.windows.hann

# ========= Librosa 预热（避免第一次加载卡住） =========
try:
    y_pre = np.random.randn(22050)
    librosa.feature.melspectrogram(y=y_pre, sr=22050, n_mels=40)
    librosa.feature.chroma_stft(y=y_pre, sr=22050)
    librosa.feature.spectral_contrast(y=y_pre, sr=22050)
    librosa.feature.tonnetz(y=librosa.effects.harmonic(y_pre), sr=22050)
    print("🔧 Librosa 预热完成")
except Exception as e:
    print("预热失败:", e)


# ========= GTZAN 数据集路径 =========
GTZAN_PATH = r"C:\Users\33529\Desktop\music\archive\Data\genres_original"

OUTPUT_JSON = "backend/dataset_open/style_dataset.json"


# ========= 5类风格映射 =========
style_map = {
    "pop": ["pop", "disco", "country"],
    "rock": ["rock", "metal", "blues"],
    "jazz": ["jazz"],
    "classical": ["classical"],
    "electronic": ["hiphop", "reggae"]
}

reverse_map = {}
for new_label, old_list in style_map.items():
    for o in old_list:
        reverse_map[o] = new_label


# ========= 加载音频（带 5 秒超时保护） =========
def safe_load(path, timeout=5):
    import threading

    result = {}

    def load():
        try:
            y, sr = librosa.load(path, sr=None)
            result["audio"] = (y, sr)
        except Exception as e:
            result["error"] = e

    thread = threading.Thread(target=load)
    thread.start()
    thread.join(timeout)

    if thread.is_alive():
        return None, None, "timeout"

    if "error" in result:
        return None, None, result["error"]

    return result["audio"][0], result["audio"][1], None


# ========= 核心：68维特征提取函数 =========
def extract_features(path):
    y, sr, err = safe_load(path, timeout=5)

    if err is not None or y is None:
        raise Exception(f"音频加载失败: {err}")

    if len(y) < sr:
        y = np.pad(y, (0, sr - len(y)))

    # 1. tempo（节奏）
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)

    # 2. RMS（能量）
    rms = librosa.feature.rms(y=y)[0].mean()

    # 3. spectral centroid（亮度）
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0].mean()

    # 4. chroma（12 维）
    chroma = librosa.feature.chroma_stft(y=y, sr=sr).mean(axis=1)

    # 5. mel（40 维）
    mel = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=40)
    mel_mean = mel.mean(axis=1)

    # 6. spectral contrast（7 维）
    contrast = librosa.feature.spectral_contrast(y=y, sr=sr).mean(axis=1)

    # 7. tonnetz（6 维）
    try:
        tonnetz = librosa.feature.tonnetz(
            y=librosa.effects.harmonic(y),
            sr=sr
        ).mean(axis=1)
    except Exception:
        tonnetz = np.zeros(6)

    # === 拼接成最终 68 维特征 ===
    feature = np.concatenate([
        [tempo, rms, centroid],
        chroma,
        mel_mean,
        contrast,
        tonnetz
    ])

    return feature.tolist()


# ========= 构建数据集 =========
def build():
    dataset = []

    for old_label in reverse_map.keys():
        folder = os.path.join(GTZAN_PATH, old_label)

        if not os.path.isdir(folder):
            print("❌ 目录不存在:", folder)
            continue

        print(f"\n📂 正在处理类别: {old_label}")

        for file in os.listdir(folder):
            if not file.endswith(".wav"):
                continue

            full_path = os.path.join(folder, file)

            print("▶ 处理:", full_path)

            try:
                feature = extract_features(full_path)
            except Exception as e:
                print("⚠ 特征提取失败:", full_path, "错误:", e)
                continue

            new_label = reverse_map[old_label]

            dataset.append({
                "feature": feature,
                "label": new_label
            })

            print("✔ 完成:", file)

    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    print("\n🎉 数据构建完成！共样本数:", len(dataset))


if __name__ == "__main__":
    build()
