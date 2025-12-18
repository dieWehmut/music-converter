import os
import soundfile as sf
import numpy as np
from scipy.signal import resample
from tqdm import tqdm


RAW_DIR = "backend/dataset/emomusic_raw"
AUG_DIR = "backend/dataset/emomusic_aug"


os.makedirs(AUG_DIR, exist_ok=True)


def speed_change(data, rate):
    """改变语速（改变采样缩放）"""
    idx = np.round(np.arange(0, len(data), rate))
    idx = idx[idx < len(data)].astype(int)
    return data[idx]


def add_noise(data, noise_factor=0.005):
    """加噪声"""
    noise = np.random.randn(len(data))
    return data + noise_factor * noise


def pitch_shift(data, shift=200):
    """简单移调: 加一些频率扰动（伪移调）"""
    return data + 0.002 * np.sin(np.linspace(0, 50, len(data)))


def process_one_audio(src_path, dst_path):
    try:
        data, sr = sf.read(src_path)
    except Exception as e:
        print(f"❌ 无法读取 {src_path}: {e}")
        return

    # ----------- 数据增强 ----------
    enhanced = []

    enhanced.append(data)                       # 原始
    enhanced.append(speed_change(data, 0.9))    # 变慢
    enhanced.append(speed_change(data, 1.1))    # 变快
    enhanced.append(add_noise(data))            # 加噪声
    enhanced.append(pitch_shift(data))          # 移调

    # ----------- 保存增强版本 ----------
    for idx, wav in enumerate(enhanced):
        out_file = dst_path.replace(".wav", f"_aug{idx}.wav")
        sf.write(out_file, wav, sr)


def augment_all():
    print("🎧 正在进行数据增强 ...")

    for cls in os.listdir(RAW_DIR):
        src_class = os.path.join(RAW_DIR, cls)
        if not os.path.isdir(src_class):
            continue

        dst_class = os.path.join(AUG_DIR, cls)
        os.makedirs(dst_class, exist_ok=True)

        print(f"\n📂 类别：{cls}")

        for filename in tqdm(os.listdir(src_class)):
            if not filename.endswith(".wav"):
                continue

            src_path = os.path.join(src_class, filename)
            dst_path = os.path.join(dst_class, filename)

            process_one_audio(src_path, dst_path)

    print("\n✅ 数据增强完成！")
    print(f"增强后数据保存在：{AUG_DIR}")


if __name__ == "__main__":
    augment_all()
