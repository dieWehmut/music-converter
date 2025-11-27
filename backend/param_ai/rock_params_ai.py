from .base_params_ai import BaseParamsAI
import random


class RockParamsAI(BaseParamsAI):

    def __init__(self, emotion, length_s=20):
        super().__init__(style="rock", emotion=emotion, length_s=length_s)
        self.generate_all()

    # ====== 规则 1：Rock 的调式 ======
    def choose_scale(self):
        if self.emotion in ["sad", "scary", "angry"]:
            return "E minor"
        else:
            return "E major"

    # ====== 规则 2：和弦（Power Chord） ======
    def generate_chords(self):
        if "sad" in self.emotion:
            return ["Em", "G", "D", "Am"]
        if "angry" in self.emotion:
            return ["E5", "G5", "A5", "B5"]
        if "happy" in self.emotion:
            return ["E", "A", "B", "C#m"]
        return ["Em", "C", "D", "G"]

    # ====== 规则 3：鼓 ======
    def drum_pattern(self):
        if "angry" in self.emotion:
            return "Heavy kick, loud snare, fast hi-hat, double-pedal feeling"
        if "sad" in self.emotion:
            return "Soft kick, low snare, gentle ride cymbal"
        if "happy" in self.emotion:
            return "Bright snare, steady 4/4 kick, open hi-hat"
        return "Standard rock drum kit"

    # ====== 规则 4：旋律（按情绪随机生成） ======
    def generate_melody(self):
        patterns = {
            "sad":  ["E4", "G4", "F#4", "E4", "D4"],
            "angry": ["E4", "E4", "G4", "A4", "B4"],
            "happy": ["E4", "F#4", "G#4", "B4", "C#5"],
            "tender": ["E4", "G#4", "A4", "B4", "A4"]
        }
        return patterns.get(self.emotion, ["E4", "G4", "A4"])

    # ====== 规则 5：Bass ======
    def generate_bass(self):
        root_map = {
            "Em": "E2",
            "G": "G2",
            "D": "D2",
            "Am": "A2",
            "E5": "E2",
            "A5": "A2",
            "B5": "B2",
        }
        return [root_map.get(ch, "E2") for ch in self.chords]

    # ====== 规则 6：曲式 ======
    def choose_structure(self):
        if "angry" in self.emotion:
            return "Intro – Verse – Verse – Break – Verse"
        if "sad" in self.emotion:
            return "Intro – Verse – Chorus – Verse – Outro"
        return "Verse – Chorus – Verse – Chorus"

    # ====== 调用全部规则 ======
    def generate_all(self):
        self.scale = self.choose_scale()
        self.chords = self.generate_chords()
        self.drums = self.drum_pattern()
        self.melody = self.generate_melody()
        self.bass = self.generate_bass()
        self.structure = self.choose_structure()
        self.tempo = 120 if "angry" in self.emotion else 100
