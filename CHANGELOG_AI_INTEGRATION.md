# MindFlow AI Integration — Changelog & Setup Guide

## Overview

This update adds three major features to MindFlow:

1. **OpenClaw AI Assistant** — A conversational AI powered by OpenAI that can create, edit, and query tasks, stakeholders, and notes, plus generate productivity insights.
2. **Telegram Bot Integration** — A full Telegram bot that lets you manage MindFlow from your phone via commands or natural language.
3. **Obsidian-Inspired Improvements** — Command palette, markdown notes, and enhanced analytics.

---

## New Files

| File | Description |
|------|-------------|
| `mindflow-backend/src/routes/ai_assistant.py` | Backend AI assistant with OpenAI function calling (12 tools) |
| `mindflow-backend/src/routes/telegram_bot.py` | Telegram bot webhook handler with smart message classification |
| `mindflow-frontend/src/components/AIChatWidget.jsx` | Floating AI chat widget (accessible from every page) |
| `mindflow-frontend/src/components/CommandPalette.jsx` | Obsidian-style command palette (Cmd+K) |
| `mindflow-frontend/src/components/TelegramSettings.jsx` | Telegram integration settings panel |
| `RESEARCH_NOTES.md` | Obsidian research findings used to guide improvements |

## Modified Files

| File | Changes |
|------|---------|
| `mindflow-backend/src/main.py` | Registered `ai_assistant_bp` and `telegram_bp` blueprints |
| `mindflow-frontend/src/lib/api.js` | Added `aiAPI.chat`, `aiAPI.quickInsight`, and `telegramAPI` endpoints |
| `mindflow-frontend/src/components/EnhancedDashboard.jsx` | Integrated AIChatWidget, CommandPalette, analytics page, enhanced notes |
| `mindflow-frontend/src/components/UserProfile.jsx` | Added Telegram tab to settings |
| `mindflow-frontend/package.json` | Added `react-markdown` dependency |

---

## Feature Details

### 1. OpenClaw AI Assistant

**Backend** (`ai_assistant.py`):
- Uses OpenAI's function calling with 12 defined tools
- Tools: `create_task`, `update_task`, `delete_task`, `list_tasks`, `create_stakeholder`, `update_stakeholder`, `list_stakeholders`, `create_note`, `update_note`, `list_notes`, `generate_insights`, `search_items`
- System prompt provides full context about MindFlow's data model
- Conversation history maintained for multi-turn interactions
- Graceful fallback when OpenAI is unavailable

**Frontend** (`AIChatWidget.jsx`):
- Floating purple button in bottom-right corner
- Slide-up chat panel with expand/minimize
- Markdown rendering in messages (via `react-markdown`)
- Voice input support (Web Speech API)
- Quick action buttons for common tasks
- Action badges showing what the AI did (e.g., "create task")
- Auto-refresh of dashboard data after AI actions
- Keyboard shortcut: **Cmd+J** (or Ctrl+J) to toggle

### 2. Telegram Bot Integration

**Backend** (`telegram_bot.py`):
- Webhook-based architecture (receives updates from Telegram)
- Commands:
  - `/start` — Welcome message with menu
  - `/task <description>` — Create a task (AI-parsed)
  - `/note <content>` — Save a note
  - `/stakeholder <info>` — Add a contact (AI-parsed)
  - `/status` — Dashboard statistics
  - `/insights` — AI-powered productivity insights
  - `/ask <question>` — Ask the AI anything
  - `/link <token>` — Link Telegram to MindFlow account
- Free-form text is auto-classified by AI into task/note/stakeholder/question
- Inline keyboard menus for quick actions
- Conversation state machine for multi-step flows

**Frontend** (`TelegramSettings.jsx`):
- Located in Profile → Telegram tab
- Bot token input (from @BotFather)
- Webhook URL configuration
- One-time link token generation
- Connection status indicator
- Usage guide with all commands

### 3. Obsidian-Inspired Improvements

**Command Palette** (`CommandPalette.jsx`):
- Triggered by **Cmd+K** (or Ctrl+K)
- Quick actions: create task, note, stakeholder, open AI
- Navigation: jump to any view
- Search: recent tasks, stakeholders, notes
- Uses shadcn/ui Command component

**Markdown Notes**:
- Note edit form now has title field
- Markdown preview toggle (Edit/Preview button)
- Monospace font in editor
- Placeholder with markdown syntax hints
- Note cards show title prominently

**Analytics Page**:
- Replaced "Coming Soon" placeholder
- Task status distribution with progress bars
- Stakeholder sentiment breakdown
- Overdue/urgent items attention section
- AI assistant tip card

---

## Setup Instructions

### AI Assistant (Required: OpenAI API Key)

The AI assistant uses the OpenAI API. Set these environment variables on your backend:

```bash
export OPENAI_API_KEY="sk-your-key-here"
export OPENAI_API_BASE=""  # Optional, for custom endpoints
```

### Telegram Bot Setup

1. **Create a bot** via [@BotFather](https://t.me/BotFather) on Telegram
2. Copy the bot token
3. In MindFlow, go to **Profile → Telegram** tab
4. Enter the bot token and your backend's public URL
5. Click "Connect Bot"
6. Generate a link token and send `/link <token>` to your bot

For the webhook to work, your backend must be publicly accessible (e.g., via ngrok, Cloudflare Tunnel, or a deployed server).

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Cmd+J` / `Ctrl+J` | Toggle AI Assistant chat |
| `Cmd+K` / `Ctrl+K` | Open Command Palette |
| `Escape` | Close AI chat or palette |
| `Enter` | Send message in AI chat |
| `Shift+Enter` | New line in AI chat |

---

## Architecture Notes

- The AI assistant uses OpenAI's `gpt-4o-mini` model for cost efficiency
- Function calling ensures structured data creation (no hallucinated fields)
- The Telegram bot reuses the same `_exec_*` functions as the AI assistant
- All database operations go through SQLAlchemy models (Task, Stakeholder, Note)
- The frontend chat widget is rendered at the root level, always accessible
- The command palette uses Radix UI's Command primitive (already in shadcn/ui)
