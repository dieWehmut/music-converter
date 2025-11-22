# backend/dsp/demucs_runner.py

import subprocess
from pathlib import Path


class DemucsRunner:
    """
    使用 Demucs 进行 4 轨拆分的工具类（最稳定方案）
    输出：vocals.wav, drums.wav, bass.wav, other.wav
    """

    def __init__(self, output_dir="backend/dsp/stems"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def separate(self, audio_path: str) -> dict:
        """
        拆轨核心函数
        :param audio_path: 输入音频路径
        :return: dict，包含 4 轨文件路径
        """
        audio_path = Path(audio_path).resolve()
        if not audio_path.exists():
            raise FileNotFoundError(f"输入音频未找到: {audio_path}")

        print(f"[Demucs] 开始拆轨：{audio_path}")

        # 使用稳定模型 mdx_extra_q（CPU 最可靠）
        cmd = [
            "demucs",
            "-n", "mdx_extra_q",
            "--jobs=1",
            "--device", "cpu",
            str(audio_path)
        ]

        # 执行 demucs 命令
        subprocess.run(cmd, check=True)

        # Demucs 输出位置：~/demucs_separated/{model-name}/song-name
        demucs_root = Path("separated")

        # 找到最新一次拆轨输出
        result_dirs = sorted(demucs_root.glob("*"))
        if not result_dirs:
            raise RuntimeError("Demucs 没有生成输出目录，请检查模型是否正常运行。")

        latest_dir = result_dirs[-1]
        print(f"[Demucs] 拆轨输出目录：{latest_dir}")

        # 查找四条轨道
        try:
            vocals_file = list(latest_dir.rglob("vocals.wav"))[0]
            drums_file = list(latest_dir.rglob("drums.wav"))[0]
            bass_file = list(latest_dir.rglob("bass.wav"))[0]
            other_file = list(latest_dir.rglob("other.wav"))[0]
        except IndexError:
            raise RuntimeError("无法找到完整的 4 个拆轨文件，请检查 Demucs 输出。")

        # 输出到项目目录 backend/dsp/stems
        out_vocals = self.output_dir / "vocals.wav"
        out_drums = self.output_dir / "drums.wav"
        out_bass = self.output_dir / "bass.wav"
        out_other = self.output_dir / "other.wav"

        out_vocals.write_bytes(vocals_file.read_bytes())
        out_drums.write_bytes(drums_file.read_bytes())
        out_bass.write_bytes(bass_file.read_bytes())
        out_other.write_bytes(other_file.read_bytes())

        print("[Demucs] 拆轨完成！")

        return {
            "vocals": str(out_vocals),
            "drums": str(out_drums),
            "bass": str(out_bass),
            "other": str(out_other),
        }


if __name__ == "__main__":
    runner = DemucsRunner()
    result = runner.separate("backend/test_audio.wav")
    print(result)
