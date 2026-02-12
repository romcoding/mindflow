from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
import os
import json
import logging

ai_parser_bp = Blueprint('ai_parser', __name__)
logger = logging.getLogger(__name__)

# Lazy initialization of OpenAI client
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
client = None

def get_openai_client():
    """Lazy initialization of OpenAI client to avoid import-time errors"""
    global client
    if client is not None:
        return client
    
    if not OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not set - AI parsing will not be available")
        return None
    
    try:
        from openai import OpenAI
        # Only pass api_key explicitly to avoid any proxy/environment variable conflicts
        # Strip any whitespace from the API key
        api_key = OPENAI_API_KEY.strip() if OPENAI_API_KEY else None
        if not api_key:
            logger.warning("OPENAI_API_KEY is empty after stripping")
            return None
        
        # Initialize client with only the api_key parameter
        # This avoids issues with proxies or other environment variables
        client = OpenAI(api_key=api_key)
        logger.info("✅ OpenAI client initialized successfully")
        return client
    except TypeError as e:
        # Handle specific TypeError about unexpected arguments
        logger.error(f"Failed to initialize OpenAI client (TypeError): {str(e)}")
        logger.error("This might be due to an incompatible OpenAI library version or environment variable conflicts")
        # Try to re-import and check version
        try:
            import openai
            logger.error(f"OpenAI library version: {openai.__version__}")
        except:
            pass
        return None
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

@ai_parser_bp.route('/ai/check-config', methods=['GET'])
@jwt_required()
def check_ai_config():
    """Diagnostic endpoint to check OpenAI configuration"""
    try:
        api_key_set = bool(OPENAI_API_KEY)
        api_key_length = len(OPENAI_API_KEY) if OPENAI_API_KEY else 0
        api_key_prefix = OPENAI_API_KEY[:10] + "..." if OPENAI_API_KEY and len(OPENAI_API_KEY) > 10 else "N/A"
        
        client = get_openai_client()
        client_available = client is not None
        
        # Try to get OpenAI library version
        try:
            import openai
            openai_version = openai.__version__
        except:
            openai_version = "Unknown"
        
        return jsonify({
            'openai_api_key_set': api_key_set,
            'openai_api_key_length': api_key_length,
            'openai_api_key_prefix': api_key_prefix,
            'openai_client_available': client_available,
            'openai_library_version': openai_version
        }), 200
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@ai_parser_bp.route('/ai/parse-content', methods=['POST'])
@jwt_required()
def parse_content():
    """Use AI to parse and structure content from text input"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        
        if not text:
            return jsonify({
                'success': False,
                'error': 'Text input is required'
            }), 400
        
        logger.info(f"📝 AI parsing request for text: {text[:100]}...")
        
        client = get_openai_client()
        if not client:
            logger.warning("❌ OpenAI client not available - returning error")
            return jsonify({
                'success': False,
                'error': 'AI parsing not available. OPENAI_API_KEY not configured or client initialization failed.'
            }), 503
        
        logger.info("✅ OpenAI client available, proceeding with AI parsing")
        
        # Determine content type first
        type_prompt = f"""Analyze the following text and determine if it's about:
1. A task/to-do item - something that needs to be done, an action item, a reminder
2. A person/stakeholder/contact - information about a person, someone's name, contact details, someone you met or know
3. A general note - any other information, thoughts, observations, or general notes

IMPORTANT: If the text mentions a person's name, contact information, role, company, or any personal details, it should be classified as "stakeholder" even if it also contains other information.

Text: "{text}"

Respond with ONLY one word: "task", "stakeholder", or "note"
"""
        
        logger.info("🔍 Step 1: Classifying content type...")
        type_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a content classifier. Respond with only one word."},
                {"role": "user", "content": type_prompt}
            ],
            temperature=0.3,
            max_tokens=10
        )
        
        # Log OpenAI API usage
        if hasattr(type_response, 'usage'):
            logger.info(f"📊 OpenAI API usage (classification) - Tokens: {type_response.usage.total_tokens} (prompt: {type_response.usage.prompt_tokens}, completion: {type_response.usage.completion_tokens})")
        
        content_type = type_response.choices[0].message.content.strip().lower()
        logger.info(f"✅ Content classified as: {content_type}")
        
        # If it's a stakeholder, extract detailed information
        if content_type == 'stakeholder':
            # Comprehensive extraction prompt covering ALL stakeholder model fields
            system_prompt = (
                "You are an AI extraction system for a CRM/stakeholder management tool. "
                "Extract ALL possible information about a person from natural language or voice-transcribed text. "
                "Handle spelling errors, run-on sentences, and phonetic misspellings gracefully. "
                "Correct capitalization of proper names and companies. "
                "Infer fields intelligently from context (e.g., 'CEO' → seniority_level: 'executive', influence: 8, decision_making_authority: 'high'). "
                "Use null for any field not mentioned or inferable. Return ONLY valid JSON."
            )
            
            extraction_prompt = f"""Extract ALL stakeholder fields from this text. Return a JSON object with these exact keys:

