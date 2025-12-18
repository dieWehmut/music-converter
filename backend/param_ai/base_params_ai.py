class BaseParamsAI:
    """
    Param AI 的基类：负责根据 style + emotion 动态生成音乐参数
    最终输出结构化 Prompt，给 MusicGen 使用
    """

    def __init__(self, style, emotion, length_s=20):
        self.style = style
        self.emotion = emotion
        self.length_s = length_s

        # 参数库（各风格模块会 override）
        self.scale = None         # 音阶（major / minor）
        self.chords = []          # 和弦进行
        self.melody = []          # 主旋律音符
        self.bass = []            # Bass line
        self.drums = ""           # 鼓描述文本
        self.structure = ""       # AABA / ABAC / Verse-Chorus
        self.tempo = 110          # 默认 bpm

    def build_prompt(self):
        """
        组合成 MusicGen 可用的 Prompt（核心输出）
        """

        prompt = f"""
        Style: {self.style}
        Emotion: {self.emotion}
        Tempo: {self.tempo} BPM
        Key: {self.scale}

        Structure: {self.structure}

        Chord Progression: {', '.join(self.chords)}

        Melody pattern: {self.melody}

        Bass line: {self.bass}

        Drum style: {self.drums}
        """

        # 把 prompt 压缩成一行，防止换行带来模型误解
        return " ".join(prompt.split())
