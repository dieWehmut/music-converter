<<<<<<< HEAD
<<<<<<< HEAD
import librosa
import numpy as np
import joblib
import scipy.signal

# 修复 hann 问题
if not hasattr(scipy.signal, "hann"):
    scipy.signal.hann = scipy.signal.windows.hann

MODEL_PATH = "backend/models/style_model.pkl"
ENCODER_PATH = "backend/models/style_label_encoder.pkl"


def extract_style_features(path):
    """
    === 与训练脚本严格一致的68维特征 ===
    顺序必须是：
    [tempo, rms, centroid] +
    chroma(12) +
    mel(40) +
    contrast(7) +
    tonnetz(6)
    """
    y, sr = librosa.load(path, sr=None, mono=True)

    # tempo
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)

    # rms
    rms = librosa.feature.rms(y=y)[0].mean()

    # spectral centroid
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0].mean()

    # chroma 12维
    chroma = librosa.feature.chroma_stft(y=y, sr=sr).mean(axis=1)

    # mel 40维
    mel = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=40)
    mel_mean = mel.mean(axis=1)

    # contrast 7维
    contrast = librosa.feature.spectral_contrast(y=y, sr=sr).mean(axis=1)

    # tonnetz 6维
    try:
        tonnetz = librosa.feature.tonnetz(
            y=librosa.effects.harmonic(y),
            sr=sr
        ).mean(axis=1)
    except Exception:
        tonnetz = np.zeros(6)

    # === 拼接成最终 68 维（顺序严格一致） ===
    feature = np.concatenate([
        [tempo, rms, centroid],
        chroma,
        mel_mean,
        contrast,
        tonnetz
    ])

    return feature.reshape(1, -1)


def predict_style(path):
    model = joblib.load(MODEL_PATH)
    encoder = joblib.load(ENCODER_PATH)

    feat = extract_style_features(path)
    pred = model.predict(feat)[0]

    return encoder.inverse_transform([pred])[0]


if __name__ == "__main__":
    test_path = r"D:\idea_python\music_project\backend\test_audio.wav"
    print("预测风格:", predict_style(test_path))
=======
=======
import joblib
>>>>>>> 368ab93 (need_test_try)
import librosa
import numpy as np

MODEL_PATH = "backend/models/style_model.pkl"
ENCODER_PATH = "backend/models/style_label_encoder.pkl"

model = joblib.load(MODEL_PATH)
encoder = joblib.load(ENCODER_PATH)


def extract_style_features(path):
    y, sr = librosa.load(path, sr=None, mono=True)

    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    rms = librosa.feature.rms(y=y).mean()
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr).mean()

    mel = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=40)
    mel_mean = mel.mean(axis=1)

    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    chroma_mean = chroma.mean(axis=1)

    feat = np.concatenate([[tempo, rms, centroid], mel_mean, chroma_mean])
    return feat.reshape(1, -1)


def predict_style(path):
    feat = extract_style_features(path)
<<<<<<< HEAD

    pred_idx = model.predict(feat)[0]
    label = encoder.inverse_transform([pred_idx])[0]

    # 预测概率
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
    print("prob:", p)
>>>>>>> 0cf27b1 (failed_v4)
=======
    prob = model.predict_proba(feat)[0]
    idx = np.argmax(prob)
    label = encoder.inverse_transform([idx])[0]
    return label, prob.tolist()
>>>>>>> 368ab93 (need_test_try)
