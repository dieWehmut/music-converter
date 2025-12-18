# backend/dataset/download_emomusic.py
# 下载 MUSGEN-EmoMusic 数据集到 backend/dataset/emomusic_raw/

import os
from huggingface_hub import snapshot_download

SAVE_DIR = "backend/dataset/emomusic_raw"


def download_emomusic():
    print("🚀 正在下载 MUSGEN-EmoMusic 数据集（原始 wav 文件）...")

    snapshot_download(
        repo_id="jfforero/MUSGEN-EmoMusic",
        repo_type="dataset",
        local_dir=SAVE_DIR,
        local_dir_use_symlinks=False,  # Windows 必须禁用
        revision="main",
    )

    print("🎉 下载完成！数据已保存到：", SAVE_DIR)


if __name__ == "__main__":
    download_emomusic()
