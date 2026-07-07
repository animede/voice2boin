import wave

from .base import Aligner
from ..types import PhonemeSegment


class MockAligner(Aligner):
    """Juliusなしでパイプライン/UIの動作確認をするためのダミー実装。

    音声の全長を音素数で均等割りして仮のタイミングを生成するだけであり、
    実際の発音タイミングとは一致しない。本番の精度用途ではなく、デモ・テスト用。
    """

    def align(self, wav_path: str, phonemes: list[str]) -> list[PhonemeSegment]:
        duration = self._get_duration(wav_path)
        n = len(phonemes)
        if n == 0:
            return []

        step = duration / n
        segments = []
        for i, phoneme in enumerate(phonemes):
            start = i * step
            end = (i + 1) * step
            segments.append(PhonemeSegment(phoneme=phoneme, start=start, end=end))
        return segments

    @staticmethod
    def _get_duration(wav_path: str) -> float:
        with wave.open(wav_path, "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            return frames / float(rate)
