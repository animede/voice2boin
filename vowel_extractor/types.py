from dataclasses import dataclass


@dataclass
class PhonemeSegment:
    """強制アライメントで得られる音素1つ分の区間情報"""

    phoneme: str
    start: float
    end: float

    @property
    def duration(self) -> float:
        return self.end - self.start


@dataclass
class VowelSegment:
    """母音(a/i/u/e/o、任意でN)の区間情報"""

    vowel: str
    start: float
    end: float

    @property
    def duration(self) -> float:
        return self.end - self.start
