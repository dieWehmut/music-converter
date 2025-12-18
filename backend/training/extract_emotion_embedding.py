import os
import sys
import json
from tqdm import tqdm

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(ROOT)

from backend.features.yamnet_extract import extract_yamnet_embedding

AUG_DIR = "backend/dataset/emomusic_aug"
OUT_JSON = "backend/dataset/emomusic_embedding/emotion_dataset.json"


def extract_all_embeddings():
    print("🎧 读取增强后的数据集...")

    result = []
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)

    for folder in os.listdir(AUG_DIR):
        folder_path = os.path.join(AUG_DIR, folder)
        if not os.path.isdir(folder_path):
            continue

        # 提取情绪标签（第二个词）
        parts = folder.split()
        if len(parts) < 2:
            print(f"⚠ 无法解析情绪标签：{folder}")
            continue

        emotion = parts[1].lower()  # angry / happy / dark / funny

        print(f"\n📂 类别：{folder} -> 情绪：{emotion}")

        for filename in tqdm(os.listdir(folder_path)):
            if not filename.endswith(".wav"):
                continue

            file_path = os.path.join(folder_path, filename)

            try:
                emb = extract_yamnet_embedding(file_path)
            except Exception as e:
                print(f"❌ 提取失败：{file_path} -> {e}")
                continue

            result.append({
                "embedding": emb.tolist(),
                "label": emotion,
                "file": filename
            })

    print("\n💾 正在保存 JSON 数据 ...")
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n🎉 完成！所有 embedding 已保存：{OUT_JSON}")
    print(f"共计 {len(result)} 条数据")


if __name__ == "__main__":
    extract_all_embeddings()
