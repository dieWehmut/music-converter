# backend/inference/melody_scorer.py

import numpy as np
import librosa


class MelodyScorer:
    """
    Melody Scorer v1
    评分旋律的“人耳好听程度”，范围 0~1，越高越悦耳。

    五个评分项：
    1. 平滑度 Smoothness
    2. 音程 Interval Penalty
    3. 重复度 Pattern Stability (Hook)
    4. 节奏规律度 Rhythm Regularity
    5. 调式匹配度 Scale Fit
    """

    @staticmethod
    def _extract_f0(y, sr):
        """稳定版 f0 提取"""
        try:
            f0, _, _ = librosa.pyin(
                y,
                fmin=65.4,       # C2
                fmax=1046.5,     # C6
                sr=sr,
                frame_length=2048,
                hop_length=256,
            )
        except TypeError:
            f0, _, _ = librosa.pyin(y, 65.4, 1046.5, sr=sr)

        return f0

    # ------------------------------------------------------------
    # 1. Smoothness（平滑度）
    # ------------------------------------------------------------
    @staticmethod
    def smoothness_score(f0):
        f0 = f0.copy()
        f0 = f0[~np.isnan(f0)]
        if len(f0) < 5:
            return 0.2

        diff2 = np.abs(np.diff(f0, n=2))
        score = 1 / (1 + np.mean(diff2) / 20.0)
        return float(np.clip(score, 0, 1))

    # ------------------------------------------------------------
    # 2. Interval penalty（音程跳跃）
    # ------------------------------------------------------------
    @staticmethod
    def interval_score(f0):
        f0 = f0.copy()
        f0 = f0[~np.isnan(f0)]
        if len(f0) < 5:
            return 0.2

        intervals = np.abs(np.diff(f0))
        intervals = intervals[intervals < 2000]  # 避免异常值
        if len(intervals) == 0:
            return 0.2

        # 转半音
        semitones = 12 * np.log2(intervals / 440 + 1e-6)

        # 惩罚
        large_jump_penalty = np.mean(semitones > 9)  # 9半音以上重罚
        medium_jump_penalty = np.mean((semitones > 5) & (semitones <= 9))

        score = 1 - (0.7 * large_jump_penalty + 0.3 * medium_jump_penalty)
        return float(np.clip(score, 0, 1))

    # ------------------------------------------------------------
    # 新增：Contour score（旋律走向平滑程度）
    # ------------------------------------------------------------
    @staticmethod
    def contour_score(f0):
        """
        简单轮廓评分：
        - 先去掉 NaN
        - 看一阶差分的方差和范围，越稳定越高分
        """
        f0 = f0.copy()
        f0 = f0[~np.isnan(f0)]
        if len(f0) < 5:
            return 0.3

        diff = np.diff(f0)
        if len(diff) == 0:
            return 0.3

        norm = np.median(f0) + 1e-6
        diff_norm = diff / norm

        var = np.var(diff_norm)
        rng = np.max(diff_norm) - np.min(diff_norm)

        score = 1.0 / (1.0 + 3.0 * var + 0.5 * abs(rng))
        return float(np.clip(score, 0.0, 1.0))

    # ------------------------------------------------------------
    # 3. Pattern stability（重复结构 Hook）
    # ------------------------------------------------------------
    @staticmethod
    def hook_score(f0):
        f0 = f0.copy()
        f0 = f0[~np.isnan(f0)]
        if len(f0) < 10:
            return 0.2

        corr = np.correlate(f0 - np.mean(f0), f0 - np.mean(f0), mode="full")
        corr = corr[len(corr)//2:]

        # 跳过前0.2s避免无意义自相关
        skip = 5
        peak = np.max(corr[skip:]) / (np.sum(f0**2) + 1e-9)

        return float(np.clip(peak, 0, 1))

    # ------------------------------------------------------------
    # 4. Rhythm regularity（节奏规律）
    # ------------------------------------------------------------
    @staticmethod
    def rhythm_score(y, sr):
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env)

        if len(onset_frames) < 2:
            return 0.3

        times = librosa.frames_to_time(onset_frames, sr=sr)
        diff = np.diff(times)
        if len(diff) < 2:
            return 0.4

        # 越稳定分布越好
        var = np.var(diff)
        score = 1 / (1 + var * 4)

        return float(np.clip(score, 0, 1))

    # ------------------------------------------------------------
    # 5. Scale fit（音阶匹配）
    # ------------------------------------------------------------
    @staticmethod
    def scale_score(f0):
        f0 = f0.copy()
        f0 = f0[~np.isnan(f0)]
        if len(f0) < 5:
            return 0.3

        midi = librosa.hz_to_midi(f0)

        # 五声音阶
        pentatonic = np.array([0, 2, 4, 7, 9])
        diffs = np.abs((midi[:, None] - pentatonic[None, :]) % 12)
        min_dist = np.min(diffs, axis=1)

        score = np.mean(min_dist < 1.2)  # 容差
        return float(np.clip(score, 0, 1))

    # ------------------------------------------------------------
    # 总分（强 Hook 版）
    # ------------------------------------------------------------
    def score(self, y, sr):
        f0 = self._extract_f0(y, sr)

        smooth = self.smoothness_score(f0)
        interval = self.interval_score(f0)
        hook = self.hook_score(f0)
        rhythm = self.rhythm_score(y, sr)
        scale = self.scale_score(f0)

        total = (
            0.70 * hook +
            0.15 * smooth +
            0.05 * interval +
            0.05 * rhythm +
            0.05 * scale
        )

        return float(np.clip(total, 0, 1))
