"""
AI Assistant (OpenClaw) - Conversational AI for MindFlow
Uses OpenAI function calling to create/edit/query tasks, stakeholders, notes,
and generate insights.
"""
from flask import Blueprint, request, jsonify, stream_with_context, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
import json
import logging
from datetime import datetime, timedelta

ai_assistant_bp = Blueprint('ai_assistant', __name__)
logger = logging.getLogger(__name__)

# OpenAI client (lazy init)
_client = None

def get_client():
    global _client
    if _client is not None:
        return _client
    api_key = os.environ.get('OPENAI_API_KEY', '').strip()
    api_base = os.environ.get('OPENAI_API_BASE', '').strip() or None
    if not api_key:
        return None
    try:
        from openai import OpenAI
        kwargs = {'api_key': api_key}
        if api_base:
            kwargs['base_url'] = api_base
        _client = OpenAI(**kwargs)
        return _client
    except Exception as e:
        logger.error(f"Failed to init OpenAI client: {e}")
        return None

# ── Tool definitions for function calling ──────────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_task",
            "description": "Create a new task in MindFlow. Use this when the user wants to add a task, to-do item, or action item.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Task title"},
                    "description": {"type": "string", "description": "Task description or details"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"], "description": "Task priority level"},
                    "due_date": {"type": "string", "description": "Due date in YYYY-MM-DD format"},
                    "status": {"type": "string", "enum": ["todo", "in_progress", "waiting", "done"], "description": "Task status"},
                    "board_column": {"type": "string", "enum": ["todo", "in_progress", "review", "done"], "description": "Kanban board column"}
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_task",
            "description": "Update an existing task. Use when the user wants to edit, change, or modify a task.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer", "description": "ID of the task to update"},
                    "title": {"type": "string", "description": "New task title"},
                    "description": {"type": "string", "description": "New task description"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]},
                    "due_date": {"type": "string", "description": "New due date in YYYY-MM-DD format"},
                    "status": {"type": "string", "enum": ["todo", "in_progress", "waiting", "done"]},
                    "board_column": {"type": "string", "enum": ["todo", "in_progress", "review", "done"]},
                    "completed": {"type": "boolean", "description": "Whether the task is completed"}
                },
                "required": ["task_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_tasks",
            "description": "List tasks with optional filters. Use when the user asks about their tasks, to-dos, or wants to see task status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["todo", "in_progress", "waiting", "done", "all"], "description": "Filter by status"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent", "all"], "description": "Filter by priority"},
                    "search": {"type": "string", "description": "Search term to filter tasks by title or description"},
                    "overdue_only": {"type": "boolean", "description": "Only show overdue tasks"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_task",
            "description": "Delete a task. Use when the user wants to remove a task.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer", "description": "ID of the task to delete"}
                },
                "required": ["task_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_stakeholder",
            "description": "Create a new stakeholder/contact in MindFlow. Use when the user mentions a person, contact, or stakeholder to add.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Full name of the person"},
                    "role": {"type": "string", "description": "Job title or role"},
                    "company": {"type": "string", "description": "Company or organization"},
                    "department": {"type": "string", "description": "Department"},
                    "email": {"type": "string", "description": "Email address"},
                    "phone": {"type": "string", "description": "Phone number"},
                    "birthday": {"type": "string", "description": "Birthday in YYYY-MM-DD format"},
                    "personal_notes": {"type": "string", "description": "Personal notes about this person"},
                    "location": {"type": "string", "description": "Location or city"},
                    "sentiment": {"type": "string", "enum": ["positive", "neutral", "negative"]},
                    "influence": {"type": "integer", "description": "Influence level 1-10"},
                    "interest": {"type": "integer", "description": "Interest level 1-10"},
                    "tags": {"type": "string", "description": "Comma-separated tags"}
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_stakeholder",
            "description": "Update an existing stakeholder/contact. Use when the user wants to edit contact information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "stakeholder_id": {"type": "integer", "description": "ID of the stakeholder to update"},
                    "name": {"type": "string"},
                    "role": {"type": "string"},
                    "company": {"type": "string"},
                    "department": {"type": "string"},
                    "email": {"type": "string"},
                    "phone": {"type": "string"},
                    "birthday": {"type": "string"},
                    "personal_notes": {"type": "string"},
                    "location": {"type": "string"},
                    "sentiment": {"type": "string", "enum": ["positive", "neutral", "negative"]},
                    "influence": {"type": "integer"},
                    "interest": {"type": "integer"},
                    "tags": {"type": "string", "description": "Comma-separated tags"}
                },
                "required": ["stakeholder_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_stakeholders",
            "description": "List stakeholders/contacts with optional filters. Use when the user asks about their contacts or network.",
            "parameters": {
                "type": "object",
                "properties": {
                    "search": {"type": "string", "description": "Search by name, company, or role"},
                    "sentiment": {"type": "string", "enum": ["positive", "neutral", "negative", "all"]}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_note",
            "description": "Create a new note in MindFlow. Use when the user wants to save a thought, idea, or information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "Note content (supports markdown)"},
                    "title": {"type": "string", "description": "Optional note title"},
                    "category": {"type": "string", "enum": ["general", "idea", "meeting", "reminder", "reference"], "description": "Note category"}
                },
                "required": ["content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_note",
            "description": "Update an existing note.",
            "parameters": {
                "type": "object",
                "properties": {
                    "note_id": {"type": "integer", "description": "ID of the note to update"},
                    "content": {"type": "string"},
                    "title": {"type": "string"},
                    "category": {"type": "string", "enum": ["general", "idea", "meeting", "reminder", "reference"]}
                },
                "required": ["note_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_notes",
            "description": "List notes with optional filters.",
            "parameters": {
                "type": "object",
                "properties": {
                    "search": {"type": "string", "description": "Search term"},
                    "category": {"type": "string", "description": "Filter by category"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_insights",
            "description": "Generate AI-powered insights and analysis about the user's productivity, tasks, stakeholders, or notes. Use when the user asks for a summary, analysis, recommendations, or insights.",
            "parameters": {
                "type": "object",
                "properties": {
                    "focus": {
                        "type": "string",
                        "enum": ["productivity", "stakeholders", "tasks", "notes", "weekly_review", "general"],
                        "description": "What area to focus the insights on"
                    },
                    "question": {"type": "string", "description": "Specific question the user is asking"}
                },
                "required": ["focus"]
            }
        }
    }
]

# ── Function execution helpers ─────────────────────────────────────────

def _exec_create_task(user_id, args):
    from src.models.task import Task
    from src.models.user import db
    
    status_to_column = {
        'todo': 'todo', 'in_progress': 'in_progress',
        'waiting': 'review', 'done': 'done'
    }
    status = args.get('status', 'todo')
    task = Task(
        user_id=user_id,
        title=args['title'],
        description=args.get('description', ''),
        priority=args.get('priority', 'medium'),
        due_date=args.get('due_date'),
        status=status,
        board_column=args.get('board_column', status_to_column.get(status, 'todo')),
        board_position=0
    )
    db.session.add(task)
    db.session.commit()
    return {"success": True, "task": task.to_dict(), "message": f"Task '{task.title}' created successfully."}


def _exec_update_task(user_id, args):
    from src.models.task import Task
    from src.models.user import db
    
    task = Task.query.filter_by(id=args['task_id'], user_id=user_id).first()
    if not task:
        return {"success": False, "message": f"Task with ID {args['task_id']} not found."}
    
    status_to_column = {
        'todo': 'todo', 'in_progress': 'in_progress',
        'waiting': 'review', 'done': 'done'
    }
    
    for field in ['title', 'description', 'priority', 'due_date', 'status', 'board_column', 'completed']:
        if field in args and args[field] is not None:
            setattr(task, field, args[field])
    
    if 'status' in args:
        task.board_column = status_to_column.get(args['status'], task.board_column)
    
    db.session.commit()
    return {"success": True, "task": task.to_dict(), "message": f"Task '{task.title}' updated successfully."}


def _exec_delete_task(user_id, args):
    from src.models.task import Task
    from src.models.user import db
    
    task = Task.query.filter_by(id=args['task_id'], user_id=user_id).first()
    if not task:
        return {"success": False, "message": f"Task with ID {args['task_id']} not found."}
    
    title = task.title
    db.session.delete(task)
    db.session.commit()
    return {"success": True, "message": f"Task '{title}' deleted successfully."}


def _exec_list_tasks(user_id, args):
    from src.models.task import Task
    
    query = Task.query.filter_by(user_id=user_id)
    
    status = args.get('status', 'all')
    if status and status != 'all':
        query = query.filter_by(status=status)
    
    priority = args.get('priority', 'all')
    if priority and priority != 'all':
        query = query.filter_by(priority=priority)
    
    search = args.get('search')
    if search:
        query = query.filter(
            (Task.title.ilike(f'%{search}%')) | (Task.description.ilike(f'%{search}%'))
        )
    
    tasks = query.order_by(Task.created_at.desc()).all()
    
    if args.get('overdue_only'):
        today = datetime.utcnow().strftime('%Y-%m-%d')
        tasks = [t for t in tasks if t.due_date and t.due_date < today and t.status != 'done']
    
    return {
        "success": True,
        "tasks": [t.to_dict() for t in tasks],
        "count": len(tasks),
        "message": f"Found {len(tasks)} task(s)."
    }


def _exec_create_stakeholder(user_id, args):
    from src.models.stakeholder import Stakeholder
    from src.models.user import db
    
    s = Stakeholder(
        user_id=user_id,
        name=args['name'],
        role=args.get('role'),
        company=args.get('company'),
        department=args.get('department'),
        email=args.get('email'),
        phone=args.get('phone'),
        birthday=args.get('birthday'),
        personal_notes=args.get('personal_notes'),
        location=args.get('location'),
        sentiment=args.get('sentiment', 'neutral'),
        influence=args.get('influence', 5),
        interest=args.get('interest', 5),
        tags=args.get('tags')
    )
    db.session.add(s)
    db.session.commit()
    return {"success": True, "stakeholder": s.to_dict(), "message": f"Stakeholder '{s.name}' created successfully."}


def _exec_update_stakeholder(user_id, args):
    from src.models.stakeholder import Stakeholder
    from src.models.user import db
    
    s = Stakeholder.query.filter_by(id=args['stakeholder_id'], user_id=user_id).first()
    if not s:
        return {"success": False, "message": f"Stakeholder with ID {args['stakeholder_id']} not found."}
    
    for field in ['name', 'role', 'company', 'department', 'email', 'phone', 'birthday',
                  'personal_notes', 'location', 'sentiment', 'influence', 'interest', 'tags']:
        if field in args and args[field] is not None:
            setattr(s, field, args[field])
    
    s.last_contact = datetime.utcnow()
    db.session.commit()
    return {"success": True, "stakeholder": s.to_dict(), "message": f"Stakeholder '{s.name}' updated successfully."}


def _exec_list_stakeholders(user_id, args):
    from src.models.stakeholder import Stakeholder
    
    query = Stakeholder.query.filter_by(user_id=user_id)
    
    search = args.get('search')
    if search:
        query = query.filter(
            (Stakeholder.name.ilike(f'%{search}%')) |
            (Stakeholder.company.ilike(f'%{search}%')) |
            (Stakeholder.role.ilike(f'%{search}%'))
        )
    
    sentiment = args.get('sentiment', 'all')
    if sentiment and sentiment != 'all':
        query = query.filter_by(sentiment=sentiment)
    
    stakeholders = query.order_by(Stakeholder.name).all()
    return {
        "success": True,
        "stakeholders": [s.to_dict() for s in stakeholders],
        "count": len(stakeholders),
        "message": f"Found {len(stakeholders)} stakeholder(s)."
    }


def _exec_create_note(user_id, args):
    from src.models.note import Note
    from src.models.user import db
    
    note = Note(
        user_id=user_id,
        content=args['content'],
        title=args.get('title'),
        category=args.get('category', 'general')
    )
    db.session.add(note)
    db.session.commit()
    return {"success": True, "note": note.to_dict(), "message": "Note created successfully."}


def _exec_update_note(user_id, args):
    from src.models.note import Note
    from src.models.user import db
    
    note = Note.query.filter_by(id=args['note_id'], user_id=user_id).first()
    if not note:
        return {"success": False, "message": f"Note with ID {args['note_id']} not found."}
    
    for field in ['content', 'title', 'category']:
        if field in args and args[field] is not None:
            setattr(note, field, args[field])
    
    db.session.commit()
    return {"success": True, "note": note.to_dict(), "message": "Note updated successfully."}


def _exec_list_notes(user_id, args):
    from src.models.note import Note
    
    query = Note.query.filter_by(user_id=user_id)
    
    search = args.get('search')
    if search:
        query = query.filter(
            (Note.content.ilike(f'%{search}%')) | (Note.title.ilike(f'%{search}%'))
        )
    
    category = args.get('category')
    if category:
        query = query.filter_by(category=category)
    
    notes = query.order_by(Note.created_at.desc()).all()
    return {
        "success": True,
        "notes": [n.to_dict() for n in notes],
        "count": len(notes),
        "message": f"Found {len(notes)} note(s)."
    }


def _exec_generate_insights(user_id, args):
    from src.models.task import Task
    from src.models.stakeholder import Stakeholder
    from src.models.note import Note
    
    focus = args.get('focus', 'general')
    
    tasks = Task.query.filter_by(user_id=user_id).all()
    stakeholders = Stakeholder.query.filter_by(user_id=user_id).all()
    notes = Note.query.filter_by(user_id=user_id).all()
    
    today = datetime.utcnow().strftime('%Y-%m-%d')
    
    # Build context data
    total_tasks = len(tasks)
    done_tasks = len([t for t in tasks if t.status == 'done'])
    overdue = [t for t in tasks if t.due_date and t.due_date < today and t.status != 'done']
    high_priority = [t for t in tasks if t.priority in ('high', 'urgent') and t.status != 'done']
    
    data = {
        "tasks_summary": {
            "total": total_tasks,
            "completed": done_tasks,
            "completion_rate": round(done_tasks / total_tasks * 100, 1) if total_tasks > 0 else 0,
            "overdue_count": len(overdue),
            "overdue_tasks": [{"title": t.title, "due_date": t.due_date, "priority": t.priority} for t in overdue[:5]],
            "high_priority_pending": [{"title": t.title, "due_date": t.due_date} for t in high_priority[:5]],
            "by_status": {},
            "by_priority": {}
        },
        "stakeholders_summary": {
            "total": len(stakeholders),
            "by_sentiment": {},
            "high_influence": [{"name": s.name, "company": s.company, "influence": s.influence} for s in stakeholders if s.influence and s.influence >= 8],
            "recent_contacts": []
        },
        "notes_summary": {
            "total": len(notes),
            "by_category": {},
            "recent": [{"content": n.content[:100], "category": n.category} for n in notes[:5]]
        }
    }
    
    # Count by status/priority
    for t in tasks:
        s = t.status or 'todo'
        data["tasks_summary"]["by_status"][s] = data["tasks_summary"]["by_status"].get(s, 0) + 1
        p = t.priority or 'medium'
        data["tasks_summary"]["by_priority"][p] = data["tasks_summary"]["by_priority"].get(p, 0) + 1
    
    for s in stakeholders:
        sent = s.sentiment or 'neutral'
        data["stakeholders_summary"]["by_sentiment"][sent] = data["stakeholders_summary"]["by_sentiment"].get(sent, 0) + 1
    
    for n in notes:
        cat = n.category or 'general'
        data["notes_summary"]["by_category"][cat] = data["notes_summary"]["by_category"].get(cat, 0) + 1
    
    return {
        "success": True,
        "data": data,
        "focus": focus,
        "question": args.get('question', ''),
        "message": "Insights data gathered successfully."
    }


# Map function names to executors
FUNCTION_MAP = {
    "create_task": _exec_create_task,
    "update_task": _exec_update_task,
    "delete_task": _exec_delete_task,
    "list_tasks": _exec_list_tasks,
    "create_stakeholder": _exec_create_stakeholder,
    "update_stakeholder": _exec_update_stakeholder,
    "list_stakeholders": _exec_list_stakeholders,
    "create_note": _exec_create_note,
    "update_note": _exec_update_note,
    "list_notes": _exec_list_notes,
    "generate_insights": _exec_generate_insights,
}

# ── System prompt ──────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are OpenClaw, the AI assistant for MindFlow — a personal productivity and stakeholder management app.

You help users manage their tasks, stakeholders/contacts, and notes through natural conversation. You are friendly, concise, and action-oriented.

**Your capabilities:**
- Create, update, delete, and list tasks (with Kanban board support)
- Create, update, and list stakeholders/contacts
- Create, update, and list notes
- Generate insights and analysis about productivity, stakeholders, and tasks
- Provide weekly reviews and recommendations

**Guidelines:**
- When the user mentions creating something, use the appropriate create function
- When asked about existing items, use list functions first to find them
- For updates, always list first to find the correct ID, then update
- When generating insights, gather data first, then provide a thoughtful analysis
- Use markdown formatting in your responses for readability
- Be proactive — suggest next steps or related actions
- Keep responses concise but helpful
- When you create or modify something, confirm what was done
- Today's date is {today}

**Important:**
- Always execute the relevant function calls — don't just describe what you would do
- If the user's request is ambiguous, ask for clarification
- For insights, analyze the data and provide actionable recommendations
"""

# ── API Routes ─────────────────────────────────────────────────────────

@ai_assistant_bp.route('/ai/chat', methods=['POST'])
@jwt_required()
def ai_chat():
    """Main AI chat endpoint - processes user messages and executes functions"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        user_message = data.get('message', '').strip()
        conversation_history = data.get('history', [])
        
        if not user_message:
            return jsonify({"success": False, "error": "Message is required"}), 400
        
        client = get_client()
        if not client:
            return jsonify({"success": False, "error": "AI service not available. Please configure OPENAI_API_KEY."}), 503
        
        today = datetime.utcnow().strftime('%Y-%m-%d')
        system_msg = SYSTEM_PROMPT.replace('{today}', today)
        
        # Build messages array
        messages = [{"role": "system", "content": system_msg}]
        
        # Add conversation history (last 20 messages to keep context manageable)
        for msg in conversation_history[-20:]:
            if msg.get('role') in ('user', 'assistant'):
                messages.append({"role": msg['role'], "content": msg['content']})
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        # First API call - may include tool calls
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.7,
            max_tokens=2000
        )
        
        assistant_message = response.choices[0].message
        tool_calls = assistant_message.tool_calls
        
        actions_taken = []
        
        # Process tool calls if any
        if tool_calls:
            # Add assistant message with tool calls to messages
            messages.append(assistant_message)
            
            for tool_call in tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)
                
                logger.info(f"🔧 Executing function: {fn_name} with args: {json.dumps(fn_args)}")
                
                executor = FUNCTION_MAP.get(fn_name)
                if executor:
                    try:
                        result = executor(user_id, fn_args)
                        actions_taken.append({
                            "function": fn_name,
                            "args": fn_args,
                            "result": result
                        })
                    except Exception as e:
                        logger.error(f"Function execution error: {e}")
                        result = {"success": False, "error": str(e)}
                else:
                    result = {"success": False, "error": f"Unknown function: {fn_name}"}
                
                # Add function result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, default=str)
                })
            
            # Second API call to get final response after function execution
            final_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )
            
            final_text = final_response.choices[0].message.content
        else:
            final_text = assistant_message.content
        
        return jsonify({
            "success": True,
            "message": final_text,
            "actions": actions_taken,
            "has_actions": len(actions_taken) > 0
        }), 200
        
    except Exception as e:
        logger.error(f"AI chat error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": f"AI chat failed: {str(e)}"}), 500


