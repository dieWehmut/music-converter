# backend/dsp/style_accompaniment/mixer/smart_mixer.py

from pathlib import Path
from pydub import AudioSegment

from backend.dsp.dsp_effects import DSPEffects


class SmartMixer:
    """
    根据 mix_params（来自 RockParamsAI）对多轨进行简单智能混音。
    """

    def __init__(self, output_path="backend/dsp/style_accompaniment/rock_accompaniment.wav"):
        self.output_path = Path(output_path)

    def mix(self, stems: dict, mix_params: dict) -> str:
        """
        stems: {
            "drums": path,
            "bass": path,
            "guitar": path,
        }
        """
        drums = AudioSegment.from_file(stems["drums"])
        bass = AudioSegment.from_file(stems["bass"])
        guitar = AudioSegment.from_file(stems["guitar"])

        length = min(len(drums), len(bass), len(guitar))
        drums = drums[:length]
        bass = bass[:length]
        guitar = guitar[:length]

        # 初步音量平衡
        drums = drums - 1
        bass = bass - 3
        guitar = guitar - 2

        # 根据参数做 EQ / reverb / saturation
        eq_high = mix_params.get("eq_high", 0.0)
        eq_low = mix_params.get("eq_low", 0.0)
        reverb_amt = mix_params.get("reverb", 0.1)
        satur_amt = mix_params.get("saturation", 0.2)

        # 高频处理（只对吉他）
        if eq_high > 0:
            # 简单做一点高通 + 轻微提升
            guitar = DSPEffects.highpass(guitar, 3000)
            guitar = DSPEffects.change_volume(guitar, eq_high * 3)  # 最多 +1~2dB
        elif eq_high < 0:
            guitar = DSPEffects.treble_cut(guitar, db=eq_high * 3)

        # 低频处理（对 bass）
        if eq_low > 0:
            bass = DSPEffects.bass_boost(bass, gain_db=eq_low * 6)
        elif eq_low < 0:
            bass = DSPEffects.lowpass(bass, cutoff=150)

        # 轻微饱和（整个总线）
        if satur_amt > 0:
            drums = DSPEffects.saturation(drums, amount=satur_amt)

        # 简单混响（鼓 + 吉他）
        if reverb_amt > 0.05:
            drums = DSPEffects.reverb(drums, decay=reverb_amt)
            guitar = DSPEffects.reverb(guitar, decay=reverb_amt)

        # 叠加
        mix = drums.overlay(bass).overlay(guitar)

        # 安全归一化
        mix = DSPEffects.safe_normalize(mix)

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        mix.export(self.output_path, format="wav")
        return str(self.output_path)
