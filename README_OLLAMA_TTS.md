## Ollama + TTS Chat

**Prerequisites on Ubuntu:**

- Install system packages:

```bash
sudo apt update
sudo apt install -y curl python3 python3-venv python3-pip espeak ffmpeg
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

