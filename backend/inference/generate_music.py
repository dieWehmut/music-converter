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
import numpy as np
import soundfile as sf
import torch
from transformers import AutoProcessor, MusicgenForConditionalGeneration


class MusicGenerator:
    """
    MusicGen-medium 生成器（方案 A 用，带 anti-collapse 防掉音）

    - 半精度 (float16) 加速
    - 使用 melody 条件
    - 根据 target_seconds 自动换算 max_new_tokens
    - guidance_scale 由外部随 attempt 调整（3.8 → 3.6 → 3.4 → 3.2）
    - 生成后做尾部 energy 检测与 crossfade 修补，防止结尾静音/掉音
    """

    def __init__(
        self,
        model_name: str = "facebook/musicgen-medium",
        device: str | None = None,
    ):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        print(f"[MusicGen] Loading {model_name} on {self.device} ...")

        self.processor = AutoProcessor.from_pretrained(model_name)
        self.model = MusicgenForConditionalGeneration.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
        ).to(self.device)

        if self.device == "cuda":
            self.model = self.model.half()

        self.model.eval()
        print("[MusicGen] Model loaded.")

        # 根据你之前 11.44s / 375 token 推算得到的经验：
        # seconds_per_token ≈ 0.0305
        self.seconds_per_token = 0.0305

    def _load_melody(self, melody_path: str):
        y, sr = sf.read(melody_path)
        if y.ndim > 1:
            y = y.mean(axis=1)
        if sr != 32000:
            y = librosa.resample(y, orig_sr=sr, target_sr=32000)
            sr = 32000
        return y.astype(np.float32), sr

    @staticmethod
    def _anti_collapse(audio: np.ndarray, sr: int, tail_sec: float = 2.0) -> np.ndarray:
        """
        简单 anti-collapse：
        - 若最后 tail_sec 的 RMS 明显小于整体 RMS，则用前一段 crossfade 修补。
        """
        if audio.size == 0:
            return audio

        total_rms = float(np.sqrt(np.mean(audio**2)))
        if total_rms < 1e-6:
            return audio

        n_tail = int(tail_sec * sr)
        if audio.shape[0] < 3 * n_tail:
            # 太短就不修
            return audio

        tail = audio[-n_tail:]
        prev = audio[-2 * n_tail : -n_tail]
        tail_rms = float(np.sqrt(np.mean(tail**2)))

        # 小于整体的 35% 认为崩坏
        if tail_rms >= 0.35 * total_rms:
            return audio

        print(
            f"[MusicGen] Detected tail collapse (tail_rms={tail_rms:.4f}, "
            f"total_rms={total_rms:.4f}), applying crossfade fix..."
        )

        new_tail = 0.7 * prev[-n_tail:] + 0.3 * tail
        max_abs = float(np.max(np.abs(new_tail)))
        if max_abs > 1.0:
            new_tail = new_tail / max_abs

        out = audio.copy()
        out[-n_tail:] = new_tail
        return out

    def generate_with_melody(
        self,
        prompt: str,
        melody_path: str,
        output_path: str,
        target_seconds: float = 15.0,
        guidance_scale: float = 3.5,
        temperature: float = 1.0,
        top_p: float = 0.95,
        do_sample: bool = True,
        max_new_tokens: int | None = None,
    ) -> str:
        melody_path = str(melody_path)
        output_path = str(output_path)

        print(f"[MusicGen] Loading melody from {melody_path} ...")
        melody, sr = self._load_melody(melody_path)

        if max_new_tokens is None:
            approx_tokens = target_seconds / self.seconds_per_token
            max_new_tokens = int(approx_tokens + 0.5)
            print(
                f"[MusicGen] Target seconds: {target_seconds} → "
                f"max_new_tokens={max_new_tokens} "
                f"(≈{self.seconds_per_token:.4f}s/token)"
            )
        else:
            print(f"[MusicGen] Using external max_new_tokens={max_new_tokens}")

        inputs = self.processor(
            text=[prompt],
            audio=[melody],
            sampling_rate=sr,
            return_tensors="pt",
        ).to(self.device)

        print(f"[MusicGen] Generating audio (guidance_scale={guidance_scale})...")
        start_t = time.time()

        with torch.no_grad():
            audio_values = self.model.generate(
                **inputs,
                do_sample=do_sample,
                temperature=temperature,
                top_p=top_p,
                guidance_scale=guidance_scale,
                max_new_tokens=max_new_tokens,
            )

        gen_t = time.time() - start_t
        print(f"[MusicGen] Generation done in {gen_t:.1f}s")

        audio_np = audio_values[0].cpu().numpy().reshape(-1)

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
