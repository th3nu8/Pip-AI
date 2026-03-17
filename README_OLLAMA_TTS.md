## Ollama + TTS Chat

**Prerequisites on Ubuntu:**

- Install system packages:

```bash
sudo apt update
sudo apt install -y curl python3 python3-venv python3-pip ffmpeg
```

- Install Ollama:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

- Start the Ollama server:

```bash
ollama serve
```

- Pull a model that fits your 8 GB machine (examples):

```bash
ollama pull llama3
# or
ollama pull mistral
```

**Install Piper (offline TTS):**

Option A (recommended on Ubuntu): install via Snap

```bash
sudo snap install piper-tts --edge
```

Option B: install via pip (inside the venv below)

```bash
pip install piper-tts
```

**Python setup (inside this repo):**

```bash
cd Pip-AI
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Run the chat with TTS:**

```bash
python3 ollama_chat_tts.py
```

Type your questions; the response will be printed and spoken aloud.

## VPS note (Ubuntu 24.04)

Most VPS machines have **no audio device**, so playback will fail even if TTS works.

To generate WAV files you can download, run with:

```bash
TTS_MODE=wav python3 ollama_chat_tts.py
```

WAV files will be written to `./tts_out/` (timestamped).

