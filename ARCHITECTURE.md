# Rovot/MindFlow Enhancement Architecture

## 1. Introduction

This document outlines the architectural design for enhancing the **MindFlow** (formerly Rovot) application. The goal is to transform the existing full-stack application into a more powerful, versatile, and production-ready personal assistant. The key enhancements include integrating multiple Large Language Model (LLM) providers, adding new communication channels (WhatsApp, Signal), implementing background services for file and email processing, and ensuring the application is secure and easily deployable on both cloud and desktop environments.

## 2. Core Principles

The architecture is guided by the following principles:

- **Modularity:** Components will be designed as loosely-coupled modules to allow for easy extension, maintenance, and independent development. This is crucial for adding future LLM providers, messaging channels, or background services.
- **Abstraction:** Key functionalities, such as LLM interaction and messaging, will be abstracted behind common interfaces. This allows the core application logic to remain agnostic of the specific implementation details (e.g., whether it's talking to OpenAI or a local LM Studio instance).
- **Security by Design:** Security is a primary consideration. This includes secure management of credentials, robust authentication and authorization, and protection against common web vulnerabilities.
- **Scalability & Deployability:** The application will be structured for straightforward deployment on various platforms, from serverless frontends like Vercel to container-based backends on Render or other cloud providers, using Docker for portability.

## 3. System Architecture Overview

The enhanced architecture consists of a **React Frontend**, a **Flask Backend**, and a new set of modular components for **LLM Providers**, **Messaging Channels**, and **Background Services**.

```mermaid
graph TD
    subgraph User Interfaces
        UI_React["React SPA (mindflow-frontend)"]
        UI_Desktop["Desktop App (Electron Wrapper)"]
        UI_Mobile["Messaging Channels (WhatsApp, Signal, Telegram)"]
    end

    subgraph Backend API (mindflow-backend)
        API["Flask REST API"]
        Auth["Authentication (JWT + OAuth)"]
        CoreLogic["Core Business Logic (Tasks, Stakeholders, Notes)"]
        DB[(PostgreSQL / SQLite)]

        subgraph Abstraction Layers
            LLM_Abs["LLM Provider Abstraction"]
            Channel_Abs["Messaging Channel Abstraction"]
        end

        subgraph Background Services
            Service_File["File Watcher Service"]
            Service_Email["Email Checker Service"]
        end
    end

    subgraph External Services
        Ext_OpenAI["OpenAI API"]
        Ext_LMStudio["Local LLM (LM Studio / Ollama)"]
        Ext_WhatsApp["WhatsApp Cloud API"]
        Ext_Signal["Signal CLI API"]
        Ext_Email["IMAP/SMTP Server"]
    end

    UI_React --> API
    UI_Desktop --> API
    UI_Mobile --> Channel_Abs

    API --> Auth
    API --> CoreLogic
    CoreLogic --> DB
    CoreLogic --> LLM_Abs

    Channel_Abs --> API

    LLM_Abs --> Ext_OpenAI
    LLM_Abs --> Ext_LMStudio

    Channel_Abs --> Ext_WhatsApp
    Channel_Abs --> Ext_Signal

    Service_File --> CoreLogic
    Service_Email --> CoreLogic

    CoreLogic --> Service_File
    CoreLogic --> Service_Email
```

### 3.1. LLM Provider Abstraction

To support both the official OpenAI API and local, OpenAI-compatible servers like LM Studio or Ollama, a new abstraction layer will be introduced.

- **Location:** `mindflow-backend/src/llm/`
- **Interface (`provider.py`):** A base class `LlmProvider` will define a common interface, including methods like `chat_completion(...)` and `parse_content(...)`.
- **Implementations:**
    - `openai_provider.py`: Implements the `LlmProvider` interface using the official `openai` Python SDK.
    - `local_llm_provider.py`: Implements the interface for OpenAI-compatible endpoints. It will be configurable with a `base_url` (e.g., `http://localhost:1234/v1`) and a dummy API key.
- **Factory (`factory.py`):** A factory function `get_llm_provider()` will read the user's configuration from the database or environment variables and return the appropriate provider instance.
- **Refactoring:** The existing routes in `ai_assistant.py` and `ai_parser.py` will be modified to use `get_llm_provider()` instead of directly initializing the OpenAI client.

### 3.2. Messaging Channel Abstraction

This layer will unify the handling of incoming messages from various platforms.

- **Location:** `mindflow-backend/src/channels/`
- **Interface (`channel.py`):** A base class `MessagingChannel` will define methods like `handle_webhook(...)`, `send_message(...)`, and `setup(...)`.
- **Implementations:**
    - `telegram_channel.py`: Refactors the existing logic from `telegram_bot.py` into a class that inherits from `MessagingChannel`.
    - `whatsapp_channel.py`: A new implementation for the WhatsApp Business API (via Twilio or Meta Cloud API).
    - `signal_channel.py`: A new implementation using a `signal-cli` REST API wrapper.
- **Unified Webhook:** A single new endpoint, `/api/messaging/webhook/<channel_name>`, will receive all incoming messages. It will delegate the request to the appropriate channel handler based on the URL.

### 3.3. Background Services

To provide proactive assistance, two background services will be implemented. These will run in separate threads or processes managed by the main Flask application.

- **Location:** `mindflow-backend/src/services/`
- **File Watcher Service (`file_watcher.py`):**
    - Uses the `watchdog` library to monitor user-specified directories.
    - When a new file is created or a file is modified, it will trigger an action (e.g., use the LLM provider to summarize the content and create a new note in MindFlow).
- **Email Checker Service (`email_checker.py`):**
    - Uses Python's built-in `imaplib` to connect to a user's email account.
    - Periodically fetches new emails from the inbox.
    - Processes emails based on user-defined rules (e.g., create a task from an email sent by a specific person, or save an email with a specific subject as a note).

## 4. Deployment Strategy

### 4.1. Cloud Deployment

The application is already designed for cloud deployment, but we will enhance this with Docker for greater portability.

- **Backend (Flask):**
    - A `Dockerfile` will be created for the backend. This allows it to be deployed on any service that supports containers, including Render, Railway, AWS ECS, or Google Cloud Run.
    - The `render.yaml` will be updated to use this Docker image instead of the native Python environment, ensuring consistency between development and production.
- **Frontend (React):**
    - The current deployment strategy using Vercel is optimal for a React SPA and will be maintained. The `vercel.json` file ensures correct configuration.

### 4.2. Desktop Application

To create `.dmg` and `.exe` installers, **Electron** will be used to wrap the existing web application.

- **Structure:** The Electron application will essentially be a lightweight browser that loads the React frontend.
- **Backend Integration:** For a fully self-contained desktop app, the Python backend can be packaged and run as a child process spawned by the Electron main process. This is a complex undertaking and will be treated as a secondary goal after the cloud-native enhancements are complete.

## 5. Security Enhancements

Building on the existing security measures, the following will be implemented:

- **Credential Management:** All API keys and sensitive credentials (e.g., IMAP passwords, database URLs) **MUST** be managed through environment variables. The application code will be audited to ensure no secrets are hardcoded.
- **Secure Configuration:** The frontend settings page where users enter credentials (e.g., for the Email Checker) will store this sensitive information encrypted in the database.
- **CORS Policy:** The backend's CORS policy will be strictly configured in production to only allow requests from the official frontend domain.
- **Rate Limiting:** The existing rate limiting on authentication endpoints will be reviewed and potentially extended to other resource-intensive API endpoints.

## 6. Frontend UI/UX Changes

A new **"Integrations & Services"** section will be added to the user settings page to manage the new features:

- **LLM Provider:** A dropdown to select between "OpenAI", "LM Studio (Local)", or "Custom". The user can then provide the necessary API Key and Base URL.
- **Messaging Channels:** Tabs for Telegram, WhatsApp, and Signal, each providing instructions and fields to configure the respective bot tokens and webhook URLs.
- **Background Services:** Toggles to enable/disable the File Watcher and Email Checker, with forms to specify directories to watch and enter IMAP credentials.
