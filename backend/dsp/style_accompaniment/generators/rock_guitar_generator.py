# backend/dsp/style_accompaniment/generators/rock_guitar_generator.py

from pathlib import Path
import random
from pydub import AudioSegment


class RockGuitarGenerator:
    """
    使用 samples/rock 下的：
        guitar_riff_*.wav 作为主 riff
        guitar_fill_*.wav 作为 fill

    根据 guitar_params:
        riff_density: 小节里放 riff 的概率
        fill_prob:    每 4 小节末尾加 fill 的概率
        variation_prob: 更换 riff 的频率
        palm_mute:    模拟闷音
        distortion:   失真强度(用音量/压缩简单模拟)

    length_s: 最终长度(秒)，推荐 30~60
    """

    def __init__(self):
        style_root = Path(__file__).resolve().parents[1] / "samples" / "rock"
        self.root = style_root

        riff_files = sorted(style_root.glob("guitar_riff_*.wav"))
        fill_files = sorted(style_root.glob("guitar_fill_*.wav"))

        if not riff_files:
            raise RuntimeError(f"在 {style_root} 下未找到 guitar_riff_*.wav")

        self.riffs = [AudioSegment.from_file(p) for p in riff_files]
        self.fills = [AudioSegment.from_file(p) for p in fill_files] if fill_files else []

        # 默认小节长度 = 第一个 riff 长度
        self.bar_ms = len(self.riffs[0])

    def _apply_tone(self, seg: AudioSegment, palm_mute: bool, distortion: float) -> AudioSegment:
        # palm mute: 减高频 + 降音量
        if palm_mute:
            seg = seg.low_pass_filter(4000)
            seg = seg - 3

        # 简单失真模拟：增加音量（后面由 mixer 做真正限制）
        seg = seg + int(distortion * 4)  # +0~+4 dB
        return seg

    def generate(self, guitar_params: dict, length_s: float = 30.0) -> str:
        riff_density = float(guitar_params.get("riff_density", 0.7))
        fill_prob = float(guitar_params.get("fill_prob", 0.3))
        var_prob = float(guitar_params.get("variation_prob", 0.5))
        palm_mute = bool(guitar_params.get("palm_mute", False))
        distortion = float(guitar_params.get("distortion", 0.5))

        total_ms = int(length_s * 1000)

        segments: list[AudioSegment] = []
        current_riff = random.choice(self.riffs)

        t = 0
        bar_index = 0

        while t < total_ms:
            use_fill = False
            # 每 4 小节末尾，有概率用 fill
            if (bar_index + 1) % 4 == 0 and self.fills:
                if random.random() < fill_prob:
                    use_fill = True

            if use_fill:
                seg = random.choice(self.fills)
            else:
                # 决定是否本小节放 riff
                if random.random() <= riff_density:
                    # 是否换 riff
                    if random.random() < var_prob:
                        current_riff = random.choice(self.riffs)
                    seg = current_riff
                else:
                    # 留白：空小节
                    seg = AudioSegment.silent(duration=self.bar_ms)

            seg = self._apply_tone(seg, palm_mute, distortion)
            segments.append(seg)

            t += self.bar_ms
            bar_index += 1

        track = sum(segments, AudioSegment.silent(duration=0))
        track = track[:total_ms]

        out_path = self.root / "rock_guitar.wav"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        track.export(out_path, format="wav")
        return str(out_path)
