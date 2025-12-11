# ============================
# MelodyExtractor vFinal (5s version)
# ============================

from pathlib import Path
import numpy as np
import librosa
import soundfile as sf
from scipy.signal import butter, filtfilt

from backend.inference.melody_scorer import MelodyScorer

class MelodyExtractor:
    def __init__(
        self,
        target_sr: int = 32000,
        window_seconds: float = 5.0,     # ★★★ 从 3 秒 → 5 秒 ★★★
        hop_seconds: float = 0.5,
        min_score_threshold: float = 0.2,
    ):
        self.target_sr = target_sr
        self.window_seconds = window_seconds
        self.hop_seconds = hop_seconds
        self.min_score_threshold = min_score_threshold
        self.scorer = MelodyScorer()

    @staticmethod
    def _load_audio(path, sr=32000):
        y, s = librosa.load(path, sr=sr)
        return y, s

    # -------------------------------------------
    # Key detection（不变）
    # -------------------------------------------
    @staticmethod
    def _detect_key(y, sr):
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        chroma_mean = np.mean(chroma, axis=1)
        chroma_mean /= np.linalg.norm(chroma_mean) + 1e-9

        major_profile = np.array([6.35,2.23,3.48,2.33,4.38,4.09,2.52,5.19,2.39,3.66,2.29,2.88])
        minor_profile = np.array([6.33,2.68,3.52,5.38,2.60,3.53,2.54,4.75,3.98,2.69,3.34,3.17])
        major_profile /= np.linalg.norm(major_profile)
        minor_profile /= np.linalg.norm(minor_profile)

        best = -1
        tonic = 0
        mode = "major"
        for t in range(12):
            if np.dot(chroma_mean, np.roll(major_profile, t)) > best:
                best = np.dot(chroma_mean, np.roll(major_profile, t))
                tonic = t
                mode = "major"
            if np.dot(chroma_mean, np.roll(minor_profile, t)) > best:
                best = np.dot(chroma_mean, np.roll(minor_profile, t))
                tonic = t
                mode = "minor"

        names = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
        print(f"[Key] {names[tonic]} {mode}")
        return tonic, mode, f"{names[tonic]} {mode}"

    # -------------------------------------------
    # f0 提取（不变）
    # -------------------------------------------
    def _extract_f0(self, y, sr):
        try:
            f0, _, _ = librosa.pyin(
                y, fmin=65.4, fmax=1046.5,
                sr=sr, frame_length=2048, hop_length=512
            )
        except Exception:
            return None
        return f0

    # -------------------------------------------
    # 低破坏旋律（不变）
    # -------------------------------------------
    @staticmethod
    def _extract_low_destruction(clip, sr):
        harm, _ = librosa.effects.hpss(clip)
        b, a = butter(4, [200/(sr/2), 1200/(sr/2)], btype='band')
        filtered = filtfilt(b, a, harm)
        peak = np.max(np.abs(filtered))
        if peak > 1e-6:
            filtered = filtered / peak * 0.9
        return filtered.astype(np.float32)

    # -------------------------------------------
    # Window selection（不变）
    # -------------------------------------------
    def _find_best_window(self, y, sr):
        total = len(y)
        win = int(self.window_seconds * sr)
        hop = int(self.hop_seconds * sr)

        best_score = -1
        best_start = 0

        for start in range(0, total - win, hop):
            seg = y[start:start+win]
            rms = np.sqrt(np.mean(seg**2)) if seg.size>0 else 0.0
            if rms < 1e-4: continue

            zcr = np.mean(librosa.feature.zero_crossing_rate(seg))
            if zcr > 0.20: continue

            s = self.scorer.score(seg, sr)
            if s > best_score:
                best_score = s
                best_start = start

        end = best_start + win
        print(f"[Window] best {best_start} ~ {end}")
        return best_start, end

    # -------------------------------------------
    # Public API（只输出 5 秒，逻辑完全不变）
    # -------------------------------------------
    def extract_melody_to_wav(
        self,
        audio_path,
        strength=0.5,
        output_path=None,
        weaken_level=0,
        mode="low",
        target_style=None,
        target_emotion=None,
    ):
        y, sr = librosa.load(audio_path, sr=self.target_sr, mono=True)

        tonic_pc, mode_key, _ = self._detect_key(y, sr)

        s, e = self._find_best_window(y, sr)
        clip = y[s:e]

        if mode=="low":
            mel = self._extract_low_destruction(clip, sr)
        else:
            mel = clip.astype(np.float32)

        if output_path is None:
            output_path = Path(audio_path).parent / f"melody_best5s_attempt_{weaken_level+1}.wav"

        sf.write(str(output_path), mel, sr)
        print(f"[MelodyExtractor] Saved (5s): {output_path}")
        return str(output_path)
