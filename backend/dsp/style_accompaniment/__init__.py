from pydub import AudioSegment
import os

ffmpeg_bin = r"C:\ffmpeg\bin"

AudioSegment.converter = os.path.join(ffmpeg_bin, "ffmpeg.exe")
AudioSegment.ffprobe = os.path.join(ffmpeg_bin, "ffprobe.exe")
