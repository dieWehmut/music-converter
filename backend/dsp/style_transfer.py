# backend/dsp/style_transfer.py

from pathlib import Path
from pydub import AudioSegment

from .dsp_effects import DSPEffects
from backend.inference.analyze import analyzer


class StyleTransfer:
    """
    风格转换（已加 gain-staging，避免爆音）
    """

    def load_accompaniment(self, path: str) -> AudioSegment:
        return AudioSegment.from_file(Path(path))

    def apply_style_preset(self, acc: AudioSegment, target_style: str):
        dsp = DSPEffects
        s = target_style.lower()

        if s == "rock":
            acc = dsp.bass_boost(acc, gain_db=4.0, cutoff=180)
            acc = dsp.saturation(acc, amount=0.25)
            acc = dsp.change_volume(acc, 0.5)

        elif s == "jazz":
            acc = dsp.lowpass(acc, cutoff=5000)
            acc = dsp.reverb(acc, decay=0.4)
            acc = dsp.change_volume(acc, -1.0)

        elif s == "pop":
            acc = dsp.bass_boost(acc, gain_db=3.0, cutoff=200)
            acc = dsp.safe_normalize(acc)

        elif s == "lofi":
            acc = dsp.lowpass(acc, cutoff=3500)
            acc = dsp.saturation(acc, amount=0.2)
            acc = dsp.change_volume(acc, -2)

        elif s == "classical":
            acc = dsp.lowpass(acc, cutoff=4500)
            acc = dsp.change_volume(acc, -3)

        else:
            acc = dsp.safe_normalize(acc)

        return dsp.safe_normalize(acc)

    def apply(self, accompaniment_path: str, target_style: str):
        acc = self.load_accompaniment(accompaniment_path)
        return self.apply_style_preset(acc, target_style)


style_transfer = StyleTransfer()
