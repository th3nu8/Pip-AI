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
    """
    if not text:
        return

    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()


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

