import tempfile
import time
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Response, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from server import aivis_client
from vowel_extractor.aligners.julius_aligner import JuliusAligner
from vowel_extractor.aligners.mock_aligner import MockAligner
from vowel_extractor.extractor import VowelTimingExtractor

app = FastAPI(title="voice2boin")

STATIC_DIR = Path(__file__).parent / "static"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/analyze")
async def analyze(
    audio: UploadFile = File(...),
    text: str = Form(...),
    mode: str = Form("mock"),
):
    if mode not in ("mock", "julius"):
        raise HTTPException(status_code=400, detail="mode は 'mock' か 'julius' を指定してください")

    aligner = MockAligner() if mode == "mock" else JuliusAligner()
    extractor = VowelTimingExtractor(aligner=aligner)

    suffix = Path(audio.filename or "audio.wav").suffix or ".wav"
    start = time.perf_counter()
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=True) as tmp:
        tmp.write(await audio.read())
        tmp.flush()

        try:
            result = extractor.extract(tmp.name, text)
        except RuntimeError as e:
            raise HTTPException(status_code=500, detail=str(e))
    elapsed = time.perf_counter() - start

    data = result.to_dict()
    data["processing_time_sec"] = round(elapsed, 3)
    return JSONResponse(content=data)


@app.get("/api/speakers")
def speakers():
    try:
        raw_speakers = aivis_client.get_speakers()
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return [
        {"id": style["id"], "label": f"{speaker['name']} - {style['name']}"}
        for speaker in raw_speakers
        for style in speaker["styles"]
    ]


@app.post("/api/synthesize")
def synthesize(text: str = Form(...), speaker_id: int = Form(...)):
    start = time.perf_counter()
    try:
        wav_bytes = aivis_client.synthesize(None, text, speaker_id)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    elapsed = time.perf_counter() - start

    return Response(
        content=wav_bytes,
        media_type="audio/wav",
        headers={"X-Processing-Time": f"{elapsed:.3f}"},
    )
