const VOWEL_COLORS = {
  a: "var(--color-a)",
  i: "var(--color-i)",
  u: "var(--color-u)",
  e: "var(--color-e)",
  o: "var(--color-o)",
  N: "var(--color-n)",
};
const VOWEL_LABELS = { a: "a", i: "i", u: "u", e: "e", o: "o", N: "N (撥音)" };

const form = document.getElementById("analyze-form");
const statusEl = document.getElementById("status");
const resultPanel = document.getElementById("result-panel");
const audioPlayer = document.getElementById("audio-player");
const timelineEl = document.getElementById("timeline");
const legendEl = document.getElementById("legend");
const tableBody = document.querySelector("#segments-table tbody");
const jsonOutput = document.getElementById("json-output");
const toggleJsonBtn = document.getElementById("toggle-json");
const analyzeBtn = document.getElementById("analyze-btn");
const speakerSelect = document.getElementById("speaker-select");
const synthesizeBtn = document.getElementById("synthesize-btn");
const ttsStatusEl = document.getElementById("tts-status");
const audioFileInput = document.getElementById("audio-file");

let currentSegments = [];
let audioDuration = 0;

async function loadSpeakers() {
  try {
    const res = await fetch("/api/speakers");
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `話者一覧の取得に失敗しました (HTTP ${res.status})`);
    }
    const speakers = await res.json();
    speakerSelect.innerHTML = "";
    for (const speaker of speakers) {
      const option = document.createElement("option");
      option.value = speaker.id;
      option.textContent = speaker.label;
      speakerSelect.appendChild(option);
    }
  } catch (err) {
    ttsStatusEl.textContent = "AivisSpeech Engineに接続できませんでした: " + err.message;
    ttsStatusEl.classList.add("error");
    synthesizeBtn.disabled = true;
  }
}
loadSpeakers();

synthesizeBtn.addEventListener("click", async () => {
  ttsStatusEl.textContent = "";
  ttsStatusEl.classList.remove("error");

  const text = document.getElementById("text-input").value;
  if (!text.trim()) {
    ttsStatusEl.textContent = "原稿テキストを入力してください";
    ttsStatusEl.classList.add("error");
    return;
  }

  const speakerId = speakerSelect.value;
  const formData = new FormData();
  formData.append("text", text);
  formData.append("speaker_id", speakerId);

  synthesizeBtn.disabled = true;
  ttsStatusEl.textContent = "音声合成中...";

  try {
    const res = await fetch("/api/synthesize", { method: "POST", body: formData });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `音声合成に失敗しました (HTTP ${res.status})`);
    }
    const processingTime = res.headers.get("X-Processing-Time");
    const blob = await res.blob();
    const file = new File([blob], "synthesized.wav", { type: "audio/wav" });

    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);
    audioFileInput.files = dataTransfer.files;
    audioFileInput.dispatchEvent(new Event("change"));

    const timeMsg = processingTime ? `(処理時間: ${Number(processingTime).toFixed(2)}秒)` : "";
    ttsStatusEl.textContent = `音声合成が完了しました${timeMsg}。音声ファイル欄にセットされました`;
  } catch (err) {
    ttsStatusEl.textContent = err.message;
    ttsStatusEl.classList.add("error");
  } finally {
    synthesizeBtn.disabled = false;
  }
});

audioFileInput.addEventListener("change", () => {
  const file = audioFileInput.files[0];
  if (file) {
    audioPlayer.src = URL.createObjectURL(file);
  }
});

