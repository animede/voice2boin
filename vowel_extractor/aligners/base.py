from abc import ABC, abstractmethod

from ..types import PhonemeSegment


class Aligner(ABC):
    """音声とテキスト(音素列)から強制アライメントを行う抽象基底クラス"""

    @abstractmethod
    def align(self, wav_path: str, phonemes: list[str]) -> list[PhonemeSegment]:
        """wav_path の音声と phonemes を強制アライメントし、音素ごとの区間を返す"""
        raise NotImplementedError
