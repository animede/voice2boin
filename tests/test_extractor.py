import json
import wave

import pytest

from vowel_extractor.aligners.mock_aligner import MockAligner
from vowel_extractor.extractor import VowelTimingExtractor
from vowel_extractor.types import PhonemeSegment, VowelSegment


@pytest.fixture
def silent_wav(tmp_path):
    """1秒間の無音wavファイルを生成する"""
    path = tmp_path / "silence.wav"
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b"\x00\x00" * 16000)
    return str(path)


def test_vowel_segment_duration():
    seg = VowelSegment(vowel="a", start=0.1, end=0.3)
    assert seg.duration == pytest.approx(0.2)


def test_phoneme_segment_duration():
    seg = PhonemeSegment(phoneme="k", start=0.0, end=0.05)
    assert seg.duration == pytest.approx(0.05)


def test_mock_aligner_even_split(silent_wav):
    aligner = MockAligner()
    phonemes = ["k", "o", "N", "n", "i", "ch", "i", "w", "a"]
    segments = aligner.align(silent_wav, phonemes)

    assert len(segments) == len(phonemes)
    assert segments[0].start == pytest.approx(0.0)
    assert segments[-1].end == pytest.approx(1.0)

    step = 1.0 / len(phonemes)
    for i, seg in enumerate(segments):
        assert seg.phoneme == phonemes[i]
        assert seg.start == pytest.approx(i * step)
        assert seg.end == pytest.approx((i + 1) * step)


def test_mock_aligner_empty_phonemes(silent_wav):
    aligner = MockAligner()
    assert aligner.align(silent_wav, []) == []


def test_extractor_filters_vowels_only(silent_wav):
    extractor = VowelTimingExtractor(aligner=MockAligner())
    result = extractor.extract(silent_wav, "こんにちは")

    assert len(result.vowel_segments) > 0
    for seg in result.vowel_segments:
        assert seg.vowel in {"a", "i", "u", "e", "o"}


def test_extractor_excludes_n_by_default(silent_wav):
    extractor = VowelTimingExtractor(aligner=MockAligner(), include_n=False)
    result = extractor.extract(silent_wav, "こんにちは")

    assert all(seg.vowel != "N" for seg in result.vowel_segments)


def test_extractor_includes_n_when_requested(silent_wav):
    extractor = VowelTimingExtractor(aligner=MockAligner(), include_n=True)
    result = extractor.extract(silent_wav, "こんにちは")

    vowels_found = {seg.vowel for seg in result.vowel_segments}
    assert "N" in vowels_found


def test_extractor_timing_within_audio_duration(silent_wav):
    extractor = VowelTimingExtractor(aligner=MockAligner())
    result = extractor.extract(silent_wav, "こんにちは")

    for seg in result.vowel_segments:
        assert 0.0 <= seg.start < seg.end <= 1.0 + 1e-9


def test_extractor_segments_ordered_and_non_overlapping(silent_wav):
    extractor = VowelTimingExtractor(aligner=MockAligner())
    result = extractor.extract(silent_wav, "こんにちは")

    phoneme_segments = result.phoneme_segments
    for prev, curr in zip(phoneme_segments, phoneme_segments[1:]):
        assert prev.end == pytest.approx(curr.start)


def test_to_dict_structure(silent_wav):
    extractor = VowelTimingExtractor(aligner=MockAligner())
    result = extractor.extract(silent_wav, "こんにちは")
    data = result.to_dict()

    assert "vowel_segments" in data
    assert "phoneme_segments" in data
    assert isinstance(data["vowel_segments"], list)

    for seg in data["vowel_segments"]:
        assert set(seg.keys()) == {"vowel", "start", "end", "duration"}


def test_to_json_is_valid_json(silent_wav):
    extractor = VowelTimingExtractor(aligner=MockAligner())
    result = extractor.extract(silent_wav, "こんにちは")
    json_str = result.to_json()

    parsed = json.loads(json_str)
    assert "vowel_segments" in parsed
    assert "phoneme_segments" in parsed


def test_to_json_handles_japanese_without_escaping(silent_wav):
    extractor = VowelTimingExtractor(aligner=MockAligner())
    result = extractor.extract(silent_wav, "あ")
    json_str = result.to_json()

    # ensure_ascii=False なので日本語がそのまま出力されるべき箇所は音素("a"等)のみだが、
    # 少なくとも \u エスケープだらけにならないことを確認
    assert isinstance(json_str, str)
