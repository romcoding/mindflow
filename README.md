# Rovot / MindFlow — AI-Powered Personal Productivity Platform

A comprehensive full-stack application for managing tasks, stakeholders, and notes with AI assistance, multi-channel messaging, and flexible LLM provider support. Runs as a desktop app (.dmg/.exe), a local server, or a cloud deployment.

---

## Features

### Core Productivity
- **Intelligent Content Categorisation**: AI automatically analyses input to determine if it is a task, note, or stakeholder information
- **Voice Input Integration**: Web Speech API with real-time transcription
- **Task Management**: Priority-based task organisation with smart due date extraction and Kanban board
- **Stakeholder Mapping**: Interactive relationship management with influence/interest matrix
- **Notes**: Rich note-taking with categories and search

### AI Assistant
- **OpenAI API** (GPT-4o, GPT-4, GPT-3.5-turbo) — cloud-hosted
- **LM Studio** — connect to any local model running on your machine
- **Ollama** — run open-source models locally
- **Custom endpoints** — any OpenAI-compatible API
- **Tool calling** — the AI can create tasks, notes, and contacts on your behalf
- **Switchable at runtime** — change provider from the Settings page without restarting

### Messaging Channels
- **Telegram Bot** — existing integration, fully functional
- **WhatsApp Business** — via Meta Cloud API with webhook signature verification
- **Signal Messenger** — via signal-cli REST API bridge
- **Unified architecture** — all channels share the same message processing pipeline

### Background Services
- **File Watcher** — monitors local directories for changes and creates notes automatically (desktop mode)
- **Email Checker** — connects to any IMAP inbox (Gmail, Outlook, Yahoo, etc.) and creates tasks/notes based on configurable rules

### Security
- JWT authentication with bcrypt password hashing
- OAuth 2.0 (Google, GitHub)
- Fernet (AES-128-CBC) encryption for stored credentials
- Security headers, CORS, rate limiting, HSTS
- Non-root Docker containers
- See [SECURITY.md](./SECURITY.md) for the full policy and production checklist

---

## Architecture

```
mindflow/
├── mindflow-backend/              # Flask API server
│   ├── src/
│   │   ├── main.py               # Application entry point
│   │   ├── security.py           # Security middleware
│   │   ├── crypto.py             # Credential encryption
│   │   ├── extensions.py         # Flask extensions
│   │   ├── models/               # SQLAlchemy models
│   │   ├── routes/               # API endpoints
│   │   │   ├── auth.py           # Authentication
│   │   │   ├── ai_assistant.py   # AI chat with tool calling
│   │   │   ├── llm_settings.py   # LLM provider management
│   │   │   ├── messaging.py      # WhatsApp / Signal webhooks
│   │   │   ├── services.py       # File watcher & email checker API
│   │   │   ├── telegram_bot.py   # Telegram bot
│   │   │   └── ...               # Tasks, notes, stakeholders, etc.
│   │   ├── llm/                  # LLM provider abstraction
│   │   │   ├── provider.py       # Abstract base class
│   │   │   ├── openai_provider.py# OpenAI-compatible implementation
│   │   │   └── factory.py        # Provider factory
│   │   ├── channels/             # Messaging channel abstraction
│   │   │   ├── channel.py        # Abstract base class
│   │   │   ├── whatsapp_channel.py
│   │   │   └── signal_channel.py
│   │   └── services/             # Background services
│   │       ├── file_watcher.py
│   │       └── email_checker.py
│   ├── Dockerfile                # Production Docker image
│   └── requirements.txt
├── mindflow-frontend/             # React 19 + Vite + Tailwind
│   ├── src/
│   │   ├── components/           # UI components (shadcn/ui)
│   │   ├── hooks/                # Custom React hooks
│   │   ├── lib/                  # API client, utilities
│   │   └── App.jsx               # Main application
│   ├── Dockerfile                # Nginx-based production image
│   ├── nginx.conf                # SPA routing + security headers
│   └── vercel.json               # Vercel deployment config
├── docker-compose.yml             # Full-stack local/production
├── docker-compose.prod.yml        # Production overrides
├── render.yaml                    # Render.com blueprint
├── .env.example                   # All configuration options
├── SECURITY.md                    # Security policy & checklist
└── README.md
```

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+ with pnpm
- PostgreSQL (production) or SQLite (development)

### 1. Clone and configure

```bash
git clone https://github.com/romcoding/mindflow.git
cd mindflow
cp .env.example .env
# Edit .env with your values (at minimum: JWT_SECRET_KEY, OPENAI_API_KEY)
```

### 2. Backend

```bash
cd mindflow-backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
```

### 3. Frontend

```bash
cd mindflow-frontend
pnpm install
pnpm run dev
```

The app is now running at `http://localhost:5173` (frontend) and `http://localhost:5000` (API).

---

## LLM Provider Configuration

Rovot supports multiple LLM backends through a unified provider interface. Switch providers without changing any application code.

| Provider | `LLM_PROVIDER` | Required Variables | Notes |
|----------|----------------|-------------------|-------|
| OpenAI | `openai` | `OPENAI_API_KEY` | Default. Uses GPT-4o. |
| LM Studio | `lmstudio` | — | Connects to `localhost:1234` |
| Ollama | `ollama` | — | Connects to `localhost:11434` |
| Custom | `custom` | `LLM_CUSTOM_BASE_URL`, `LLM_CUSTOM_API_KEY` | Any OpenAI-compatible API |

