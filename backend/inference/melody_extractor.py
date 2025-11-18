import numpy as np
import librosa
import soundfile as sf
from pathlib import Path
import crepe


class MelodyExtractor:
    """
    使用 CREPE 提取 F0，并以正弦波重建旋律音轨，用于 MusicGen Melody 条件。
    """

    def __init__(self, target_sr=16000):
        # 最推荐 16kHz 输出
        self.target_sr = target_sr

    # -------------------------
    # Step 1: CREPE 提取 F0
    # -------------------------
    def extract_f0(self, audio_path):
        # CREPE 最佳采样率：16k
        y, sr = librosa.load(audio_path, sr=16000, mono=True)

        # CREPE f0，每帧 hop=160（10ms）
        time, frequency, confidence, activation = crepe.predict(
            y, sr, viterbi=True
        )

        f0 = frequency
        conf = confidence

        # 低置信度 f0 去掉
        f0[conf < 0.4] = 0

        return f0

    # -------------------------
    # Step 2: 插值 & 平滑 f0
    # -------------------------
    def smooth_f0(self, f0):
        f0 = np.where(f0 == 0, np.nan, f0)
        idx = np.arange(len(f0))
        valid = np.where(~np.isnan(f0))[0]

        if len(valid) < 2:
            return np.zeros_like(f0)

        # 插值
        f_interp = np.interp(idx, valid, f0[valid])

        # 平滑（librosa harmonic）
        f_smooth = librosa.effects.harmonic(f_interp)

        return f_smooth

    # -------------------------
    # Step 3: 正弦合成旋律
    # -------------------------
    def synthesize_melody(self, f0):
        hop_length = 160  # CREPE 固定
        base_sr = 16000   # CREPE 基准采样率

        # 正确的 duration 计算（重点修复）
        duration = len(f0) * hop_length / base_sr
        t = np.linspace(0, duration, int(duration * self.target_sr))

        melody = np.zeros_like(t)

        # 每帧对应多少 samples（重新采样到 target_sr）
        samples_per_frame = int((hop_length / base_sr) * self.target_sr)
        pos = 0

        for freq in f0:
            if freq > 0:
                frame = 0.5 * np.sin(
                    2 * np.pi * freq * np.linspace(0, samples_per_frame / self.target_sr, samples_per_frame)
                )
            else:
                frame = np.zeros(samples_per_frame)

            end = pos + samples_per_frame
            if end <= len(melody):
                melody[pos:end] = frame

            pos = end

        return melody

    # -------------------------
    # Step 4: 完整流程
    # -------------------------
    def extract_melody_to_wav(self, audio_path, output_path=None):
        f0 = self.extract_f0(audio_path)
        f0 = self.smooth_f0(f0)
        melody = self.synthesize_melody(f0)

        if output_path is None:
            parent = Path(audio_path).parent
            output_path = parent / "melody.wav"

        sf.write(output_path, melody, self.target_sr)
        return str(output_path)


# Debug
if __name__ == "__main__":
    test_audio = r"D:\idea_python\music_project\backend\test_audio.wav"
    extractor = MelodyExtractor()
    out = extractor.extract_melody_to_wav(test_audio)
    print("旋律文件生成：", out)