@ai_assistant_bp.route('/ai/quick-insight', methods=['GET'])
@jwt_required()
def quick_insight():
    """Generate a quick insight/tip based on current data"""
    try:
        user_id = get_jwt_identity()
        result = _exec_generate_insights(user_id, {"focus": "general"})
        
        if not result['success']:
            return jsonify(result), 500
        
        data = result['data']
        
        # Build a quick insight without AI call for speed
        insights = []
        
        overdue_count = data['tasks_summary']['overdue_count']
        if overdue_count > 0:
            insights.append(f"You have {overdue_count} overdue task(s) that need attention.")
        
        completion_rate = data['tasks_summary']['completion_rate']
        if completion_rate >= 80:
            insights.append(f"Great productivity! {completion_rate}% completion rate.")
        elif completion_rate < 50 and data['tasks_summary']['total'] > 0:
            insights.append(f"Your completion rate is {completion_rate}%. Consider breaking tasks into smaller pieces.")
        
        high_influence = data['stakeholders_summary']['high_influence']
        if high_influence:
            names = ', '.join([s['name'] for s in high_influence[:3]])
            insights.append(f"Key stakeholders to engage: {names}")
        
        return jsonify({
            "success": True,
            "insights": insights,
            "stats": {
                "total_tasks": data['tasks_summary']['total'],
                "completed_tasks": data['tasks_summary']['completed'],
                "overdue_tasks": overdue_count,
                "total_stakeholders": data['stakeholders_summary']['total'],
                "total_notes": data['notes_summary']['total']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Quick insight error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
