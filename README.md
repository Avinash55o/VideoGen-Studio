<div align="center">
  <img src=".github/assets/icon-dark.webp" alt="VideoGen Studio" width="120" height="120" />
</div>

<h1 align="center">VideoGen Studio</h1>

<p align="center">
  <strong>Local-first AI video generation studio</strong>
</p>

<p align="center">
  <a href="https://github.com/Avinash55o/VideoGen-Studio/releases">
    <img src="https://img.shields.io/github/downloads/Avinash55o/VideoGen-Studio/total?style=flat&color=blue" alt="Downloads" />
  </a>
  <a href="https://github.com/Avinash55o/VideoGen-Studio/releases/latest">
    <img src="https://img.shields.io/github/v/release/Avinash55o/VideoGen-Studio?style=flat" alt="Release" />
  </a>
  <a href="https://github.com/Avinash55o/VideoGen-Studio/stargazers">
    <img src="https://img.shields.io/github/stars/Avinash55o/VideoGen-Studio?style=flat" alt="Stars" />
  </a>
  <a href="https://github.com/Avinash55o/VideoGen-Studio/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/Avinash55o/VideoGen-Studio?style=flat" alt="License" />
  </a>
</p>

<p align="center">
  <a href="https://github.com/Avinash55o/VideoGen-Studio">GitHub</a>
</p>

---

## What is VideoGen Studio?

A **local-first AI video generation studio** — generate and edit videos on your machine using open-weight models. No cloud, no API keys, no per-generation fees.

### Features

- **Text-to-Video & Image-to-Video** — CogVideoX 5B, Wan2.1 T2V 1.3B, and more
- **Voiceover generation** — reuse TTS engines for narration with Whisper STT for auto-subtitles
- **Render pipeline** — compose clips, voiceover, and subtitles into final video export
- **Fully local** — everything runs on your machine

### Quick Start

```bash
git clone https://github.com/Avinash55o/VideoGen-Studio.git
cd VideoGen-Studio
just setup
just dev
```

### Project Structure

```
videogen-studio/
├── backend/          # FastAPI server (Python)
│   ├── routes/       # API endpoints
│   ├── services/     # TTS, STT, render, voiceover
│   ├── database/     # SQLite ORM models
│   └── backends/     # Model engine registry
├── app/              # React frontend (Vite + Bun)
│   └── src/          # UI components, pages, hooks
└── web/              # Web app (alternative frontend)
```

### License

MIT