BASIC: name (string), role (string), company (string), department (string), job_title (string), email (string), phone (string)
PERSONAL: birthday (YYYY-MM-DD), personal_notes (string), family_info (string), hobbies (string), education (string), career_history (string)
PROFESSIONAL: seniority_level (junior|mid|senior|executive), years_experience (integer), specializations (comma-separated string), decision_making_authority (low|medium|high), budget_authority (none|limited|significant|full), work_style (string)
GEOGRAPHIC: location (string, City/Country), timezone (e.g. EST, CET, UTC+1), preferred_language (string), cultural_background (string)
COMMUNICATION: preferred_communication_method (email|phone|slack|teams|whatsapp), communication_frequency (daily|weekly|monthly|as_needed), best_contact_time (string), communication_style (formal|casual|direct|diplomatic)
SOCIAL: linkedin_url (string), twitter_handle (string)
RELATIONSHIP: sentiment (positive|neutral|negative), influence (1-10), interest (1-10), trust_level (1-10), strategic_value (low|medium|high|critical), tags (comma-separated string)

Inference rules:
- "CEO/CTO/VP/Director/Head of" → seniority_level: executive, influence: 8+, decision_making_authority: high
- "Manager/Lead/Senior" → seniority_level: senior, influence: 6-7
- "Junior/Intern/Associate" → seniority_level: junior, influence: 3-4
- Mentioned "met at conference/event" → sentiment: positive, tags include "networking"
- Mentioned "client/customer" → strategic_value: high, tags include "client"
- Mentioned "friend/buddy" → sentiment: positive, communication_style: casual
- Phone patterns: detect and format international numbers
- Email patterns: detect email addresses even in voice text ("at" → "@", "dot" → ".")
- "Name, Company Role" pattern: split correctly (e.g. "Niclas Delfs, Vector8 Executive Director")

Text: "{text}"

Return ONLY valid JSON with all keys listed above. Use null for missing/unknown fields."""
            
            logger.info("🔍 Step 2: Extracting comprehensive stakeholder information...")
            extraction_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": extraction_prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            if hasattr(extraction_response, 'usage'):
                logger.info(f"📊 OpenAI API usage (extraction) - Tokens: {extraction_response.usage.total_tokens}")
            
            try:
                d = json.loads(extraction_response.choices[0].message.content)
                logger.info(f"📊 Extracted data: {json.dumps(d, indent=2)}")
                
                # Helper to safely get int values
                def safe_int(val, default=None):
                    if val is None: return default
                    try: return int(val)
                    except (ValueError, TypeError): return default
                
                # Build comprehensive stakeholder_info matching ALL model fields
                stakeholder_info = {
                    # Basic
                    'name': d.get('name') or None,
                    'role': d.get('role') or d.get('job_title') or None,
                    'company': d.get('company') or None,
                    'department': d.get('department') or None,
                    'job_title': d.get('job_title') or d.get('role') or None,
                    'email': d.get('email') or None,
                    'phone': d.get('phone') or None,
                    # Personal
                    'birthday': d.get('birthday') or None,
                    'personal_notes': d.get('personal_notes') or None,
                    'family_info': d.get('family_info') or None,
                    'hobbies': d.get('hobbies') or None,
                    'education': d.get('education') or None,
                    'career_history': d.get('career_history') or None,
                    # Professional
                    'seniority_level': d.get('seniority_level') or None,
                    'years_experience': safe_int(d.get('years_experience')),
                    'specializations': d.get('specializations') or None,
                    'decision_making_authority': d.get('decision_making_authority') or None,
                    'budget_authority': d.get('budget_authority') or None,
                    'work_style': d.get('work_style') or None,
                    # Geographic
                    'location': d.get('location') or None,
                    'timezone': d.get('timezone') or None,
                    'preferred_language': d.get('preferred_language') or None,
                    'cultural_background': d.get('cultural_background') or None,
                    # Communication
                    'preferred_communication_method': d.get('preferred_communication_method') or None,
                    'communication_frequency': d.get('communication_frequency') or None,
                    'best_contact_time': d.get('best_contact_time') or None,
                    'communication_style': d.get('communication_style') or None,
                    # Social
                    'linkedin_url': d.get('linkedin_url') or None,
                    'twitter_handle': d.get('twitter_handle') or None,
                    # Relationship
                    'sentiment': d.get('sentiment') or 'neutral',
                    'influence': safe_int(d.get('influence'), 5),
                    'interest': safe_int(d.get('interest'), 5),
                    'trust_level': safe_int(d.get('trust_level'), 5),
                    'strategic_value': d.get('strategic_value') or 'medium',
                    'tags': d.get('tags') or None,
                    # Keep original text as fallback notes
                    '_original_text': text
                }
                
                logger.info(f"✅ Comprehensive stakeholder_info extracted")
                
                return jsonify({
                    'success': True,
                    'type': 'stakeholder',
                    'stakeholder_info': stakeholder_info,
                    'confidence': 0.95,
                    'open_modal': True  # Signal frontend to open edit modal for review
                }), 200
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI JSON response: {e}")
                return jsonify({
                    'success': True,
                    'type': 'stakeholder',
                    'stakeholder_info': {
                        'name': None,
                        'personal_notes': text,
                        '_original_text': text
                    },
                    'confidence': 0.7,
                    'open_modal': True
                }), 200
        
        elif content_type == 'task':
            from datetime import date
            today = date.today().isoformat()
            
            task_prompt = f"""Extract task information from the following text. Today is {today}.
