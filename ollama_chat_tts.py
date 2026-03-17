import sys
import json
import os
import shutil
import subprocess
import tempfile
import datetime
import requests

OLLAMA_HOST = "http://localhost:11434"
MODEL_NAME = "llama3"  # or "mistral", or any other pulled model

# Piper voice (small-ish, good default). Downloaded automatically on first run.
PIPER_VOICE_BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium"
PIPER_VOICE_NAME = "en_US-amy-medium"
VOICE_DIR = os.path.join(os.path.dirname(__file__), "voices")
PIPER_MODEL_PATH = os.path.join(VOICE_DIR, f"{PIPER_VOICE_NAME}.onnx")
PIPER_JSON_PATH = os.path.join(VOICE_DIR, f"{PIPER_VOICE_NAME}.onnx.json")

# TTS_MODE:
# - "auto" (default): try to play audio if possible, else save WAV
# - "play": force playback (may fail on VPS)
# - "wav": always save WAV files under ./tts_out/
TTS_MODE = os.environ.get("TTS_MODE", "auto").strip().lower() or "auto"
TTS_OUT_DIR = os.path.join(os.path.dirname(__file__), "tts_out")


def ask_ollama(prompt: str) -> str:
    """
    Send a chat request to the local Ollama server and return the full response text.
    """
    url = f"{OLLAMA_HOST}/api/chat"
    headers = {"Content-Type": "application/json"}

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": prompt},
        ],
        "stream": True,
    }

    try:
        with requests.post(url, headers=headers, data=json.dumps(payload), stream=True) as resp:
            resp.raise_for_status()
            full_text = []

            for line in resp.iter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line.decode("utf-8"))
                except json.JSONDecodeError:
                    continue

                delta = data.get("message", {}).get("content")
                if delta:
                    full_text.append(delta)
                    sys.stdout.write(delta)
                    sys.stdout.flush()

                if data.get("done"):
                    break

            print()
            return "".join(full_text).strip()

    except requests.RequestException as e:
        print(f"Error talking to Ollama: {e}", file=sys.stderr)
        return ""


def _download_file(url: str, dest_path: str) -> None:
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)


def ensure_piper_voice() -> None:
    if os.path.exists(PIPER_MODEL_PATH) and os.path.exists(PIPER_JSON_PATH):
        return

    print("\n[Downloading Piper voice model...]", file=sys.stderr)
    model_url = f"{PIPER_VOICE_BASE}/{PIPER_VOICE_NAME}.onnx?download=true"
    json_url = f"{PIPER_VOICE_BASE}/{PIPER_VOICE_NAME}.onnx.json?download=true"
    _download_file(model_url, PIPER_MODEL_PATH)
    _download_file(json_url, PIPER_JSON_PATH)


def _play_wav(path: str) -> None:
    # Prefer ffplay (from ffmpeg), else fall back to aplay/paplay if present.
    if shutil.which("ffplay"):
        subprocess.run(
            ["ffplay", "-autoexit", "-nodisp", "-loglevel", "error", path],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return
    if shutil.which("aplay"):
        subprocess.run(["aplay", "-q", path], check=False)
        return
    if shutil.which("paplay"):
        subprocess.run(["paplay", path], check=False)
        return

    print("\n[TTS warning: no audio player found (ffplay/aplay/paplay)]", file=sys.stderr)


def _save_wav(src_path: str) -> str:
    os.makedirs(TTS_OUT_DIR, exist_ok=True)
    ts = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(TTS_OUT_DIR, f"tts_{ts}.wav")
    shutil.copyfile(src_path, dest)
    return dest


def speak_text(text: str) -> None:
    """
    Offline TTS via Piper. If Piper isn't available, fall back to text-only.
    """
    if not text:
        return

    piper_bin = shutil.which("piper")
    if not piper_bin:
        print("\n[TTS warning: 'piper' not found; continuing without speech]", file=sys.stderr)
        return

    try:
        ensure_piper_voice()
        with tempfile.TemporaryDirectory() as tmpdir:
            wav_path = os.path.join(tmpdir, "out.wav")
            proc = subprocess.run(
                [piper_bin, "-m", PIPER_MODEL_PATH, "--output_file", wav_path],
                input=text,
                text=True,
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            if proc.returncode != 0:
                err = (proc.stderr or "").strip()
                print(f"\n[TTS error: piper failed ({proc.returncode}): {err}]", file=sys.stderr)
                return
            if TTS_MODE == "wav":
                saved = _save_wav(wav_path)
                print(f"\n[TTS] Wrote {saved}", file=sys.stderr)
                return

            if TTS_MODE == "play":
                _play_wav(wav_path)
                return

            # auto: try playback; if no player available, save instead
            if shutil.which("ffplay") or shutil.which("aplay") or shutil.which("paplay"):
                _play_wav(wav_path)
            else:
                saved = _save_wav(wav_path)
                print(f"\n[TTS] No audio device/player detected; wrote {saved}", file=sys.stderr)
    except Exception as e:
        print(f"\n[TTS error: {e}; continuing without speech]", file=sys.stderr)


def main() -> None:
    print(f"Using model: {MODEL_NAME}")
    print("Type your question, or 'exit' to quit.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye.")
            break

        if not user_input:
            continue

        print("AI: ", end="", flush=True)
        answer = ask_ollama(user_input)
        speak_text(answer)


if __name__ == "__main__":
    main()

