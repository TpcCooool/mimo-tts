# MiMo TTS

> A web-based Text-to-Speech tool powered by Xiaomi MiMo TTS V2.5 API

English | [中文](./README.md)

A lightweight web TTS application built with Xiaomi's MiMo TTS V2.5 API. Supports Chinese & English speech synthesis, voice design, and voice cloning. Features a bold Neo-Brutalism UI design.

## Features

- **Speech Synthesis** — Convert Chinese and English text to natural speech
- **Built-in Voices** — 9 preset voices: 冰糖, 茉莉, 苏打, 白桦, Mia, Chloe, Milo, Dean, and more
- **Voice Design** — Describe your desired voice in natural language, and AI generates it (e.g. "a warm young female voice, slow pace, whispering")
- **Voice Clone** — Upload audio or video samples to clone a voice for synthesis
- **Director Mode** — Control speaking style via natural language instructions (e.g. "read in an enthusiastic TV host tone")
- **Audio Tags** — Insert tags like `(叹气)` (sigh), `(笑)` (laugh), `(唱歌)` (sing) in text for expressive effects
- **Download** — Export as WAV or MP3 (client-side conversion)

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Vue 3 (Composition API) |
| Build Tool | Vite 8 |
| Backend | Vercel Serverless Functions |
| Styling | Vanilla CSS (Neo-Brutalism) |
| Audio Processing | lamejs (WAV → MP3) |
| Deployment | Vercel |

## Quick Start

### Prerequisites

- Node.js 18+
- MiMo API Key (get one at [MiMo Platform](https://platform.xiaomimimo.com/#/console/api-keys))

### Install & Run

```bash
# Clone the project
git clone https://github.com/your-username/mimo-tts.git
cd mimo-tts

# Install dependencies
npm install

# Configure environment variables
cp .env.example .env
# Edit .env and fill in your API key

# Start development server
npm run dev
```

### Environment Variables

Configure in `.env`:

```env
MIMO_API_KEY=your_api_key_here
MIMO_API_BASE_URL=https://api.xiaomimimo.com/v1
```

### Deploy to Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

Add the `MIMO_API_KEY` environment variable in your Vercel project settings.

## Project Structure

```
mimo-tts/
├── api/                  # Vercel Serverless Functions
│   ├── tts.js            # TTS API proxy
│   └── health.js         # Health check endpoint
├── src/
│   ├── App.vue           # Main application component
│   ├── main.js           # Entry point
│   └── style.css         # Global styles
├── public/               # Static assets
├── index.html            # HTML entry
├── vite.config.js        # Vite configuration
└── vercel.json           # Vercel deployment config
```

## License

[MIT License](./LICENSE)
