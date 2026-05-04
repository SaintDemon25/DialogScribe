# DialogScribe

Self-hosted audio & video transcription service with speaker diarization, LLM-powered analysis, and a modern web UI.

Built on [GigaAM](https://github.com/salute-developers/GigaAM) for Russian speech recognition, [pyannote](https://huggingface.co/pyannote/speaker-diarization-3.1) for speaker diarization, and [Mistral Voxtral](https://mistral.ai) as an alternative ASR backend.

## Features

- **Transcription** — audio & video files up to 1 GB, powered by GigaAM or Voxtral API
- **Speaker diarization** — identify who spoke and when, via pyannote 3.1
- **LLM analysis** — automatic summaries, mind maps, and key insights via OpenAI-compatible API
- **Saved transcriptions** — library with search, edit, and public sharing links
- **Templates** — reusable prompt templates for analysis with import/export
- **Autoflow** — end-to-end pipeline: upload → transcribe → analyze in one step
- **Multi-user** — registration, login, admin panel, usage tracking
- **Export** — TXT, JSON, SRT, VTT, DOCX, PDF
- **REST API** — OpenAI `/v1/audio/transcriptions`-compatible endpoint
- **Denoise** — optional audio pre-processing for noisy recordings

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   SvelteKit SPA │────▶│   FastAPI backend │────▶│     GigaAM      │
│   (frontend)    │     │   (api.py)        │     │   / Voxtral     │
└─────────────────┘     ├──────────────────┤     └─────────────────┘
                        │ PostgreSQL/SQLite│     ┌─────────────────┐
                        │ (alembic migrations)│   │    pyannote     │
                        ├──────────────────┤     │  diarization    │
                        │ LLM (OpenAI-compat)│───▶│  (GPU required) │
                        └──────────────────┘     └─────────────────┘
```

**Tech stack:**
- **Backend:** Python 3.10+, FastAPI, SQLAlchemy (async), Alembic, uvicorn
- **Frontend:** SvelteKit 5, TypeScript, Vite
- **ML:** GigaAM, pyannote-audio 3.1, torch 2.8
- **Infrastructure:** Docker, NVIDIA GPU runtime, HashiCorp Vault (secrets)

## Quick Start

### Prerequisites

- NVIDIA GPU with CUDA (required for GigaAM + pyannote)
- [Docker](https://docs.docker.com/get-docker/) with [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
- [HuggingFace token](https://huggingface.co/settings/tokens) with access to:
  - [pyannote/segmentation-3.0](https://huggingface.co/pyannote/segmentation-3.0)
  - [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)

### Configuration

```bash
# Clone the repository
git clone https://github.com/Timik232/DialogScribe.git
cd DialogScribe

# Create environment file from template
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Required: HuggingFace token for diarization models
HF_TOKEN=hf_your_token_here

# Required: Admin credentials (created on first startup)
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=your-secure-password

# Required: Database URL
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dialogscribe

# Optional: LLM for analysis (OpenAI-compatible endpoint)
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4.1
LLM_API_KEY=sk-your-key-here

# Optional: Mistral Voxtral for alternative ASR
MISTRAL_API_KEY=your_mistral_key_here
```

### Run with Docker

```bash
# Build and start
docker compose build
docker compose up -d
```

The service will be available at **http://localhost:7860**.

First startup downloads GigaAM and pyannote models (~5-10 min depending on connection). Subsequent starts are near-instant.

### Run without Docker

```bash
# Install system dependencies
# - FFmpeg (apt install ffmpeg / brew install ffmpeg)
# - Python 3.10+

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install GigaAM
git clone https://github.com/salute-developers/GigaAM.git
pip install -e ./GigaAM

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-diarization.txt

# Run database migrations
alembic upgrade head

# Start the server
python api.py
```

## API Endpoints

### Transcription

```bash
# OpenAI-compatible endpoint
curl -X POST http://localhost:7860/v1/audio/transcriptions \
  -F "file=@meeting.mp4" \
  -F "model=whisper-1" \
  -F "response_format=json"
```

### Full Transcription with Diarization

```bash
curl -X POST http://localhost:7860/api/transcribe \
  -H "Authorization: Bearer <token>" \
  -F "file=@meeting.mp4" \
  -F "diarization=pyannote" \
  -F "num_speakers=3"
```

### Analysis

```bash
# Generate summary + mind map + insights
curl -X POST http://localhost:7860/api/analysis/analyze \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"transcription_id": 42, "template_id": 1}'
```

### Key Routes

| Route | Description |
|-------|-------------|
| `POST /v1/audio/transcriptions` | OpenAI-compatible transcription |
| `POST /api/transcribe` | Full transcription with diarization options |
| `POST /api/autoflow` | Upload → transcribe → analyze pipeline |
| `POST /api/analysis/analyze` | LLM summary, mind map, insights |
| `GET /api/exports/{id}/{format}` | Export as TXT/JSON/SRT/VTT/DOCX/PDF |
| `POST /api/auth/login` | Session-based authentication |
| `GET /api/templates` | Analysis template management |
| `GET /api/saved-transcriptions` | Saved transcriptions library |

## Web UI

The SvelteKit SPA provides:

- **Transcribe** — upload files, configure diarization, download results
- **Transcriptions** — saved library with search, edit, share
- **Analysis** — LLM-generated summaries, interactive mind maps, key insights
- **Autoflow** — one-click pipeline from upload to analysis
- **Templates** — manage analysis prompt templates
- **Admin** — user management, usage stats (admin only)
- **Auth** — registration, login, password reset via email

## Project Structure

```
DialogScribe/
├── api.py                          # FastAPI application entry point
├── Dockerfile                      # Multi-stage build (frontend + backend)
├── docker-compose.yaml             # Production deployment config
├── entrypoint.sh                   # Vault secrets loader + DB migration
├── requirements.txt                # Python dependencies
├── alembic/                        # Database migrations
├── frontend/                       # SvelteKit SPA
│   ├── src/routes/                 # Page components
│   └── static/                     # Static assets
├── gigaam_transcriber/             # Core transcription library
│   ├── transcriber.py              # GigaAM wrapper
│   ├── audio_processor.py          # Audio/video preprocessing + denoise
│   ├── diarization.py              # pyannote speaker diarization
│   ├── summarizer.py               # LLM analysis (summary, insights)
│   ├── mindmap.py                  # Interactive mind map generation
│   ├── auth.py                     # User auth (bcrypt, JWT sessions)
│   ├── database.py                 # SQLAlchemy async setup
│   ├── models.py                   # ORM models
│   ├── exporters.py                # DOCX/PDF export
│   ├── template_manager.py         # Analysis prompt templates
│   ├── cli.py                      # CLI interface
│   └── ...
├── routers/                        # FastAPI route handlers
│   ├── auth.py                     # Login, register, password reset
│   ├── transcription.py            # Transcription endpoints
│   ├── analysis.py                 # LLM analysis endpoints
│   ├── autoflow.py                 # End-to-end pipeline
│   ├── exports.py                  # File export endpoints
│   ├── templates.py                # Template CRUD
│   ├── admin.py                    # Admin panel endpoints
│   └── ...
├── tests/                          # Test suite
└── .env.example                    # Configuration template
```

## Configuration Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `HF_TOKEN` | — | HuggingFace token (required for diarization) |
| `MISTRAL_API_KEY` | — | Mistral API key (for Voxtral ASR) |
| `ADMIN_EMAIL` | — | Admin email (created on first start) |
| `ADMIN_PASSWORD` | — | Admin password |
| `DATABASE_URL` | — | PostgreSQL or SQLite connection string |
| `LLM_BASE_URL` | `https://api.openai.com/v1` | OpenAI-compatible API endpoint |
| `LLM_MODEL` | `gpt-4.1` | Model for summaries and analysis |
| `LLM_API_KEY` | — | API key for LLM endpoint |
| `MAX_UPLOAD_SIZE_MB` | `1024` | Maximum upload file size |
| `SMTP_HOST` | — | SMTP server for password reset emails |
| `SMTP_PORT` | `465` | SMTP port |
| `SMTP_USER` | — | SMTP username |
| `SMTP_PASSWORD` | — | SMTP password |

## Testing

```bash
# Run all tests
pytest tests/ -v

# Fast tests (no GPU, no model downloads)
pytest tests/ -v -m "not requires_gpu"
```

## License

MIT

## Acknowledgements

- [GigaAM](https://github.com/salute-developers/GigaAM) — Russian speech recognition model
- [pyannote-audio](https://github.com/pyannote/pyannote-audio) — Speaker diarization
- [Mistral Voxtral](https://mistral.ai) — Alternative ASR backend
