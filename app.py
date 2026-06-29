"""
context-checker — Slack mesajlari eksik alan denetcisi
"""

from __future__ import annotations

import json
import logging
import os
import subprocess

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("context-checker")

# .env'de virgülle ayrılmış bir veya birden fazla kanal ID'si olabilir.
# Bot yalnızca bu kanallarda davranır (yanlış bir kanala eklense bile susar).
QA_CHANNEL_IDS = {
    c.strip() for c in os.environ["QA_CHANNEL_ID"].split(",") if c.strip()
}
# launchd altında PATH minimaldir; `which claude` çıktısını CLAUDE_BIN'e koy.
CLAUDE_BIN = os.environ.get("CLAUDE_BIN", "claude")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-haiku-4-5-20251001")
CLAUDE_TIMEOUT = int(os.environ.get("CLAUDE_TIMEOUT", "60"))

app = App(token=os.environ["SLACK_BOT_TOKEN"])

# Aynı mesaja iki kez yanıt vermemek için (süreç ömrü boyunca) basit bir kayıt.
_replied: set[str] = set()

# Sistem promptu kolay düzenlenebilsin diye ayrı bir dosyada tutulur.
_PROMPT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "system_prompt.md"
)
with open(_PROMPT_PATH, encoding="utf-8") as _f:
    SYSTEM_PROMPT = _f.read()


def _extract_json(text: str) -> dict:
    """Modelin metin yanıtından JSON nesnesini çıkar (kod bloğu olsa bile)."""
    s = text.strip()
    if s.startswith("```"):
        s = s.strip("`")
        if s[:4].lower() == "json":
            s = s[4:]
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        i, j = s.find("{"), s.rfind("}")
        if i != -1 and j != -1 and j > i:
            return json.loads(s[i : j + 1])
        raise


# Alt-süreç SAF bir sınıflandırıcı olmalı: hiçbir MCP sunucusu (Slack dahil) ve
# hiçbir dahili araç çalıştıramasın. Aksi halde agentic `claude`, gelen mesajı
# bir "görev" sanıp Slack MCP ile kanala kendi mesajını atabilir (thread'siz) ya
# da kullanıcı metnindeki prompt-injection ile araç çalıştırabilir.
_DISALLOWED_TOOLS = [
    "Bash", "Edit", "Write", "Read", "Glob", "Grep",
    "WebFetch", "WebSearch", "Task", "NotebookEdit",
]


def assess(text: str) -> dict | None:
    """Mesaji `claude` CLI üzerinden değerlendir; sonuç dict'ini döndür."""
    proc = subprocess.run(
        [
            CLAUDE_BIN,
            "--print",
            "--output-format", "json",
            "--model", CLAUDE_MODEL,
            "--strict-mcp-config",            # hiçbir MCP sunucusu yükleme
            "--system-prompt", SYSTEM_PROMPT,
            # variadic; arg yutmamak için EN SONDA dursun:
            "--disallowed-tools", *_DISALLOWED_TOOLS,
        ],
        input=text,                           # kullanıcı metni stdin'den (arg yutma/injection yok)
        capture_output=True,
        text=True,
        timeout=CLAUDE_TIMEOUT,
    )
    if proc.returncode != 0:
        logger.error("claude CLI hata kodu %s: %s", proc.returncode, proc.stderr.strip())
        return None

    # --output-format json: stdout bir zarf nesnesidir; asıl metin "result"ta.
    envelope = json.loads(proc.stdout)
    if envelope.get("is_error"):
        logger.error("claude sonucu hata: %s", envelope.get("result"))
        return None
    return _extract_json(envelope["result"])


@app.event("message")
def handle_message(event, client):
    # Sadece izlenen kanal(lar).
    channel = event.get("channel")
    if channel not in QA_CHANNEL_IDS:
        return
    # Botları (kendimiz dahil) ve düzenleme/katılma gibi alt-tipleri ele.
    # Ekli dosyalı normal mesajlara izin ver (file_share).
    if event.get("bot_id"):
        return
    if event.get("subtype") not in (None, "file_share"):
        return
    # Yalnızca üst-seviye mesajlar; thread yanıtlarına dokunma.
    if event.get("thread_ts"):
        return

    text = (event.get("text") or "").strip()
    if not text:
        return

    ts = event["ts"]
    if ts in _replied:
        return

    try:
        result = assess(text)
    except Exception:
        logger.exception("Değerlendirme başarısız (ts=%s)", ts)
        return

    if not result or not result.get("is_bug_report"):
        return

    missing = result.get("missing") or []
    if not missing:
        return  # rapor tam; sessiz kal.

    question = (result.get("question") or "").strip()
    if not question:
        return

    user = event.get("user")
    mention = f"<@{user}> " if user else ""
    client.chat_postMessage(
        channel=channel,
        thread_ts=ts,
        text=f"{mention}{question}",
    )
    _replied.add(ts)
    logger.info("Eksik alan soruldu %s (ts=%s)", missing, ts)


if __name__ == "__main__":
    logger.info(
        "context-checker başlıyor (Socket Mode, motor=claude CLI) — izlenen kanal: %d",
        len(QA_CHANNEL_IDS),
    )
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
