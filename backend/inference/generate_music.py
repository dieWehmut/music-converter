import soundfile as sf
import torch
import librosa
from transformers import AutoProcessor, MusicgenForConditionalGeneration


class MusicGenerator:
    def __init__(self, model_name="facebook/musicgen-small", device=None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        print(f"[MusicGen] Loading model on {self.device} ...")

        self.processor = AutoProcessor.from_pretrained(model_name)
        self.model = MusicgenForConditionalGeneration.from_pretrained(model_name).to(self.device)

        print("[MusicGen] Model loaded successfully.")

    def generate_with_melody(self, prompt, melody_path, output_path="generated.wav", max_new_tokens=256):
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

        # MUST be 1D tensor
        melody = torch.tensor(melody).float().to(self.device)

        print("[MusicGen] Preparing input...")
        inputs = self.processor(
            text=[prompt],
            audio=melody,
            sampling_rate=sr,
            return_tensors="pt",
            padding=True
        ).to(self.device)

        print("[MusicGen] Generating new audio...")
        audio_values = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens
        )

        # Convert to numpy
        audio_np = audio_values[0].cpu().numpy()

        # --- 🔥 flatten to 1D ---
        audio_np = audio_np.reshape(-1)

        sf.write(output_path, audio_np, self.model.config.audio_encoder.sampling_rate)
        print(f"[MusicGen] Saved generated audio to {output_path}")

        return output_path