### Using LM Studio (local LLM)

1. Download and install [LM Studio](https://lmstudio.ai/)
2. Load a model and start the local server (default port 1234)
3. Set environment variables:

```bash
LLM_PROVIDER=lmstudio
# LM Studio uses the OpenAI-compatible API, no API key needed
```

### Using Ollama

```bash
ollama serve                    # Start Ollama
ollama pull llama3              # Download a model
LLM_PROVIDER=ollama LLM_MODEL=llama3 python src/main.py
```

### Runtime switching

Use the Settings page in the UI, or call the API directly:

```bash
curl -X POST http://localhost:5000/api/llm/settings \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"provider": "lmstudio", "base_url": "http://localhost:1234/v1"}'
```

---

## Messaging Channels

### Telegram (existing)

Set `TELEGRAM_BOT_TOKEN` in your environment. See the existing Telegram documentation.

### WhatsApp Business

1. Create a Meta Business App at [developers.facebook.com](https://developers.facebook.com)
2. Add the WhatsApp product and get a permanent access token
3. Configure environment variables:

```bash
WHATSAPP_PHONE_NUMBER_ID=your-phone-number-id
WHATSAPP_ACCESS_TOKEN=your-access-token
WHATSAPP_VERIFY_TOKEN=your-custom-verify-token
WHATSAPP_APP_SECRET=your-app-secret   # For webhook signature verification
```

4. Set the webhook URL to: `https://your-backend.com/api/messaging/webhook/whatsapp`
5. Subscribe to the `messages` webhook field

### Signal Messenger

Signal integration uses the [signal-cli REST API](https://github.com/bbernhard/signal-cli-rest-api) as a bridge:

```bash
# Start the Signal API bridge
docker run -d --name signal-api \
  -p 8080:8080 \
  -v $HOME/.local/share/signal-cli:/home/.local/share/signal-cli \
  -e MODE=json-rpc \
  bbernhard/signal-cli-rest-api

# Register your phone number
curl -X POST 'http://localhost:8080/v1/register/+1234567890'

# Configure Rovot
SIGNAL_API_URL=http://localhost:8080
SIGNAL_PHONE_NUMBER=+1234567890
```

### Linking your account

From any channel, send `/link YOUR_TOKEN` to the bot. Generate a link token from the Settings page or via:

```bash
curl -X POST http://localhost:5000/api/messaging/generate-link-token \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Background Services

### File Watcher

Monitors local directories and creates notes when files change. Ideal for desktop deployments.

```bash
# Add a directory to watch
curl -X POST http://localhost:5000/api/services/file-watcher/watch \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"directory": "/Users/you/Documents/projects", "recursive": true}'

# Start the watcher
curl -X POST http://localhost:5000/api/services/file-watcher/start \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Email Checker

Connects to IMAP inboxes and processes emails based on rules.

```bash
# Add an email account
curl -X POST http://localhost:5000/api/services/email/account \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email": "you@gmail.com", "password": "app-password", "provider": "gmail"}'

# Add a rule
curl -X PUT http://localhost:5000/api/services/email/rules \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"rules": [{"name": "urgent", "subject_contains": "urgent", "action": "task", "priority": "high"}]}'

# Start the checker
curl -X POST http://localhost:5000/api/services/email/start \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Deployment

### Docker (recommended for self-hosting)

```bash
# Development
docker compose up

# Production
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# With Signal support
docker compose --profile signal up -d
```

### Render.com (backend + database)

1. Connect your GitHub repository to Render
2. Click **New Blueprint** and select the repo — Render reads `render.yaml` automatically
3. Set secret environment variables in the Render dashboard (OPENAI_API_KEY, etc.)
4. Update `CORS_ORIGINS` to your frontend domain

### Vercel (frontend)

1. Connect your GitHub repository to Vercel
2. Set the root directory to `mindflow-frontend`
3. Add the environment variable `VITE_API_URL=https://your-backend.onrender.com/api`
4. Deploy

### Desktop App (.dmg / .exe)

The existing Electron packaging workflow remains unchanged. Build with:

```bash
cd mindflow-frontend
pnpm run build
# Then package with electron-builder as per existing configuration
```

---

## API Reference

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register a new user |
| POST | `/api/auth/login` | Login and receive JWT |
| POST | `/api/auth/refresh` | Refresh access token |
| GET | `/api/auth/profile` | Get current user profile |

### AI Assistant
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/ai-assistant/chat` | Send a message to the AI |
| GET | `/api/llm/settings` | Get current LLM configuration |
| POST | `/api/llm/settings` | Update LLM provider settings |
| POST | `/api/llm/test` | Test LLM connection |

### Messaging Channels
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/messaging/webhook/<channel>` | Receive messages (webhook) |
| POST | `/api/messaging/<channel>/setup` | Configure a channel |
| GET | `/api/messaging/<channel>/status` | Get channel status |
| POST | `/api/messaging/generate-link-token` | Generate account link token |
| GET | `/api/messaging/channels` | List all channels |

### Background Services
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/services/file-watcher/watch` | Add directory to watch |
| POST | `/api/services/file-watcher/start` | Start file watcher |
| POST | `/api/services/email/account` | Configure email account |
| PUT | `/api/services/email/rules` | Set email processing rules |
| POST | `/api/services/email/start` | Start email checker |

### Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check with DB status |

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License. See the LICENSE file for details.
