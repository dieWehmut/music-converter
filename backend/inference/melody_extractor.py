import librosa
import soundfile as sf
import numpy as np
from pathlib import Path

class MelodyExtractor:
    """
    Balanced 旋律提取版：
    - 保留旋律清晰可听
    - 轻微弱化，让风格转换更明显
    - 不会无声 / 不会过度破坏
    """

    def __init__(self, target_sr=32000):
        self.target_sr = target_sr

    def extract_melody_to_wav(self, audio_path, output_path=None):
        # 加载音频（32kHz）
        y, sr = librosa.load(audio_path, sr=self.target_sr, mono=True)

        # -------------------------------
        # Step 1 — 保留旋律但稍弱化
        # -------------------------------
        y = y * 0.2  # 音量保留 20%，弱化但仍可听

        # -------------------------------
        # Step 2 — 轻度低通滤波
        # -------------------------------
        y = librosa.effects.preemphasis(y, coef=-0.8)  # 柔化高频，不破坏旋律

        # -------------------------------
        # Step 3 — 加轻微噪声，保证差异明显
        # -------------------------------
        y += np.random.randn(len(y)) * 0.0015  # 轻噪，不会听不见

        # -------------------------------
        # Step 4 — 限制最长时间（防 MusicGen 崩溃）
        # -------------------------------
        MAX_SECONDS = 12
        max_len = self.target_sr * MAX_SECONDS
        if len(y) > max_len:
            y = y[:max_len]

        # -------------------------------
        # Step 5 — 保存
        # -------------------------------
        if output_path is None:
            parent = Path(audio_path).parent
            output_path = parent / "melody.wav"

        sf.write(output_path, y, self.target_sr)
        return str(output_path)
