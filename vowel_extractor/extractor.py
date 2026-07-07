import json
from dataclasses import dataclass, field

from .aligners.base import Aligner
from .aligners.mock_aligner import MockAligner
from .text_to_phoneme import text_to_phonemes
from .types import PhonemeSegment, VowelSegment

VOWELS = {"a", "i", "u", "e", "o"}
MORAIC_NASAL = "N"


@dataclass
class VowelTimingResult:
    """VowelTimingExtractor.extract() の戻り値"""

    vowel_segments: list[VowelSegment]
    phoneme_segments: list[PhonemeSegment] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "vowel_segments": [
                {
                    "vowel": seg.vowel,
                    "start": seg.start,
                    "end": seg.end,
                    "duration": seg.duration,
                }
                for seg in self.vowel_segments
            ],
            "phoneme_segments": [
                {
                    "phoneme": seg.phoneme,
                    "start": seg.start,
                    "end": seg.end,
                    "duration": seg.duration,
                }
                for seg in self.phoneme_segments
            ],
        }

    def to_json(self, **kwargs) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, **kwargs)


class VowelTimingExtractor:
    """テキスト→音素変換 + 強制アライメントを組み合わせ、母音のタイミングを抽出する"""

    def __init__(self, aligner: Aligner | None = None, include_n: bool = False):
        self.aligner = aligner or MockAligner()
        self.include_n = include_n

    def extract(self, wav_path: str, text: str) -> VowelTimingResult:
        phonemes = text_to_phonemes(text)
        phoneme_segments = self.aligner.align(wav_path, phonemes)

        target_vowels = VOWELS | {MORAIC_NASAL} if self.include_n else VOWELS

        vowel_segments = [
            VowelSegment(vowel=seg.phoneme, start=seg.start, end=seg.end)
            for seg in phoneme_segments
            if seg.phoneme in target_vowels
        ]

        return VowelTimingResult(
            vowel_segments=vowel_segments, phoneme_segments=phoneme_segments
        )
