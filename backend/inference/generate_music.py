<<<<<<< HEAD
<<<<<<< HEAD
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
=======
# backend/inference/generate_music.py

import time
from pathlib import Path

import librosa
=======
import torch
>>>>>>> 368ab93 (need_test_try)
import numpy as np
import soundfile as sf
from transformers import AutoProcessor, MusicgenForConditionalGeneration
from scipy.signal import butter, filtfilt


class MusicGenerator:
    def __init__(self, model_name="facebook/musicgen-small", device="cuda"):
        print("🔧 Loading MusicGen model...")
        self.device = device if torch.cuda.is_available() else "cpu"

        self.processor = AutoProcessor.from_pretrained(model_name)
        self.model = MusicgenForConditionalGeneration.from_pretrained(
            model_name,
            attn_implementation="eager"
        ).to(self.device)

    # -------------------------------
    # HIGH-PASS FILTER (STABLE)
    # -------------------------------
    def highpass(self, wav, sr=32000, cutoff=80):
        b, a = butter(4, cutoff / (sr / 2), btype="high")
        return filtfilt(b, a, wav)

    # -------------------------------
    # POST PROCESSING
    # -------------------------------
    def post_process(self, wav):
        wav = wav - np.mean(wav)
        wav = self.highpass(wav, cutoff=80)
        wav = wav / (np.max(np.abs(wav)) + 1e-9)
        return wav

    # -------------------------------
    # GENERATE ONCE
    # -------------------------------
    def generate_once(self, prompt, length_s):
        inputs = self.processor(
            text=[prompt],
            padding=True,
            return_tensors="pt"
        ).to(self.device)

        audio_values = self.model.generate(
            **inputs,
            max_new_tokens=length_s * 50,
            do_sample=True,
            temperature=1.0,
            guidance_scale=3.0
        )

        return audio_values[0, 0].cpu().numpy()

    # -------------------------------
    # MAIN GENERATION ENTRY
    # -------------------------------
    def generate(self, prompt, length_s):
        print("\n🎵 === Generating Music ===")
        print("Prompt:", prompt)

        wav = self.generate_once(prompt, length_s)

        # auto fallback if too short
        if len(wav) < (length_s * 32000 * 0.7):
            print("⚠ 输出过短，切换安全 prompt 重生成...")
            safe_prompt = (
                f"A coherent music track. Style: {prompt}. "
                f"Full length, stable rhythm."
            )
            wav = self.generate_once(safe_prompt, length_s)

        # pad to full length
        if len(wav) < length_s * 32000:
            shortage = length_s * 32000 - len(wav)
            wav = np.concatenate([wav, np.zeros(int(shortage))])

        wav = self.post_process(wav)
        return wav

<<<<<<< HEAD
        # anti-collapse 尾部修补
        audio_np = self._anti_collapse(audio_np, sr=32000, tail_sec=2.0)

        # 归一化防止 clipping
        peak = float(np.max(np.abs(audio_np)))
        if peak > 1e-6:
            audio_np = audio_np / peak * 0.98

        # 输出采样率
        out_sr = 32000
        cfg_enc = getattr(self.model.config, "audio_encoder", None)
        if cfg_enc is not None and hasattr(cfg_enc, "sampling_rate"):
            out_sr = cfg_enc.sampling_rate

        sf.write(output_path, audio_np, out_sr)
        print(f"[MusicGen] Saved generated audio to {output_path}")

        return output_path
>>>>>>> 0cf27b1 (failed_v4)
=======
    # -------------------------------
    # SAVE
    # -------------------------------
    def save(self, wav, path="output.wav"):
        sf.write(path, wav, 32000)
        print("💾 Saved:", path)
>>>>>>> 368ab93 (need_test_try)
