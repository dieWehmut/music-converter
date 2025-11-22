# backend/dsp/emotion_transfer.py

from pathlib import Path
from pydub import AudioSegment
from .dsp_effects import DSPEffects


class EmotionTransfer:
    """
    情绪 DSP（全部降低 gain，对应安全版本）
    """

    def load_accompaniment(self, path: str):
        return AudioSegment.from_file(Path(path))

    def apply_emotion_effects(self, audio, emotion_prob):
        dsp = DSPEffects

        angry = emotion_prob.get("angry", 0)
        funny = emotion_prob.get("funny", 0)
        happy = emotion_prob.get("happy", 0)
        sad = emotion_prob.get("sad", 0)
        scary = emotion_prob.get("scary", 0)
        tender = emotion_prob.get("tender", 0)

        # Angry：轻微失真 + 一点低频
        if angry > 0.15:
            audio = dsp.saturation(audio, amount=0.15)
            audio = dsp.bass_boost(audio, gain_db=2 + angry * 2)

        # Funny：轻微亮化
        if funny > 0.15:
            audio = dsp.highpass(audio, cutoff=500 + funny * 500)

        # Happy：更亮一点
        if happy > 0.15:
            audio = dsp.highpass(audio, cutoff=4500)

        # Sad：轻混响 + 高频柔化
        if sad > 0.15:
            audio = dsp.lowpass(audio, cutoff=int(5000 - sad * 3000))
            audio = dsp.reverb(audio, decay=0.3 + sad * 0.3)

        # Scary：暗色调
        if scary > 0.15:
            audio = dsp.lowpass(audio, cutoff=3500)
            audio = dsp.reverb(audio, decay=0.6)

        # Tender
        if tender > 0.15:
            audio = dsp.lowpass(audio, cutoff=4500)
            audio = dsp.reverb(audio, decay=0.3)

        return dsp.safe_normalize(audio)

    def apply(self, accompaniment_path, emotion_prob):
        acc = self.load_accompaniment(accompaniment_path)
        return self.apply_emotion_effects(acc, emotion_prob)


emotion_transfer = EmotionTransfer()
