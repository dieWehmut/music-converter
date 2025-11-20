import soundfile as sf
import torch
import librosa
from transformers import AutoProcessor, MusicgenForConditionalGeneration
import time


class MusicGenerator:
    def __init__(self, model_name="facebook/musicgen-medium", device=None):
        """
        推荐使用 musicgen-medium:
        - 更长上下文
        - 更少 position overflow 错误
        - 更好的生成质量
        """
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        print(f"[MusicGen] Loading model on {self.device} ...")

        self.processor = AutoProcessor.from_pretrained(model_name)
        self.model = MusicgenForConditionalGeneration.from_pretrained(model_name).to(self.device)

        print("[MusicGen] Model loaded successfully.")

    def generate_with_melody(self, prompt, melody_path, output_path="generated.wav", max_new_tokens=768):
        print(f"[MusicGen] Loading melody: {melody_path}")

        melody, sr = sf.read(melody_path)

        # ensure mono
        if melody.ndim > 1:
            melody = melody.mean(axis=1)

        # ensure 32000 Hz
        if sr != 32000:
            print(f"[MusicGen] Resampling melody from {sr} to 32000 Hz...")
            melody = librosa.resample(melody, orig_sr=sr, target_sr=32000)
            sr = 32000

        # Convert to tensor
        melody = torch.tensor(melody).float().to(self.device)

        # ---------------------------------------------------
        # 🔥 Prevent MusicGen position embedding overflow
        # ---------------------------------------------------
        MAX_MELODY_SECONDS = 12
        max_len = 32000 * MAX_MELODY_SECONDS

        if melody.shape[0] > max_len:
            print(f"[MusicGen] Trimming melody from {melody.shape[0]} to {max_len} samples")
            melody = melody[:max_len]

        print("[MusicGen] Preparing input...")
        inputs = self.processor(
            text=[prompt],
            audio=melody,
            sampling_rate=sr,
            return_tensors="pt",
            padding=True
        ).to(self.device)

        print("[MusicGen] Generating new audio...")

        # Hardcore: random seed per generation
        torch.manual_seed(int(time.time()))

        audio_values = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens
        )

        audio_np = audio_values[0].cpu().numpy()

        # flatten
        audio_np = audio_np.reshape(-1)

        sf.write(output_path, audio_np, self.model.config.audio_encoder.sampling_rate)
        print(f"[MusicGen] Saved generated audio to {output_path}")

        return output_path
