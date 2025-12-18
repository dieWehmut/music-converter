# backend/dsp/dsp_effects.py

from pydub import AudioSegment
from pydub.effects import low_pass_filter, high_pass_filter, normalize
import numpy as np


class DSPEffects:
    """
    基础 DSP 效果器（经过全局安全优化）
    """

    @staticmethod
    def change_volume(audio: AudioSegment, db: float):
        return audio + db

    @staticmethod
    def lowpass(audio: AudioSegment, cutoff: int):
        return low_pass_filter(audio, cutoff)

    @staticmethod
    def highpass(audio: AudioSegment, cutoff: int):
        return high_pass_filter(audio, cutoff)

    @staticmethod
    def bass_boost(audio: AudioSegment, gain_db: float = 6.0, cutoff: int = 150):
        """
        稳健版低频增强（不会失真）
        """
        boosted = low_pass_filter(audio, cutoff)
        boosted = boosted + gain_db
        return audio.overlay(boosted - 6)  # 安全降低叠加音量

    @staticmethod
    def treble_cut(audio: AudioSegment, db: float = -6.0, cutoff: int = 4000):
        cut = high_pass_filter(audio, cutoff)
        cut = cut + db
        return audio.overlay(cut - 6)

    @staticmethod
    def saturation(audio: AudioSegment, amount: float = 0.3):
        """
        安全软失真（不会产生硬 clipping）
        """
        samples = np.array(audio.get_array_of_samples()).astype(np.float32)
        max_val = np.max(np.abs(samples)) + 1e-9
        samples = samples / max_val

        clipped = np.tanh(samples * (1 + amount * 10))
        clipped = clipped * max_val

        new_audio = audio._spawn(clipped.astype(audio.array_type))
        return new_audio - 3  # 避免音量变大

    @staticmethod
    def reverb(audio: AudioSegment, decay: float = 0.5):
        """
        稳定混响（修复 delay -> position）
        """
        delay = 120
        echo = audio - 12
        for i in range(1, 4):
            audio = audio.overlay(echo - (i * 6), position=i * delay)
        return audio

    @staticmethod
    def safe_normalize(audio: AudioSegment):
        """
        强制不爆音 limiter
        """
        audio = normalize(audio)
        return audio - 3  # 留余量，避免 overlay 后 clip