Return a JSON object with:
- title: A clear, concise task title (action-oriented, max 80 chars)
- description: Detailed description, context, or notes (can be longer)
- priority: "low", "medium", "high", or "urgent" based on keywords/urgency
  * "ASAP", "immediately", "critical" → urgent
  * "important", "soon" → high
  * Default → medium
- due_date: Due date in YYYY-MM-DD format. Interpret relative dates:
  * "tomorrow" → {today} + 1 day
  * "next week" → next Monday
  * "end of week" → this Friday
  * "next month" → 1st of next month
  * null if no date mentioned
- status: "todo", "in_progress", "waiting", or "done"
  * "started", "working on" → in_progress
  * "waiting for", "blocked" → waiting
  * Default → todo
- board_column: "todo", "in_progress", "review", or "done" (matches status)
- stakeholder_name: Name of person related to this task if mentioned, or null

Text: "{text}"

Return ONLY valid JSON."""
            
            logger.info("\ud83d\udd0d Extracting task information...")
            task_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a task extraction assistant for a productivity app. Extract structured task data from natural language or voice input. Handle speech-to-text errors gracefully. Return ONLY valid JSON."},
                    {"role": "user", "content": task_prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            try:
                td = json.loads(task_response.choices[0].message.content)
                
                status = td.get('status') or 'todo'
                status_to_col = {'todo': 'todo', 'in_progress': 'in_progress', 'waiting': 'review', 'done': 'done'}
                
                return jsonify({
                    'success': True,
                    'type': 'task',
                    'task_info': {
                        'title': td.get('title') or text,
                        'description': td.get('description') or '',
                        'priority': td.get('priority') or 'medium',
                        'due_date': td.get('due_date'),
                        'status': status,
                        'board_column': status_to_col.get(status, 'todo'),
                        'stakeholder_name': td.get('stakeholder_name')
                    },
                    'confidence': 0.9,
                    'open_modal': True  # Signal frontend to open edit modal for review
                }), 200
            except json.JSONDecodeError:
                return jsonify({
                    'success': True,
                    'type': 'task',
                    'task_info': {
                        'title': text,
                        'description': '',
                        'priority': 'medium',
                        'due_date': None,
                        'status': 'todo',
                        'board_column': 'todo'
                    },
                    'confidence': 0.7,
                    'open_modal': True
                }), 200
        
        else:  # note
            return jsonify({
                'success': True,
                'type': 'note',
                'note_info': {
                    'content': text,
                    'category': 'general'
                },
                'confidence': 0.8
            }), 200
            
    except Exception as e:
        logger.error(f"Error in AI parsing: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'AI parsing failed: {str(e)}'
        }), 500

