# backend/dsp/remix_builder.py

from pathlib import Path
from pydub import AudioSegment

from .demucs_runner import DemucsRunner
from .style_transfer import style_transfer
from .emotion_transfer import emotion_transfer
from .dsp_effects import DSPEffects
from backend.inference.analyze import analyzer


class RemixBuilder:
    def __init__(self, stems_dir="backend/dsp/stems"):
        self.stems_dir = Path(stems_dir)
        self.demucs = DemucsRunner(output_dir=self.stems_dir)

    @staticmethod
    def _pad(audio, length):
        if len(audio) > length:
            return audio[:length]
        return audio + AudioSegment.silent(duration=length - len(audio))

    def build_accompaniment(self, stems: dict):
        drums = AudioSegment.from_file(stems["drums"]) - 6
        bass = AudioSegment.from_file(stems["bass"]) - 6
        other = AudioSegment.from_file(stems["other"]) - 6

        L = max(len(drums), len(bass), len(other))
        drums = self._pad(drums, L)
        bass = self._pad(bass, L)
        other = self._pad(other, L)

        acc = drums.overlay(bass).overlay(other)
        out = self.stems_dir / "accompaniment_mix.wav"
        acc.export(out, format="wav")
        return str(out)

    def build_remix(self, audio_path, target_style="rock", apply_emotion=True,
                    out_path="backend/dsp/output_remix.wav"):

        print("[Remix] Analyzer 分析...")
        analysis = analyzer.analyze(audio_path)
        emotion_prob = analysis.get("emotion_prob", {})

        print("[Remix] Demucs 拆轨...")
        stems = self.demucs.separate(audio_path)

        print("[Remix] 合成伴奏...")
        acc_path = self.build_accompaniment(stems)

        print("[Remix] 应用风格 DSP...")
        acc = style_transfer.apply(acc_path, target_style)

        print("[Remix] 应用情绪 DSP...")
        if apply_emotion:
            acc = emotion_transfer.apply_emotion_effects(acc, emotion_prob)

        vocals = AudioSegment.from_file(stems["vocals"])

        L = max(len(vocals), len(acc))
        vocals = self._pad(vocals, L)
        acc = self._pad(acc, L)

        final = acc.overlay(vocals)
        final = DSPEffects.safe_normalize(final)

        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        final.export(out_path, format="wav")

        print("[Remix] 完成输出：", out_path)
        return str(out_path)


if __name__ == "__main__":
    builder = RemixBuilder()
    builder.build_remix("backend/test_audio.wav", target_style="rock",
                        out_path="backend/dsp/output_remix_rock.wav")