function buildLegend() {
  legendEl.innerHTML = "";
  for (const [key, label] of Object.entries(VOWEL_LABELS)) {
    const item = document.createElement("div");
    item.className = "legend-item";
    item.innerHTML = `<span class="legend-swatch" style="background:${VOWEL_COLORS[key]}"></span>${label}`;
    legendEl.appendChild(item);
  }
}
buildLegend();

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  statusEl.textContent = "";
  statusEl.classList.remove("error");

  const fileInput = document.getElementById("audio-file");
  const text = document.getElementById("text-input").value;
  const mode = document.getElementById("mode-select").value;
  const file = fileInput.files[0];

  if (!file) {
    statusEl.textContent = "音声ファイルを選択してください";
    statusEl.classList.add("error");
    return;
  }

  const objectUrl = URL.createObjectURL(file);
  audioPlayer.src = objectUrl;

  const formData = new FormData();
  formData.append("audio", file);
  formData.append("text", text);
  formData.append("mode", mode);

  analyzeBtn.disabled = true;
  statusEl.textContent = "解析中...";

  try {
    const res = await fetch("/api/analyze", { method: "POST", body: formData });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `解析に失敗しました (HTTP ${res.status})`);
    }
    const data = await res.json();
    const timeMsg = typeof data.processing_time_sec === "number"
      ? `(処理時間: ${data.processing_time_sec.toFixed(3)}秒)`
      : "";
    statusEl.textContent = `解析が完了しました${timeMsg}`;
    renderResult(data);
  } catch (err) {
    statusEl.textContent = err.message;
    statusEl.classList.add("error");
  } finally {
    analyzeBtn.disabled = false;
  }
});

function renderResult(data) {
  resultPanel.hidden = false;
  currentSegments = data.vowel_segments || [];

  jsonOutput.textContent = JSON.stringify(data, null, 2);

  audioDuration = currentSegments.length
    ? Math.max(...currentSegments.map((s) => s.end))
    : 0;

  const onMetadata = () => {
    const duration = audioPlayer.duration && isFinite(audioPlayer.duration)
      ? audioPlayer.duration
      : audioDuration;
    renderTimeline(currentSegments, duration);
  };

  if (audioPlayer.readyState >= 1) {
    onMetadata();
  } else {
    audioPlayer.addEventListener("loadedmetadata", onMetadata, { once: true });
  }

  renderTable(currentSegments);
}

function renderTimeline(segments, duration) {
  timelineEl.innerHTML = "";
  if (!duration || duration <= 0) return;

  segments.forEach((seg, idx) => {
    const div = document.createElement("div");
    div.className = "timeline-segment";
    div.dataset.index = idx;
    const leftPct = (seg.start / duration) * 100;
    const widthPct = ((seg.end - seg.start) / duration) * 100;
    div.style.left = `${leftPct}%`;
    div.style.width = `${Math.max(widthPct, 0.3)}%`;
    div.style.background = VOWEL_COLORS[seg.vowel] || "var(--color-pause)";

    const tooltip = document.createElement("div");
    tooltip.className = "timeline-tooltip";
    tooltip.textContent = `${seg.vowel}: ${seg.start.toFixed(2)}s - ${seg.end.toFixed(2)}s`;
    div.appendChild(tooltip);

    div.addEventListener("click", () => {
      audioPlayer.currentTime = seg.start;
      audioPlayer.play();
    });

    timelineEl.appendChild(div);
  });
}

function renderTable(segments) {
  tableBody.innerHTML = "";
  segments.forEach((seg, idx) => {
    const tr = document.createElement("tr");
    tr.dataset.index = idx;
    tr.innerHTML = `
      <td>${seg.vowel}</td>
      <td>${seg.start.toFixed(3)}</td>
      <td>${seg.end.toFixed(3)}</td>
      <td>${seg.duration.toFixed(3)}</td>
    `;
    tableBody.appendChild(tr);
  });
}

audioPlayer.addEventListener("timeupdate", () => {
  const t = audioPlayer.currentTime;
  const activeIdx = currentSegments.findIndex((s) => t >= s.start && t < s.end);

  document.querySelectorAll(".timeline-segment").forEach((el) => {
    el.classList.toggle("active", Number(el.dataset.index) === activeIdx);
  });
  document.querySelectorAll("#segments-table tbody tr").forEach((el) => {
    el.classList.toggle("active-row", Number(el.dataset.index) === activeIdx);
  });
});

toggleJsonBtn.addEventListener("click", () => {
  const hidden = jsonOutput.hidden;
  jsonOutput.hidden = !hidden;
  toggleJsonBtn.textContent = hidden ? "生JSON表示 ▾" : "生JSON表示 ▸";
});
