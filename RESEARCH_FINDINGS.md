# Research Findings

## LM Studio / Local LLM Integration
- LM Studio exposes OpenAI-compatible API at `http://localhost:1234/v1`
- Can use standard OpenAI Python SDK by changing `base_url`
- Supports `/v1/chat/completions`, `/v1/completions`, `/v1/embeddings`
- Also supports newer `/v1/responses` API
- Just need to set `base_url` and pass a dummy API key
- Also compatible with Ollama (`http://localhost:11434/v1`)

## WhatsApp Integration
- WhatsApp Business Cloud API (Meta) - webhook-based, requires business verification
- Twilio WhatsApp API - easier setup, sandbox available for dev
- Both use webhook pattern similar to existing Telegram integration
- Need VERIFY_TOKEN for webhook verification (GET) and message handling (POST)

## Signal Integration
- signal-cli REST API (via Docker container) - most practical approach
- signalbot Python package on PyPI
- signal-cli-rest-api Docker image provides REST endpoints
- Webhook-based architecture similar to Telegram/WhatsApp

## Architecture Decisions
1. LLM Provider abstraction layer - support OpenAI, LM Studio, Ollama, any OpenAI-compatible
2. Messaging channel abstraction - Telegram (existing), WhatsApp, Signal
3. Service modules - file watcher, email checker, scheduled tasks
4. Cloud deployment - Docker, Render, Vercel, Railway
5. Desktop packaging - Electron for .dmg/.exe
