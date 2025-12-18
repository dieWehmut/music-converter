# backend/dsp/style_accompaniment/generators/rock_drum_generator.py

from pathlib import Path
import random
from pydub import AudioSegment


class RockDrumGenerator:
    """
    使用:
        drum_loop_*.wav 作为主节奏 loop
        drum_fill_*.wav 作为 fill

    参数:
        loop_energy: 0.3~1.2   -> 控制整体音量/力度
        fill_rate:   0~1       -> 每 4 小节中有多少小节末尾加 fill
        double_kick: bool      -> 暴躁感（用额外 overlay 模拟）
    """

    def __init__(self):
        style_root = Path(__file__).resolve().parents[1] / "samples" / "rock"
        self.root = style_root

        loop_files = sorted(style_root.glob("drum_loop_*.wav"))
        fill_files = sorted(style_root.glob("drum_fill_*.wav"))

        if not loop_files:
            raise RuntimeError(f"在 {style_root} 下未找到 drum_loop_*.wav")

        self.loops = [AudioSegment.from_file(p) for p in loop_files]
        self.fills = [AudioSegment.from_file(p) for p in fill_files] if fill_files else []

        self.bar_ms = len(self.loops[0])

    def generate(self, tempo: float, drum_params: dict, length_s: float = 30.0) -> str:
        loop_energy = float(drum_params.get("loop_energy", 0.8))
        fill_rate = float(drum_params.get("fill_rate", 0.25))
        double_kick = bool(drum_params.get("double_kick", False))

        total_ms = int(length_s * 1000)
        segments: list[AudioSegment] = []

        t = 0
        bar_index = 0

        while t < total_ms:
            loop = random.choice(self.loops)

            # 能量 -> 整体增益
            gain_db = (loop_energy - 0.8) * 6.0  # 大致 -3~+2.4 dB
            loop = loop + int(gain_db)

            # 每 4 小节末尾，按概率插入 fill
            if self.fills and (bar_index + 1) % 4 == 0 and random.random() < fill_rate:
                fill = random.choice(self.fills)
                # 把 fill 覆盖到当前小节的后半部分
                if len(fill) < len(loop):
                    start = len(loop) - len(fill)
                    loop = loop.overlay(fill, position=start)
                else:
                    loop = fill

            # 简单 double kick 模拟（整小节多叠一次）
            if double_kick:
                loop = loop.overlay(loop - 4)

            segments.append(loop)
            t += self.bar_ms
            bar_index += 1

        track = sum(segments, AudioSegment.silent(duration=0))
        track = track[:total_ms]

        out_path = self.root / "rock_drums.wav"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        track.export(out_path, format="wav")
        return str(out_path)
