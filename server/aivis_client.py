"""AivisSpeech Engine (VOICEVOX互換TTS) と通信するクライアント。"""
import os

import httpx

DEFAULT_BASE_URL = "http://127.0.0.1:10101"
TIMEOUT = 30.0


def get_base_url() -> str:
    return os.environ.get("AIVIS_ENGINE_URL", DEFAULT_BASE_URL)


def _connection_error(base_url: str) -> RuntimeError:
    return RuntimeError(
        f"AivisSpeech Engineに接続できません({base_url} が起動しているか確認してください)"
    )


def get_speakers(base_url: str | None = None) -> list[dict]:
    base_url = base_url or get_base_url()
    try:
        res = httpx.get(f"{base_url}/speakers", timeout=TIMEOUT)
        res.raise_for_status()
    except httpx.RequestError:
        raise _connection_error(base_url)
    return res.json()


def synthesize(base_url: str | None, text: str, speaker_id: int) -> bytes:
    base_url = base_url or get_base_url()
    try:
        query_res = httpx.post(
            f"{base_url}/audio_query",
            params={"text": text, "speaker": speaker_id},
            timeout=TIMEOUT,
        )
        query_res.raise_for_status()

        synth_res = httpx.post(
            f"{base_url}/synthesis",
            params={"speaker": speaker_id},
            json=query_res.json(),
            timeout=TIMEOUT,
        )
        synth_res.raise_for_status()
    except httpx.RequestError:
        raise _connection_error(base_url)

    return synth_res.content
