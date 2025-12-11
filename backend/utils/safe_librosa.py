import librosa

def safe_rms(y, sr=None):
    """兼容 librosa 0.9.x 与 0.10.x"""
    try:
        return librosa.feature.rms(y=y, sr=sr)[0]
    except TypeError:
        return librosa.feature.rms(y=y)[0]

def safe_spectral_centroid(y, sr):
    try:
        return librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    except TypeError:
        return librosa.feature.spectral_centroid(y=y)[0]

def safe_chroma_stft(y, sr):
    try:
        return librosa.feature.chroma_stft(y=y, sr=sr).mean(axis=1)
    except TypeError:
        return librosa.feature.chroma_stft(y=y).mean(axis=1)

def safe_spectral_contrast(y, sr):
    try:
        return librosa.feature.spectral_contrast(y=y, sr=sr).mean(axis=1)
    except TypeError:
        return librosa.feature.spectral_contrast(y=y).mean(axis=1)

def safe_pitch_shift(y, sr, steps):
    try:
        return librosa.effects.pitch_shift(y=y, sr=sr, n_steps=steps)
    except TypeError:
        return librosa.effects.pitch_shift(y, sr, steps)

def safe_time_stretch(y, rate):
    try:
        return librosa.effects.time_stretch(y=y, rate=rate)
    except TypeError:
        return librosa.effects.time_stretch(y, rate)
