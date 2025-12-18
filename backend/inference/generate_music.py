# ============================
# MusicGenerator vFinal (anti-mid-collapse)
# ============================

import time
from pathlib import Path
import numpy as np
import librosa
import soundfile as sf
import torch
from transformers import AutoProcessor, MusicgenForConditionalGeneration

class MusicGenerator:
    def __init__(self, model_name="facebook/musicgen-small", device=None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.processor = AutoProcessor.from_pretrained(model_name)
        self.model = MusicgenForConditionalGeneration.from_pretrained(
            model_name,
            dtype=torch.float16 if self.device=="cuda" else torch.float32
        ).to(self.device)
        if self.device=="cuda":
            self.model = self.model.half()

        self.seconds_per_token = 0.0305

    def _load_melody(self, path):
        y, sr = sf.read(path)
        if y.ndim>1: y = y.mean(axis=1)
        if sr != 32000:
            y = librosa.resample(y, sr, 32000)
        return y.astype(np.float32), 32000

    @staticmethod
    def _mid_collapse_fix(audio, sr):
        """
        检测中段是否大幅下降 → 用前一段 crossfade
        """
        if len(audio) < sr * 6:
            return audio

        N = len(audio)
        a = audio[N//3 : N//2]
        b = audio[N//2 : 2*N//3]

        rms_a = np.sqrt(np.mean(a**2))
        rms_b = np.sqrt(np.mean(b**2))

        if rms_a > 1e-5 and rms_b < rms_a * 0.33:
            print("[MusicGen] Mid collapse detected → fixing...")
            fixed = 0.7 * a[:len(b)] + 0.3 * b
            audio[N//2 : N//2+len(fixed)] = fixed

        return audio

    @staticmethod
    def _tail_fix(audio, sr):
        tail = audio[-sr*2:]
        prev = audio[-sr*4:-sr*2]
        if np.sqrt(np.mean(tail**2)) < np.sqrt(np.mean(prev**2)) * 0.3:
            print("[MusicGen] Tail collapse → fixing...")
            audio[-sr*2:] = 0.7 * prev + 0.3 * tail
        return audio

    def generate_with_melody(
            self, prompt, melody_path, output_path,
            target_seconds=20.0,
            guidance_scale=3.0,
            temperature=1.0,
            top_p=0.95,
            do_sample=True,
            max_new_tokens=None,
        ):
            mel, sr = self._load_melody(melody_path)

            # 计算 token 数量
            if max_new_tokens is None:
                max_new_tokens = int(target_seconds / self.seconds_per_token)

            inputs = self.processor(
                text=[prompt],
                audio=[mel],
                sampling_rate=sr,
                return_tensors="pt"
            ).to(self.device)

            if self.device == "cuda" and "input_values" in inputs:
                inputs["input_values"] = inputs["input_values"].to(torch.float16)

            with torch.no_grad():
                audio = self.model.generate(
                    **inputs,
                    do_sample=do_sample,
                    temperature=temperature,
                    top_p=top_p,
                    guidance_scale=guidance_scale,
                    max_new_tokens=max_new_tokens,
                )

            # 转为 numpy float32
            audio = audio[0].cpu().numpy().reshape(-1).astype(np.float32)

            # 中段修复 & 尾部修复（保持你原有的逻辑）
            audio = self._mid_collapse_fix(audio, 32000)
            audio = self._tail_fix(audio, 32000)
            # 32000 是 MusicGen 的固定采样率
            expected_samples = int(target_seconds * 32000)
            
            if len(audio) > expected_samples:
                print(f"[MusicGen] Trimming audio from {len(audio)/32000:.2f}s to {target_seconds:.2f}s")
                # 1. 直接截断
                audio = audio[:expected_samples]
                
                # 2. 为了防止截断处出现爆音(Click)，给最后 0.1秒 做个淡出
                fade_len = int(0.1 * 32000) 
                if len(audio) > fade_len:
                    # 线性淡出：从 1.0 变到 0.0
                    fade_curve = np.linspace(1.0, 0.0, fade_len)
                    audio[-fade_len:] = audio[-fade_len:] * fade_curve
            # ==========================================

            # normalize (防止爆音)
            if np.max(np.abs(audio)) > 1e-6:
                audio = audio / np.max(np.abs(audio)) * 0.98

            sf.write(output_path, audio, 32000)
            print(f"[MusicGen] Saved: {output_path}")
            return output_path
