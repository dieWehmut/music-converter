<<<<<<< HEAD
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
        window_seconds: float = 30.0,    
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

            # =========== 修改点：处理短音频 ===========
            # 如果音频总长度 <= 窗口长度 (比如原曲12秒，我们要截30秒)
            # 直接返回 0 到 结尾，不进行滑动窗口搜索
            if total <= win:
                print(f"[Window] Audio is short ({total/sr:.2f}s). Using full length.")
                return 0, total
            # ========================================

            best_score = -1
            best_start = 0

            # 只有当 total > win 时，这里才会执行
            for start in range(0, total - win, hop):
                seg = y[start:start+win]
                
                # 避免全静音片段
                rms = np.sqrt(np.mean(seg**2)) if seg.size > 0 else 0.0
                if rms < 1e-4: continue

                # 避免噪音/过高过零率片段
                zcr = np.mean(librosa.feature.zero_crossing_rate(seg))
                if zcr > 0.20: continue

                # 计算旋律评分
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
=======
import librosa
import soundfile as sf
import numpy as np
from pathlib import Path

class MelodyExtractor:
    """
    Balanced 旋律提取版：
    - 保留旋律清晰可听
    - 轻微弱化，让风格转换更明显
    - 不会无声 / 不会过度破坏
    """

    def __init__(self, target_sr=32000):
        self.target_sr = target_sr

    def extract_melody_to_wav(self, audio_path, output_path=None):
        # 加载音频（32kHz）
        y, sr = librosa.load(audio_path, sr=self.target_sr, mono=True)

        # -------------------------------
        # Step 1 — 保留旋律但稍弱化
        # -------------------------------
        y = y * 0.2  # 音量保留 20%，弱化但仍可听

        # -------------------------------
        # Step 2 — 轻度低通滤波
        # -------------------------------
        y = librosa.effects.preemphasis(y, coef=-0.8)  # 柔化高频，不破坏旋律

        # -------------------------------
        # Step 3 — 加轻微噪声，保证差异明显
        # -------------------------------
        y += np.random.randn(len(y)) * 0.0015  # 轻噪，不会听不见

        # -------------------------------
        # Step 4 — 限制最长时间（防 MusicGen 崩溃）
        # -------------------------------
        MAX_SECONDS = 12
        max_len = self.target_sr * MAX_SECONDS
        if len(y) > max_len:
            y = y[:max_len]

        # -------------------------------
        # Step 5 — 保存
        # -------------------------------
        if output_path is None:
            parent = Path(audio_path).parent
            output_path = parent / "melody.wav"

        sf.write(output_path, y, self.target_sr)
        return str(output_path)
>>>>>>> decbe0b (style_emo_model_v2)
