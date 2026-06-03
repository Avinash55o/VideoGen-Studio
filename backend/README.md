# VideoGen Studio Backend

FastAPI server powering VideoGen Studio.

## Stack

- **FastAPI** with async routes
- **SQLite** via SQLModel/SQLAlchemy ORM
- **TTS engines** — Qwen3-TTS, Kokoro, Chatterbox, and more
- **STT** — Whisper-based transcription
- **Video models** — CogVideoX, Wan2.1

## Project Layout

```
backend/
├── routes/          # FastAPI route handlers
├── services/        # Business logic (TTS, STT, render, voiceover)
├── database/        # ORM models and session management
├── backends/        # Model engine registry and configs
├── mcp_server/      # MCP protocol server
├── tests/           # Test suite
└── venv/            # Python virtual environment
```

## Development

```bash
# Start the server
venv/bin/uvicorn backend.main:app --port 17493

# Run tests
venv/bin/pytest
```

## Data files

```
data/
├── videogen.db      # SQLite database
└── media/           # Audio/video storage
```
