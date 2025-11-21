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

import numpy as np
import librosa


class MelodyTransformer:
    """
    MelodyTransformer (A1 模式)
    - 大幅修改旋律的音高和节奏，但保留大致轮廓。
    - 不再只是轻微变化，而是“几乎认不出”，仍有一点影子。
    """

    def __init__(self, target_sr=32000):
        self.target_sr = target_sr

    def _get_pitch_shift(self, style: str, emotion: str, strength: float) -> float:
        """
        根据目标风格 + 情绪，决定整体升降调的范围。
        返回值单位：半音（semitones）
        """
        style = style.lower()
        emotion = emotion.lower()

        base_shift = 0.0

        # 情绪对音高的“大方向”影响
        if emotion == "happy":
            base_shift += 4.0   # 明亮很多
        elif emotion == "funny":
            base_shift += 5.0
        elif emotion == "angry":
            base_shift += 3.0
        elif emotion == "sad":
            base_shift -= 4.0
        elif emotion == "scary":
            base_shift -= 3.0
        elif emotion == "tender":
            base_shift -= 2.0

        # 风格对音高的微调
        if style in ["jazz", "pop"]:
            base_shift += 1.0
        elif style in ["electronic"]:
            base_shift += 2.0
        elif style in ["classical"]:
            base_shift += 0.0
        elif style in ["rock"]:
            base_shift += 1.0

        # 限制到 [-7, 7] 半音左右
        base_shift = max(min(base_shift, 7.0), -7.0)

        # 按强度缩放
        shift = base_shift * strength
        return shift

    def _get_time_stretch(self, style: str, emotion: str, strength: float) -> float:
        """
        返回 time stretch 比例：
        >1 变快，<1 变慢
        """
        style = style.lower()
        emotion = emotion.lower()

        base_rate = 1.0

        # 情绪改变节奏感
        if emotion in ["happy", "funny", "angry"]:
            base_rate = 1.25   # 明显快不少
        elif emotion in ["sad", "tender"]:
            base_rate = 0.80   # 明显慢
        elif emotion == "scary":
            base_rate = 0.90

        # 风格微调
        if style == "lofi":
            base_rate *= 0.9
        elif style == "electronic":
            base_rate *= 1.1

        # 按强度缩放偏移
        rate = 1.0 + (base_rate - 1.0) * strength
        return rate

    def transform(self, y, sr, style: str, emotion: str, strength: float = 0.9):
        """
        对旋律做大幅变形。
        y: mono waveform
        sr: 采样率
        strength: 0~1, 越大变化越猛烈（A1 推荐 0.8~0.95）
        """
        # 归一化，避免数值爆炸
        if np.max(np.abs(y)) > 1e-6:
            y = y / np.max(np.abs(y)) * 0.9

        # 限制输入长度，避免时间拉伸时太慢
        MAX_INPUT_SECONDS = 12
        max_len = int(sr * MAX_INPUT_SECONDS)
        if len(y) > max_len:
            y = y[:max_len]

        # -------- 1. 全局 Pitch Shift --------
        pitch_shift_steps = self._get_pitch_shift(style, emotion, strength)
        if abs(pitch_shift_steps) > 0.1:
            try:
                y = librosa.effects.pitch_shift(y, sr=sr, n_steps=pitch_shift_steps)
            except Exception as e:
                print("[MelodyTransformer] pitch_shift failed:", e)

        # -------- 2. Time Stretch（节奏大改） --------
        rate = self._get_time_stretch(style, emotion, strength)
        if abs(rate - 1.0) > 0.05:
            try:
                y = librosa.effects.time_stretch(y, rate=rate)
            except Exception as e:
                print("[MelodyTransformer] time_stretch failed:", e)

        # -------- 3. 轻微随机抖动（幅度变化 + 很轻微噪声）--------
        # 增加一点随机感，但不做逐帧 pitch jitter（太重）
        if np.max(np.abs(y)) > 1e-6:
            y = y / np.max(np.abs(y)) * 0.8

        # 增加非常轻微的随机包络
        rng = np.random.default_rng()
        env = rng.normal(loc=1.0, scale=0.03, size=len(y))
        env = np.clip(env, 0.85, 1.15)
        y = y * env

        # 轻噪音，防止太“干净”
        y += rng.normal(scale=0.0015, size=len(y))

        # 最后再归一化
        if np.max(np.abs(y)) > 1e-6:
            y = y / np.max(np.abs(y)) * 0.7

        return y, sr
>>>>>>> cb02a3d (portionwise_failed_model_v3)
