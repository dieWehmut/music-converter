from transformers import AutoProcessor, MusicgenForConditionalGeneration
import librosa
import numpy as np
import scipy.io.wavfile

model_name = "facebook/musicgen-small"

processor = AutoProcessor.from_pretrained(model_name)
model = MusicgenForConditionalGeneration.from_pretrained(model_name)

# ====== 读取音频 ======
audio_path = "backend/test_audio.wav"

wav, sr = librosa.load(audio_path, sr=32000, mono=True)
# wav shape = (samples,)

# 限制 10 秒
wav = wav[: 32000 * 10]

# ===== 关键：保持为一维 !!!!! =====
wav = wav.astype(np.float32)

print("最终 wav shape =", wav.shape)  # (samples,)

prompt = ["angry rock version of this melody"]

# 传入 list
inputs = processor(
    text=prompt,
    audio=[wav],              # ← 一维数组
    sampling_rate=32000,
    return_tensors="pt",
)

print("Generating...")
audio_values = model.generate(
    **inputs,
    max_new_tokens=512,
)

audio = audio_values[0, 0].cpu().numpy()
scipy.io.wavfile.write("ref_output.wav", 32000, audio)

print("生成完成：ref_output.wav")
