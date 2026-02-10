"""
Telegram Bot Integration for MindFlow
Allows users to create tasks, stakeholders, and notes via Telegram.
Uses BotFather API token and webhook-based architecture.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
import json
import logging
import requests
from datetime import datetime

telegram_bp = Blueprint('telegram', __name__)
logger = logging.getLogger(__name__)

# ── Telegram API helpers ───────────────────────────────────────────────

def get_telegram_token():
    """Get Telegram bot token from environment or database"""
    return os.environ.get('TELEGRAM_BOT_TOKEN', '').strip()

def telegram_api(method, token, data=None):
    """Call Telegram Bot API"""
    url = f"https://api.telegram.org/bot{token}/{method}"
    try:
        if data:
            resp = requests.post(url, json=data, timeout=10)
        else:
            resp = requests.get(url, timeout=10)
        return resp.json()
    except Exception as e:
        logger.error(f"Telegram API error: {e}")
        return {"ok": False, "error": str(e)}

def send_message(token, chat_id, text, reply_markup=None, parse_mode="Markdown"):
    """Send a message via Telegram"""
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode
    }
    if reply_markup:
        data["reply_markup"] = reply_markup
    return telegram_api("sendMessage", token, data)

# ── Inline keyboard builders ──────────────────────────────────────────

def main_menu_keyboard():
    return {
        "inline_keyboard": [
            [
                {"text": "📝 Add Task", "callback_data": "action:add_task"},
                {"text": "👤 Add Contact", "callback_data": "action:add_stakeholder"}
            ],
            [
                {"text": "📒 Add Note", "callback_data": "action:add_note"},
                {"text": "📊 Status", "callback_data": "action:status"}
            ],
            [
                {"text": "🧠 Ask AI", "callback_data": "action:ask_ai"},
                {"text": "💡 Insights", "callback_data": "action:insights"}
            ]
        ]
    }

def priority_keyboard(prefix="priority"):
    return {
        "inline_keyboard": [
            [
                {"text": "🟢 Low", "callback_data": f"{prefix}:low"},
                {"text": "🟡 Medium", "callback_data": f"{prefix}:medium"},
            ],
            [
                {"text": "🟠 High", "callback_data": f"{prefix}:high"},
                {"text": "🔴 Urgent", "callback_data": f"{prefix}:urgent"},
            ]
        ]
    }

def confirm_keyboard(action_id):
    return {
        "inline_keyboard": [
            [
                {"text": "✅ Confirm", "callback_data": f"confirm:{action_id}"},
                {"text": "❌ Cancel", "callback_data": "cancel"}
            ]
        ]
    }

# ── User linking (Telegram chat_id ↔ MindFlow user) ──────────────────

# In-memory store for linked users and pending states
# In production, this should be stored in the database
_linked_users = {}  # chat_id -> user_id
_link_tokens = {}   # token -> user_id
_user_states = {}   # chat_id -> {state, data}

def get_user_id_for_chat(chat_id):
    """Get MindFlow user_id for a Telegram chat_id"""
    return _linked_users.get(str(chat_id))

def link_user(chat_id, user_id):
    """Link a Telegram chat to a MindFlow user"""
    _linked_users[str(chat_id)] = user_id
    logger.info(f"Linked Telegram chat {chat_id} to user {user_id}")

def set_user_state(chat_id, state, data=None):
    """Set conversation state for a user"""
    _user_states[str(chat_id)] = {"state": state, "data": data or {}}

def get_user_state(chat_id):
    """Get conversation state for a user"""
    return _user_states.get(str(chat_id), {"state": None, "data": {}})

def clear_user_state(chat_id):
    """Clear conversation state"""
    _user_states.pop(str(chat_id), None)

# ── Process incoming messages ─────────────────────────────────────────

def process_command(chat_id, command, args_text, token):
    """Process a bot command"""
    user_id = get_user_id_for_chat(chat_id)
    
    if command == '/start':
        welcome = (
            "🧠 *Welcome to MindFlow Bot!*\n\n"
            "I'm your personal productivity assistant. "
            "I can help you manage tasks, contacts, and notes right from Telegram.\n\n"
            "*Commands:*\n"
            "/task `<description>` — Create a new task\n"
            "/note `<content>` — Save a note\n"
            "/stakeholder `<name, details>` — Add a contact\n"
            "/status — View your dashboard stats\n"
            "/insights — Get AI-powered insights\n"
            "/ask `<question>` — Ask the AI assistant\n"
            "/link `<token>` — Link your MindFlow account\n"
            "/help — Show this help message\n\n"
            "Or just send me any text and I'll figure out what to do with it! 🚀"
        )
        if not user_id:
            welcome += (
                "\n\n⚠️ *Your account is not linked yet.*\n"
                "Go to MindFlow → Settings → Telegram Integration to get your link token, "
                "then use `/link <token>` to connect."
            )
        send_message(token, chat_id, welcome, main_menu_keyboard())
        return
    
    if command == '/help':
        process_command(chat_id, '/start', '', token)
        return
    
    if command == '/link':
        if not args_text:
            send_message(token, chat_id, 
                "Please provide your link token:\n`/link <your-token>`\n\n"
                "Get your token from MindFlow → Settings → Telegram Integration.",
            )
            return
        
        link_token = args_text.strip()
        linked_user_id = _link_tokens.get(link_token)
        if linked_user_id:
            link_user(chat_id, linked_user_id)
            _link_tokens.pop(link_token, None)
            send_message(token, chat_id, 
                "✅ *Account linked successfully!*\n\n"
                "You can now create tasks, notes, and contacts directly from Telegram.",
                main_menu_keyboard()
            )
        else:
            send_message(token, chat_id, 
                "❌ Invalid or expired link token. Please generate a new one from MindFlow."
            )
        return
    
    # All other commands require authentication
    if not user_id:
        send_message(token, chat_id,
            "⚠️ *Account not linked.*\n\n"
            "Please link your MindFlow account first:\n"
            "1. Go to MindFlow → Settings → Telegram Integration\n"
            "2. Click 'Generate Link Token'\n"
            "3. Use `/link <token>` here",
        )
        return
    
    if command == '/task':
        if not args_text:
            set_user_state(chat_id, 'awaiting_task')
            send_message(token, chat_id, "📝 What task would you like to create? Send me the details:")
            return
        _create_task_from_text(chat_id, user_id, args_text, token)
        return
    
    if command == '/note':
        if not args_text:
            set_user_state(chat_id, 'awaiting_note')
            send_message(token, chat_id, "📒 What would you like to note down?")
            return
        _create_note_from_text(chat_id, user_id, args_text, token)
        return
    
    if command == '/stakeholder':
        if not args_text:
            set_user_state(chat_id, 'awaiting_stakeholder')
            send_message(token, chat_id, "👤 Tell me about the contact (name, role, company, etc.):")
            return
        _create_stakeholder_from_text(chat_id, user_id, args_text, token)
        return
    
    if command == '/status':
        _send_status(chat_id, user_id, token)
        return
    
    if command == '/insights':
        _send_insights(chat_id, user_id, token)
        return
    
    if command == '/ask':
        if not args_text:
            set_user_state(chat_id, 'awaiting_question')
            send_message(token, chat_id, "🧠 What would you like to ask?")
            return
        _ask_ai(chat_id, user_id, args_text, token)
        return
    
    send_message(token, chat_id, f"Unknown command: {command}\nUse /help to see available commands.")


def process_text_message(chat_id, text, token):
    """Process a regular text message (not a command)"""
    user_id = get_user_id_for_chat(chat_id)
    
    if not user_id:
        send_message(token, chat_id,
            "⚠️ Please link your account first with `/link <token>`\n"
            "Get your token from MindFlow → Settings → Telegram Integration."
        )
        return
    
    # Check for pending state
    state = get_user_state(chat_id)
    
    if state['state'] == 'awaiting_task':
        clear_user_state(chat_id)
        _create_task_from_text(chat_id, user_id, text, token)
        return
    
    if state['state'] == 'awaiting_note':
        clear_user_state(chat_id)
        _create_note_from_text(chat_id, user_id, text, token)
        return
    
    if state['state'] == 'awaiting_stakeholder':
        clear_user_state(chat_id)
        _create_stakeholder_from_text(chat_id, user_id, text, token)
        return
    
    if state['state'] == 'awaiting_question':
        clear_user_state(chat_id)
        _ask_ai(chat_id, user_id, text, token)
        return
    
    # No pending state — use AI to classify and process
    _smart_process(chat_id, user_id, text, token)


def process_callback(chat_id, callback_data, message_id, token):
    """Process inline keyboard callback"""
    user_id = get_user_id_for_chat(chat_id)
    
    if callback_data == 'cancel':
        clear_user_state(chat_id)
        send_message(token, chat_id, "Cancelled. What would you like to do?", main_menu_keyboard())
        return
    
    if callback_data.startswith('action:'):
        action = callback_data.split(':')[1]
        
        if action == 'add_task':
            set_user_state(chat_id, 'awaiting_task')
            send_message(token, chat_id, "📝 Send me the task description:")
        elif action == 'add_stakeholder':
            set_user_state(chat_id, 'awaiting_stakeholder')
            send_message(token, chat_id, "👤 Tell me about the contact (name, role, company, etc.):")
        elif action == 'add_note':
            set_user_state(chat_id, 'awaiting_note')
            send_message(token, chat_id, "📒 What would you like to note down?")
        elif action == 'status':
            if user_id:
                _send_status(chat_id, user_id, token)
            else:
                send_message(token, chat_id, "⚠️ Please link your account first.")
        elif action == 'ask_ai':
            set_user_state(chat_id, 'awaiting_question')
            send_message(token, chat_id, "🧠 What would you like to ask?")
        elif action == 'insights':
            if user_id:
                _send_insights(chat_id, user_id, token)
            else:
                send_message(token, chat_id, "⚠️ Please link your account first.")
        return
    
    if callback_data.startswith('priority:'):
        priority = callback_data.split(':')[1]
        state = get_user_state(chat_id)
        if state['state'] == 'awaiting_priority' and state['data'].get('task_title'):
            _finalize_task(chat_id, user_id, state['data']['task_title'], priority, token)
            clear_user_state(chat_id)
        return


# ── Action helpers ─────────────────────────────────────────────────────

def _create_task_from_text(chat_id, user_id, text, token):
    """Use AI to parse text and create a task"""
    try:
        from src.routes.ai_assistant import get_client, _exec_create_task
        
        client = get_client()
        if client:
            # Use AI to extract task details
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Extract task information from the text. Return JSON with: title, description, priority (low/medium/high/urgent), due_date (YYYY-MM-DD or null). Today is " + datetime.utcnow().strftime('%Y-%m-%d')},
                    {"role": "user", "content": text}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=300
            )
            task_data = json.loads(response.choices[0].message.content)
        else:
            task_data = {"title": text, "priority": "medium"}
        
        result = _exec_create_task(user_id, {
            "title": task_data.get("title", text),
            "description": task_data.get("description", ""),
            "priority": task_data.get("priority", "medium"),
            "due_date": task_data.get("due_date"),
            "status": "todo"
        })
        
        if result['success']:
            task = result['task']
            msg = (
                f"✅ *Task created!*\n\n"
                f"📝 *{task['title']}*\n"
                f"Priority: {task.get('priority', 'medium')}\n"
                f"Due: {task.get('due_date', 'Not set')}\n"
                f"Status: {task.get('status', 'todo')}"
            )
            send_message(token, chat_id, msg, main_menu_keyboard())
        else:
            send_message(token, chat_id, f"❌ Failed to create task: {result.get('message', 'Unknown error')}")
    except Exception as e:
        logger.error(f"Task creation error: {e}")
        send_message(token, chat_id, f"❌ Error creating task: {str(e)}")


def _create_note_from_text(chat_id, user_id, text, token):
    """Create a note from text"""
    try:
        from src.routes.ai_assistant import _exec_create_note
        
        result = _exec_create_note(user_id, {
            "content": text,
            "category": "general"
        })
        
        if result['success']:
            send_message(token, chat_id, 
                f"✅ *Note saved!*\n\n📒 {text[:200]}{'...' if len(text) > 200 else ''}",
                main_menu_keyboard()
            )
        else:
            send_message(token, chat_id, f"❌ Failed to save note: {result.get('message')}")
    except Exception as e:
        logger.error(f"Note creation error: {e}")
        send_message(token, chat_id, f"❌ Error saving note: {str(e)}")


def _create_stakeholder_from_text(chat_id, user_id, text, token):
    """Use AI to parse text and create a stakeholder"""
    try:
        from src.routes.ai_assistant import get_client, _exec_create_stakeholder
        
        client = get_client()
        if client:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Extract contact/person information from the text. Return JSON with: name, role, company, department, email, phone, personal_notes, location. Use null for missing fields."},
                    {"role": "user", "content": text}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=300
            )
            data = json.loads(response.choices[0].message.content)
        else:
            # Basic extraction
            words = text.split()
            data = {"name": ' '.join(words[:2]) if len(words) >= 2 else text, "personal_notes": text}
        
        if not data.get('name'):
            data['name'] = text.split(',')[0].strip() if ',' in text else text[:50]
        
        result = _exec_create_stakeholder(user_id, {
            "name": data.get("name", "Unknown"),
            "role": data.get("role"),
            "company": data.get("company"),
            "department": data.get("department"),
            "email": data.get("email"),
            "phone": data.get("phone"),
            "personal_notes": data.get("personal_notes", text),
            "location": data.get("location"),
            "sentiment": "neutral",
            "influence": 5,
            "interest": 5
        })
        
        if result['success']:
            s = result['stakeholder']
            msg = (
                f"✅ *Contact added!*\n\n"
                f"👤 *{s['name']}*\n"
            )
            if s.get('role'): msg += f"Role: {s['role']}\n"
            if s.get('company'): msg += f"Company: {s['company']}\n"
            if s.get('email'): msg += f"Email: {s['email']}\n"
            send_message(token, chat_id, msg, main_menu_keyboard())
        else:
            send_message(token, chat_id, f"❌ Failed to add contact: {result.get('message')}")
    except Exception as e:
        logger.error(f"Stakeholder creation error: {e}")
        send_message(token, chat_id, f"❌ Error adding contact: {str(e)}")


def _send_status(chat_id, user_id, token):
    """Send dashboard status"""
    try:
        from src.routes.ai_assistant import _exec_list_tasks, _exec_list_stakeholders, _exec_list_notes
        
        tasks = _exec_list_tasks(user_id, {"status": "all"})
        stakeholders = _exec_list_stakeholders(user_id, {})
        notes = _exec_list_notes(user_id, {})
        
        task_list = tasks.get('tasks', [])
        total = len(task_list)
        done = len([t for t in task_list if t.get('status') == 'done'])
        overdue_count = len([t for t in task_list if t.get('due_date') and t['due_date'] < datetime.utcnow().strftime('%Y-%m-%d') and t.get('status') != 'done'])
        
        msg = (
            f"📊 *MindFlow Status*\n\n"
            f"📝 *Tasks:* {total} total, {done} completed\n"
            f"{'⚠️ ' + str(overdue_count) + ' overdue!' if overdue_count > 0 else '✅ All on track!'}\n\n"
            f"👥 *Contacts:* {stakeholders.get('count', 0)}\n"
            f"📒 *Notes:* {notes.get('count', 0)}\n\n"
        )
        
        # Show pending tasks
        pending = [t for t in task_list if t.get('status') != 'done'][:5]
        if pending:
            msg += "*Upcoming tasks:*\n"
            for t in pending:
                priority_emoji = {'urgent': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}.get(t.get('priority', 'medium'), '⚪')
                msg += f"{priority_emoji} {t['title']}"
                if t.get('due_date'):
                    msg += f" (due: {t['due_date']})"
                msg += "\n"
        
        send_message(token, chat_id, msg, main_menu_keyboard())
    except Exception as e:
        logger.error(f"Status error: {e}")
        send_message(token, chat_id, f"❌ Error getting status: {str(e)}")


def _send_insights(chat_id, user_id, token):
    """Send AI-powered insights"""
    try:
        from src.routes.ai_assistant import get_client, _exec_generate_insights
        
        result = _exec_generate_insights(user_id, {"focus": "general"})
        data = result.get('data', {})
        
        client = get_client()
        if client:
            # Use AI to generate natural language insights
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a productivity coach. Analyze this data and provide 3-5 brief, actionable insights. Use emoji. Be encouraging but honest. Keep it under 500 characters."},
                    {"role": "user", "content": f"User productivity data: {json.dumps(data, default=str)}"}
                ],
                temperature=0.7,
                max_tokens=300
            )
            insights_text = response.choices[0].message.content
        else:
            ts = data.get('tasks_summary', {})
            insights_text = (
                f"📊 You have {ts.get('total', 0)} tasks ({ts.get('completed', 0)} done).\n"
                f"Completion rate: {ts.get('completion_rate', 0)}%\n"
            )
            if ts.get('overdue_count', 0) > 0:
                insights_text += f"⚠️ {ts['overdue_count']} tasks are overdue!"
        
        msg = f"💡 *AI Insights*\n\n{insights_text}"
        send_message(token, chat_id, msg, main_menu_keyboard())
    except Exception as e:
        logger.error(f"Insights error: {e}")
        send_message(token, chat_id, f"❌ Error generating insights: {str(e)}")


def _ask_ai(chat_id, user_id, question, token):
    """Forward question to AI assistant"""
    try:
        from src.routes.ai_assistant import get_client, _exec_generate_insights
        
        # Gather context
        insights = _exec_generate_insights(user_id, {"focus": "general"})
        data = insights.get('data', {})
        
        client = get_client()
        if not client:
            send_message(token, chat_id, "❌ AI service not available.")
            return
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"You are OpenClaw, the MindFlow AI assistant. Answer the user's question based on their productivity data. Be concise (max 500 chars). Use emoji. Data: {json.dumps(data, default=str)}"},
                {"role": "user", "content": question}
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        answer = response.choices[0].message.content
        send_message(token, chat_id, f"🧠 *OpenClaw:*\n\n{answer}", main_menu_keyboard())
    except Exception as e:
        logger.error(f"AI ask error: {e}")
        send_message(token, chat_id, f"❌ Error: {str(e)}")


def _smart_process(chat_id, user_id, text, token):
    """Use AI to classify and process free-form text"""
    try:
        from src.routes.ai_assistant import get_client
        
        client = get_client()
        if not client:
            # Fallback: save as note
            _create_note_from_text(chat_id, user_id, text, token)
            return
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": 'Classify this text as "task", "stakeholder", "note", or "question". Return JSON: {"type": "...", "confidence": 0.0-1.0}'},
                {"role": "user", "content": text}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=50
        )
        
        classification = json.loads(response.choices[0].message.content)
        content_type = classification.get('type', 'note')
        
        if content_type == 'task':
            _create_task_from_text(chat_id, user_id, text, token)
        elif content_type == 'stakeholder':
            _create_stakeholder_from_text(chat_id, user_id, text, token)
        elif content_type == 'question':
            _ask_ai(chat_id, user_id, text, token)
        else:
            _create_note_from_text(chat_id, user_id, text, token)
    except Exception as e:
        logger.error(f"Smart process error: {e}")
        # Fallback to note
        _create_note_from_text(chat_id, user_id, text, token)


# ── Flask Routes ───────────────────────────────────────────────────────

@telegram_bp.route('/telegram/webhook', methods=['POST'])
def telegram_webhook():
    """Receive updates from Telegram via webhook"""
    try:
        token = get_telegram_token()
        if not token:
            return jsonify({"ok": False, "error": "Telegram bot not configured"}), 503
        
        update = request.get_json()
        if not update:
            return jsonify({"ok": True}), 200
        
        logger.info(f"Telegram update: {json.dumps(update)[:500]}")
        
        # Handle callback queries (inline keyboard)
        if 'callback_query' in update:
            callback = update['callback_query']
            chat_id = callback['message']['chat']['id']
            callback_data = callback['data']
            message_id = callback['message']['message_id']
            
            # Acknowledge callback
            telegram_api("answerCallbackQuery", token, {"callback_query_id": callback['id']})
            
            process_callback(chat_id, callback_data, message_id, token)
            return jsonify({"ok": True}), 200
        
        # Handle messages
        message = update.get('message', {})
        chat_id = message.get('chat', {}).get('id')
        text = message.get('text', '')
        
        if not chat_id or not text:
            return jsonify({"ok": True}), 200
        
        # Check if it's a command
        if text.startswith('/'):
            parts = text.split(maxsplit=1)
            command = parts[0].split('@')[0].lower()  # Remove @botname
            args_text = parts[1] if len(parts) > 1 else ''
            process_command(chat_id, command, args_text, token)
        else:
            process_text_message(chat_id, text, token)
        
        return jsonify({"ok": True}), 200
        
    except Exception as e:
        logger.error(f"Telegram webhook error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"ok": True}), 200  # Always return 200 to Telegram


@telegram_bp.route('/telegram/setup', methods=['POST'])
@jwt_required()
def setup_telegram():
    """Setup Telegram bot webhook and get bot info"""
    try:
        data = request.get_json()
        bot_token = data.get('bot_token', '').strip()
        webhook_url = data.get('webhook_url', '').strip()
        
        if not bot_token:
            return jsonify({"success": False, "error": "Bot token is required"}), 400
        
        # Verify the token by getting bot info
        bot_info = telegram_api("getMe", bot_token)
        if not bot_info.get('ok'):
            return jsonify({"success": False, "error": "Invalid bot token"}), 400
        
        bot_data = bot_info.get('result', {})
        
        # Set webhook if URL provided
        if webhook_url:
            webhook_result = telegram_api("setWebhook", bot_token, {
                "url": f"{webhook_url}/api/telegram/webhook",
                "allowed_updates": ["message", "callback_query"]
            })
            
            if not webhook_result.get('ok'):
                return jsonify({
                    "success": False, 
                    "error": f"Failed to set webhook: {webhook_result.get('description', 'Unknown error')}"
                }), 400
        
        return jsonify({
            "success": True,
            "bot": {
                "id": bot_data.get('id'),
                "username": bot_data.get('username'),
                "first_name": bot_data.get('first_name'),
                "can_join_groups": bot_data.get('can_join_groups', False)
            },
            "webhook_set": bool(webhook_url)
        }), 200
        
    except Exception as e:
        logger.error(f"Telegram setup error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@telegram_bp.route('/telegram/generate-link-token', methods=['POST'])
@jwt_required()
def generate_link_token():
    """Generate a one-time token to link Telegram account"""
    try:
        user_id = get_jwt_identity()
        
        import secrets
        token = secrets.token_urlsafe(32)
        _link_tokens[token] = user_id
        
        return jsonify({
            "success": True,
            "link_token": token,
            "instructions": "Send this to the MindFlow Telegram bot: /link " + token
        }), 200
        
    except Exception as e:
        logger.error(f"Generate link token error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@telegram_bp.route('/telegram/status', methods=['GET'])
@jwt_required()
def telegram_status():
    """Check Telegram bot connection status"""
    try:
        token = get_telegram_token()
        user_id = get_jwt_identity()
        
        if not token:
            return jsonify({
                "success": True,
                "configured": False,
                "linked": False,
                "message": "Telegram bot token not configured"
            }), 200
        
        bot_info = telegram_api("getMe", token)
        webhook_info = telegram_api("getWebhookInfo", token)
        
        # Check if current user is linked
        is_linked = any(uid == user_id for uid in _linked_users.values())
        
        return jsonify({
            "success": True,
            "configured": True,
            "bot": bot_info.get('result', {}),
            "webhook": webhook_info.get('result', {}),
            "linked": is_linked
        }), 200
        
    except Exception as e:
        logger.error(f"Telegram status error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
