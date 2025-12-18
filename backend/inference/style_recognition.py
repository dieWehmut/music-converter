import librosa
import numpy as np
import joblib
import scipy.signal
from typing import Dict, Tuple

from backend.utils.safe_librosa import (
    safe_rms,
    safe_spectral_centroid,
    safe_chroma_stft,
    safe_spectral_contrast,
)

# 修复 librosa hann
if not hasattr(scipy.signal, "hann"):
    scipy.signal.hann = scipy.signal.windows.hann

MODEL_PATH = "backend/models/style_model.pkl"
ENCODER_PATH = "backend/models/style_label_encoder.pkl"

# =========================
# 全局加载模型 & encoder
# =========================
try:
    _STYLE_MODEL = joblib.load(MODEL_PATH)
except Exception as e:
    raise RuntimeError(
        f"[style_recognition] 无法加载模型：{MODEL_PATH}\n{e}"
    )

try:
    _STYLE_ENCODER = joblib.load(ENCODER_PATH)
except Exception as e:
    raise RuntimeError(
        f"[style_recognition] 无法加载标签编码器：{ENCODER_PATH}\n{e}"
    )


def extract_style_features(path: str) -> np.ndarray:
    """
    === 与训练一致的 68 维特征 ===
    """
    y, sr = librosa.load(path, sr=None, mono=True)

    # ---- tempo ----
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)

    # ---- RMS（兼容） ----
    rms = safe_rms(y, sr)

    # ---- centroid（兼容） ----
    centroid = safe_spectral_centroid(y, sr)

    # ---- chroma ----
    chroma = safe_chroma_stft(y, sr)

    # ---- mel ----
    mel = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=40)
    try:
        mel = mel.mean(axis=1)
    except Exception:
        mel = np.ravel(mel)

    # ---- contrast ----
    contrast = safe_spectral_contrast(y, sr)

    # ---- tonnetz（部分音频会失败，兜底） ----
    try:
        tonnetz = librosa.feature.tonnetz(
            y=librosa.effects.harmonic(y),
            sr=sr,
        )
        try:
            tonnetz = tonnetz.mean(axis=1)
        except Exception:
            tonnetz = np.ravel(tonnetz)
    except Exception:
        tonnetz = np.zeros(6)

    # --- ensure tempo/rms/centroid are scalars (robust to librosa shape variations) ---
    # Sometimes librosa feature helpers or beat_track return 1-D arrays for short audio;
    # coerce to scalar via mean(), and log shapes when unexpected to help debugging.
    try:
        t_val = float(np.asarray(tempo).mean())
    except Exception:
        t_val = float(tempo)

    try:
        r_val = float(np.asarray(rms).mean())
    except Exception:
        r_val = float(rms)

    try:
        c_val = float(np.asarray(centroid).mean())
    except Exception:
        c_val = float(centroid)

    parts = []
    # debug: print coerced scalar values and original types/shapes
    try:
        print(f"DEBUG style: t_val={t_val} type={type(t_val)} tempo_orig_type={type(tempo)} repr={repr(tempo)[:200]}")
        print(f"DEBUG style: r_val={r_val} type={type(r_val)} rms_orig_type={type(rms)} repr={repr(rms)[:200]}")
        print(f"DEBUG style: c_val={c_val} type={type(c_val)} centroid_orig_type={type(centroid)} repr={repr(centroid)[:200]}")
    except Exception:
        # best-effort debug prints should never raise
        pass

    parts.append(np.array([t_val, r_val, c_val], dtype=float))
    for arr in (chroma, mel, contrast, tonnetz):
        a = np.array(arr, dtype=float)
        if a.ndim == 0:
            a = a.reshape(1)
        elif a.ndim > 1:
            # collapse extra dimensions by taking mean over trailing axes
            a = a.reshape(a.shape[0], -1).mean(axis=1)
        try:
            parts.append(a.flatten())
        except Exception:
            try:
                print(f"DEBUG style: failed flattening feature, type={type(a)} repr={repr(a)[:300]}")
            except Exception:
                pass
            parts.append(np.ravel(a).astype(float))
    try:
        feature = np.concatenate(parts)
    except Exception as e:
        # print shapes/types for debugging and re-raise
        try:
            for i, p in enumerate(parts):
                try:
                    print(f"DEBUG style: part[{i}] type={type(p)} ndim={getattr(p,'ndim',None)} shape={getattr(p,'shape',None)} repr_preview={repr(p)[:200]}")
                except Exception:
                    print(f"DEBUG style: part[{i}] info unavailable")
        except Exception:
            pass
        raise

    return feature.reshape(1, -1)


def predict_style(path: str) -> Tuple[str, Dict[str, float]]:
    feat = extract_style_features(path)

    model = _STYLE_MODEL
    encoder = _STYLE_ENCODER

    idx = model.predict(feat)[0]
    label = encoder.inverse_transform([idx])[0]

    try:
        prob = model.predict_proba(feat)[0]
        classes = encoder.classes_
        prob_dict = {classes[i]: float(prob[i]) for i in range(len(classes))}
    except Exception:
        classes = encoder.classes_
        prob_dict = {cls: (1.0 if cls == label else 0.0) for cls in classes}

    return label, prob_dict


if __name__ == "__main__":
    test_path = r"backend/test_audio.wav"
    s, p = predict_style(test_path)
    print("预测风格:", s)
    print("概率:", p)
