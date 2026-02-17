# Open WebUI (Fork) 🚀

![GitHub stars](https://img.shields.io/github/stars/thomelab-codes/forked-open-webui?style=social)
![GitHub forks](https://img.shields.io/github/forks/thomelab-codes/forked-open-webui?style=social)
![GitHub last commit](https://img.shields.io/github/last-commit/thomelab-codes/forked-open-webui?color=red)
![GitHub repo size](https://img.shields.io/github/repo-size/thomelab-codes/forked-open-webui)
![GitHub top language](https://img.shields.io/github/languages/top/thomelab-codes/forked-open-webui)

> A community fork of [Open WebUI](https://github.com/open-webui/open-webui) — an extensible, feature-rich, and user-friendly self-hosted AI platform designed to operate entirely offline.

![Open WebUI Banner](./banner.png)

This fork is maintained by [thomelab-codes](https://github.com/thomelab-codes) and is designed for **easy self-hosting with Docker Compose** directly from this repository. It supports **Ollama** and **OpenAI-compatible APIs**, with a built-in inference engine for RAG.

![Open WebUI Demo](./demo.png)

For upstream documentation, see the [Open WebUI Documentation](https://docs.openwebui.com/).

---

## Table of Contents

- [Quick Start with Docker Compose](#quick-start-with-docker-compose-)
- [Deployment Options](#deployment-options)
- [Configuration](#configuration)
- [Helper Script](#helper-script-run-composesh)
- [Alternative Installation Methods](#alternative-installation-methods)
- [Key Features](#key-features-)
- [Troubleshooting](#troubleshooting)
- [License](#license-)

---

## Quick Start with Docker Compose 🐳

The fastest way to deploy Open WebUI is with Docker Compose directly from this repository. This spins up both **Ollama** (the LLM backend) and **Open WebUI** (the frontend) in a single command.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) (v2+)
- Git

### Steps

1. **Clone the repository:**

   ```bash
   git clone https://github.com/thomelab-codes/forked-open-webui.git
   cd forked-open-webui
   ```

2. **(Optional) Configure environment variables:**

   ```bash
   cp .env.example .env
   # Edit .env to set API keys or other settings
   ```

3. **Start the stack:**

   ```bash
   docker compose up -d
   ```

   This builds the Open WebUI image from the included `Dockerfile` and pulls the Ollama image, then starts both services.

4. **Access the UI:**

   Open [http://localhost:3000](http://localhost:3000) in your browser.

5. **Stop the stack:**

   ```bash
   docker compose down
   ```

> [!WARNING]
> The `docker-compose.yaml` mounts a named volume (`open-webui`) for persistent data at `/app/backend/data`. Do not remove this volume unless you want to lose your data.

---

## Deployment Options

This repository includes several Docker Compose **overlay files** that extend the base `docker-compose.yaml`. Combine them to tailor the deployment to your environment.

### NVIDIA GPU Support

Enable GPU passthrough for Ollama to run models on your NVIDIA GPU:

```bash
docker compose -f docker-compose.yaml -f docker-compose.gpu.yaml up -d
```

The GPU overlay (`docker-compose.gpu.yaml`) configures NVIDIA device reservations. You can control the driver and GPU count via environment variables:

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_GPU_DRIVER` | `nvidia` | GPU driver to use |
| `OLLAMA_GPU_COUNT` | `1` | Number of GPUs (or `all`) |

> [!TIP]
> You must have the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) installed on your host.

### AMD GPU Support

For AMD GPUs (ROCm), use the AMD GPU overlay instead:

```bash
docker compose -f docker-compose.yaml -f docker-compose.amdgpu.yaml up -d
```

This passes through `/dev/kfd` and `/dev/dri` devices and uses the `ollama/ollama:rocm` image. Set `HSA_OVERRIDE_GFX_VERSION` if needed (defaults to `11.0.0`).

### Expose Ollama API

To make the Ollama API accessible outside the container stack (e.g., for external tools):

```bash
docker compose -f docker-compose.yaml -f docker-compose.api.yaml up -d
```

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_WEBAPI_PORT` | `11434` | Host port for the Ollama API |

### Bind-Mount Ollama Data

By default, Ollama model data is stored in a Docker volume. To use a host directory instead:

```bash
docker compose -f docker-compose.yaml -f docker-compose.data.yaml up -d
```

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_DATA_DIR` | `./ollama-data` | Host path for Ollama data |

### Playwright (Web Scraping)

Enable the Playwright container for web scraping support:

```bash
docker compose -f docker-compose.yaml -f docker-compose.playwright.yaml up -d
```

This starts a Playwright server and configures Open WebUI to use it as the web loader engine.

### OpenTelemetry (Observability)

For production monitoring with Grafana + OpenTelemetry:

```bash
docker compose -f docker-compose.otel.yaml up -d
```

> [!NOTE]
> The OpenTelemetry overlay is a standalone compose file (not an overlay on `docker-compose.yaml`). It runs Open WebUI on port `8088` with a Grafana LGTM stack.

### Combining Multiple Overlays

You can combine overlays freely. For example, GPU + API + host data:

```bash
docker compose \
  -f docker-compose.yaml \
  -f docker-compose.gpu.yaml \
  -f docker-compose.api.yaml \
  -f docker-compose.data.yaml \
  up -d
```

---

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and edit as needed:

```bash
cp .env.example .env
```

Key variables in `.env`:

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama backend URL (overridden to `http://ollama:11434` by `docker-compose.yaml`) |
| `OPENAI_API_BASE_URL` | *(empty)* | OpenAI-compatible API base URL |
| `OPENAI_API_KEY` | *(empty)* | API key for OpenAI-compatible services |
| `OPEN_WEBUI_PORT` | `3000` | Host port for the Open WebUI frontend |

Variables set in `docker-compose.yaml`:

| Variable | Default | Description |
|---|---|---|
| `WEBUI_DOCKER_TAG` | `main` | Docker image tag for Open WebUI |
| `OLLAMA_DOCKER_TAG` | `latest` | Docker image tag for Ollama |
| `WEBUI_SECRET_KEY` | *(empty)* | Secret key for session security |

### Makefile

A `Makefile` is included for convenience:

```bash
make install      # docker compose up -d
make start        # docker compose start
make stop         # docker compose stop
make startAndBuild # docker compose up -d --build
make remove       # Remove containers (with confirmation)
make update       # Pull latest changes, rebuild, and restart
```

---

## Helper Script: `run-compose.sh`

For interactive deployments, use the included `run-compose.sh` script. It auto-detects your GPU, lets you configure options via flags, and assembles the correct `docker compose` command.

```bash
./run-compose.sh [OPTIONS]
```

### Options

| Flag | Description |
|---|---|
| `--enable-gpu[count=COUNT]` | Enable GPU support (auto-detects driver). `COUNT` can be a number or `all`. |
| `--enable-api[port=PORT]` | Expose the Ollama API on the given port (default: `11435`). |
| `--webui[port=PORT]` | Set the Open WebUI port (default: `3000`). |
| `--data[folder=PATH]` | Bind-mount a host folder for Ollama data. |
| `--playwright` | Enable Playwright for web scraping. |
| `--build` | Build the Docker image before starting. |
| `--drop` | Tear down the compose project. |
| `-q, --quiet` | Run in headless mode (skip confirmation prompt). |

### Examples

```bash
# Basic start
./run-compose.sh

# GPU with 1 GPU, custom port, and host data folder
./run-compose.sh --enable-gpu[count=1] --webui[port=8080] --data[folder=./my-models]

# Headless GPU start with API exposed
./run-compose.sh --enable-gpu[count=all] --enable-api[port=11434] -q

# Tear down
./run-compose.sh --drop
```

---

## Alternative Installation Methods

### Docker (Single Container)

If you prefer a single `docker run` command without Compose:

```bash
# With Ollama on the same machine
docker run -d -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui --restart always \
  ghcr.io/open-webui/open-webui:main

# OpenAI API only
docker run -d -p 3000:8080 \
  -e OPENAI_API_KEY=your_secret_key \
  -v open-webui:/app/backend/data \
  --name open-webui --restart always \
  ghcr.io/open-webui/open-webui:main
```

### Python pip

```bash
pip install open-webui
open-webui serve
# Access at http://localhost:8080
```

### Kubernetes

Open WebUI can also be deployed via kubectl, Kustomize, or Helm. See the [upstream documentation](https://docs.openwebui.com/getting-started/).

---

## Key Features ⭐

- 🤝 **Ollama/OpenAI API Integration** — Connect to Ollama, LMStudio, GroqCloud, Mistral, OpenRouter, and more.
- 🛡️ **Granular Permissions & User Groups** — Role-based access control with detailed user roles.
- 📱 **Responsive Design & PWA** — Works across desktop and mobile with offline support.
- ✒️🔢 **Markdown & LaTeX** — Full rendering support for rich content.
- 🎤📹 **Voice/Video Calls** — Hands-free with Whisper, OpenAI, Deepgram, Azure STT/TTS.
- 🛠️ **Model Builder** — Create and customize Ollama models from the UI.
- 🐍 **Python Function Calling** — Extend LLMs with custom Python functions.
- 📚 **RAG (Retrieval Augmented Generation)** — 9 vector database options, multiple content extractors.
- 🔍 **Web Search for RAG** — 15+ search providers for live web results.
- 🎨 **Image Generation** — DALL-E, Gemini, ComfyUI, AUTOMATIC1111 integration.
- 🔐 **Enterprise Auth** — LDAP, SCIM 2.0, SSO, OAuth.
- 📊 **OpenTelemetry Observability** — Traces, metrics, and logs.
- ⚖️ **Horizontal Scalability** — Redis-backed sessions for multi-node deployments.
- 🌐🌍 **Multilingual** — Internationalization (i18n) support.
- 🧩 **Pipelines & Plugins** — Extend with the [Pipelines Plugin Framework](https://github.com/open-webui/pipelines).

For a full feature list, see the [upstream documentation](https://docs.openwebui.com/features).

---

## Troubleshooting

### Server Connection Error

If the Open WebUI container cannot reach Ollama at `host.docker.internal:11434`, try using `--network=host`:

```bash
docker run -d --network=host \
  -v open-webui:/app/backend/data \
  -e OLLAMA_BASE_URL=http://127.0.0.1:11434 \
  --name open-webui --restart always \
  ghcr.io/open-webui/open-webui:main
```

> [!NOTE]
> With `--network=host`, the UI is accessible at port `8080` instead of `3000`.

When using Docker Compose, the Ollama container is on the same Docker network and is accessed via service name (`http://ollama:11434`), so this issue typically does not apply.

### Offline Mode

Set `HF_HUB_OFFLINE=1` to prevent Hugging Face model downloads:

```bash
export HF_HUB_OFFLINE=1
```

For more help, see the [upstream troubleshooting guide](https://docs.openwebui.com/troubleshooting/) or the [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) file.

---

## License 📜

This project contains code under multiple licenses. The current codebase includes components licensed under the Open WebUI License with an additional requirement to preserve the "Open WebUI" branding, as well as prior contributions under their respective original licenses. For a detailed record of license changes and the applicable terms for each section of the code, please refer to [LICENSE_HISTORY](./LICENSE_HISTORY). For complete and updated licensing details, please see the [LICENSE](./LICENSE) and [LICENSE_HISTORY](./LICENSE_HISTORY) files.

## Support 💬

If you have any questions, suggestions, or need assistance, please [open an issue](https://github.com/thomelab-codes/forked-open-webui/issues) in this repository.

For upstream community support, join the [Open WebUI Discord](https://discord.gg/5rJgQTnV4s).

---

> Originally created by [Timothy Jaeryang Baek](https://github.com/tjbck). Fork maintained by [thomelab-codes](https://github.com/thomelab-codes).
