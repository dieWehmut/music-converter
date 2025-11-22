<<<<<<< HEAD
# ============================
# MelodyTransformer vFinal (safe version)
# ============================

from pathlib import Path
import numpy as np
import librosa
import soundfile as sf

from backend.utils.safe_librosa import safe_pitch_shift, safe_time_stretch

class MelodyTransformer:
    def __init__(self, target_sr: int = 32000):
        self.target_sr = target_sr

    def transform(self, melody_path: str, attempt: int, prev_score=None) -> str:

        # attempt 1 不做变形
        if attempt <= 1:
            print("[MelodyTransformer] attempt 1, keep original melody.")
            return melody_path

        y, sr = sf.read(melody_path)
        if y.ndim>1: y = y.mean(axis=1)
        if sr != self.target_sr:
            y = librosa.resample(y, sr, self.target_sr)
            sr = self.target_sr

        # ------ 安全范围（最终版） ------
        # time stretch：±3%
        rate = float(np.random.uniform(0.97, 1.03))
        # pitch shift：±1 semitone
        steps = float(np.random.uniform(-1.0, 1.0))

        # ------ transform ------
        if abs(rate - 1) > 0.01:
            y = safe_time_stretch(y, rate)

        if abs(steps) > 0.05:
            y = safe_pitch_shift(y, sr, steps)

        # normalize
        peak = np.max(np.abs(y))
        if peak > 1e-6:
            y = y / peak * 0.9

        out = Path(melody_path).with_name(Path(melody_path).stem + f"_t{attempt}.wav")
        sf.write(str(out), y, sr)
        print(f"[MelodyTransformer] Saved {out} (rate={rate:.3f}, steps={steps:.2f})")
        return str(out)
=======
# backend/inference/melody_transformer.py

from pathlib import Path
import numpy as np
import soundfile as sf
import librosa


class MelodyTransformer:
    """
    多 attempt 旋律轻度变形器：

    - attempt 1: 不做变形
    - attempt 2: 轻微 time stretch (0.97~1.03)
    - attempt 3: 再加 pitch shift (-0.5~+0.5 半音)
    - attempt >=4: time stretch + pitch shift (-1~+1 半音)

    支持新旧 librosa 版本，自动修复 time_stretch 参数问题。
    """

    def __init__(self, target_sr: int = 32000):
        self.target_sr = target_sr

    @staticmethod
    def _safe_time_stretch(y, rate):
        """兼容 librosa 0.10+ 和旧版本的 time_stretch 调用方式。"""
        try:
            # 新版 librosa 需要关键字参数
            return librosa.effects.time_stretch(y=y, rate=rate)
        except TypeError:
            # 旧版 librosa 是位置参数
            return librosa.effects.time_stretch(y, rate)

    @staticmethod
    def _safe_pitch_shift(y, sr, steps):
        """兼容 librosa pitch_shift（API 变化不大，但以防未来改版）"""
        try:
            return librosa.effects.pitch_shift(y=y, sr=sr, n_steps=steps)
        except TypeError:
            return librosa.effects.pitch_shift(y, sr, steps)

    def transform(self, melody_path: str, attempt: int) -> str:
        melody_path = str(melody_path)
        if attempt <= 1:
            return melody_path

        y, sr = sf.read(melody_path)
        if y.ndim > 1:
            y = y.mean(axis=1)

        if sr != self.target_sr:
            y = librosa.resample(y, orig_sr=sr, target_sr=self.target_sr)
            sr = self.target_sr

        # ----- 根据 attempt 决定变形强度 -----
        if attempt == 2:
            rate = float(np.random.uniform(0.97, 1.03))
            steps = 0.0
        elif attempt == 3:
            rate = float(np.random.uniform(0.95, 1.05))
            steps = float(np.random.uniform(-0.5, 0.5))
        else:
            rate = float(np.random.uniform(0.92, 1.08))
            steps = float(np.random.uniform(-1.0, 1.0))

        # ----- Time Stretch -----
        if abs(rate - 1.0) > 0.01:
            y = self._safe_time_stretch(y, rate)

        # ----- Pitch Shift -----
        if abs(steps) > 0.05:
            y = self._safe_pitch_shift(y, sr, steps)

        # ----- Normalize -----
        max_abs = float(np.max(np.abs(y)))
        if max_abs > 1e-6:
            y = y / max_abs * 0.9

        # ----- Save -----
        out_path = Path(melody_path).with_name(
            Path(melody_path).stem + f"_t{attempt}.wav"
        )
        sf.write(str(out_path), y, sr)

        print(
            f"[MelodyTransformer] Transformed melody for attempt {attempt} → {out_path} "
            f"(rate={rate:.3f}, steps={steps:.2f})"
        )

        return str(out_path)
>>>>>>> 0cf27b1 (failed_v4)
