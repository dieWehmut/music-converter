# backend/dsp/style_accompaniment/generators/rock_bass_generator.py

from pathlib import Path
import random
from pydub import AudioSegment


class RockBassGenerator:
    """
    使用 samples/rock/bass_riff_*.wav 作为 bass 循环单元。

    参数:
        note_density: 0~1，0 表示几乎不弹，1 表示每小节都弹
        octave_prob:  出现“跳高一段”的概率（通过音量变化简单模拟）
    """

    def __init__(self):
        style_root = Path(__file__).resolve().parents[1] / "samples" / "rock"
        self.root = style_root

        riff_files = sorted(style_root.glob("bass_riff_*.wav"))
        if not riff_files:
            raise RuntimeError(f"在 {style_root} 下未找到 bass_riff_*.wav")

        self.riffs = [AudioSegment.from_file(p) for p in riff_files]
        self.unit_ms = len(self.riffs[0])

    def generate(self, tempo: float, bass_params: dict, length_s: float = 30.0) -> str:
        note_density = float(bass_params.get("note_density", 0.7))
        octave_prob = float(bass_params.get("octave_prob", 0.3))

        total_ms = int(length_s * 1000)
        segments: list[AudioSegment] = []

        t = 0
        bar_index = 0

        while t < total_ms:
            if random.random() <= note_density:
                riff = random.choice(self.riffs)
                # “跳八度”用+音量模拟一点强调感
                if random.random() < octave_prob and (bar_index % 4 == 3):
                    riff = riff + 3
            else:
                riff = AudioSegment.silent(duration=self.unit_ms)

            segments.append(riff)
            t += self.unit_ms
            bar_index += 1

        track = sum(segments, AudioSegment.silent(duration=0))
        track = track[:total_ms]

        out_path = self.root / "rock_bass.wav"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        track.export(out_path, format="wav")
        return str(out_path)
