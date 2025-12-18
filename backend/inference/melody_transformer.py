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
