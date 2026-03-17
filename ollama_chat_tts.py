import sys
import json
import requests
import pyttsx3

OLLAMA_HOST = "http://localhost:11434"
MODEL_NAME = "llama3"  # or "mistral", or any other pulled model


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


def speak_text(text: str) -> None:
    """
    Use pyttsx3 (offline TTS) to speak the text aloud.
    If initialization or voice selection fails, fall back to text only.
    """
    if not text:
        return

    try:
        engine = pyttsx3.init()

        # Try to pick a known-good voice on Linux, otherwise keep default
        try:
            voices = engine.getProperty("voices") or []
            # Prefer an English voice if available
            en_voice = next((v for v in voices if "en" in (v.languages or [b""]) or "english" in (v.name or "").lower()), None)
            if en_voice is not None:
                engine.setProperty("voice", en_voice.id)
        except Exception:
            # Voice selection failed; continue with whatever default works
            pass

        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        # TTS failed; just log to stderr and continue
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

