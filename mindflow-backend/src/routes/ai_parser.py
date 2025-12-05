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
            extraction_prompt = f"""Extract structured information from the following text about a person/contact.
This text may come from voice dictation, so be forgiving with spelling and capitalization.

Pay special attention to patterns like "Name, Company Role" or "Name at Company" or "Name - Role at Company".

Return a JSON object with the following fields (use null for missing information):
- name: Full name of the person (first and last name, including special characters)
  * For voice input, correct common mispronunciations (e.g., "Karin" not "Karen", "Christopher" not "Kristopher")
  * Capitalize proper names correctly even if voice recognition didn't
- company: Company or organization they work for (extract company names even if abbreviated or misspelled)
  * For voice input, try to identify company names even if spelled phonetically
  * Common patterns: "Vector8", "Vector Eight", "Vector Ate" all mean the same company
- role: Job title or role (e.g., "CEO", "Manager", "Head of Product", "ML Engineer", "Software Engineer")
  * For voice input, correct common mistakes (e.g., "engineer" not "engineer", "manager" not "manager")
- job_title: Specific job title if mentioned (same as role if role is a full job title)
- department: Department they work in
- email: Email address if mentioned
- phone: Phone number if mentioned
- birthday: Birthday in YYYY-MM-DD format if mentioned
- personal_notes: Any additional context, history, or notes about this person
- location: Location/city if mentioned
- linkedin_url: LinkedIn URL if mentioned
- other_info: Any other relevant information

IMPORTANT: 
- If text is in format "Name, Company Role" (e.g., "Christopher Hörnle, Vector8 ML Engineer"), extract:
  * name: "Christopher Hörnle"
  * company: "Vector8"
  * role/job_title: "ML Engineer"
- If text is in format "Name at Company" or "Name - Role at Company", extract accordingly
- Always try to identify company names and job titles even if they're combined
- For voice-transcribed text, be intelligent about correcting common speech-to-text errors
- Capitalize names and companies properly even if voice recognition didn't

Text: "{text}"

Return ONLY valid JSON, no additional text or explanation.
"""
            
            logger.info("🔍 Step 2: Extracting stakeholder information...")
            extraction_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a data extraction assistant. Extract information and return ONLY valid JSON."},
                    {"role": "user", "content": extraction_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            # Log OpenAI API usage
            if hasattr(extraction_response, 'usage'):
                logger.info(f"📊 OpenAI API usage (extraction) - Tokens: {extraction_response.usage.total_tokens} (prompt: {extraction_response.usage.prompt_tokens}, completion: {extraction_response.usage.completion_tokens})")
            
            try:
                extracted_data = json.loads(extraction_response.choices[0].message.content)
                logger.info(f"📊 Extracted data: {json.dumps(extracted_data, indent=2)}")
                
                # Clean and validate the extracted data
                stakeholder_info = {
                    'name': extracted_data.get('name') or None,
                    'company': extracted_data.get('company') or None,
                    'role': extracted_data.get('role') or extracted_data.get('job_title') or None,
                    'job_title': extracted_data.get('job_title') or extracted_data.get('role') or None,
                    'department': extracted_data.get('department') or None,
                    'email': extracted_data.get('email') or None,
                    'phone': extracted_data.get('phone') or None,
                    'birthday': extracted_data.get('birthday') or None,
                    'location': extracted_data.get('location') or None,
                    'linkedin_url': extracted_data.get('linkedin_url') or None,
                    'personal_notes': extracted_data.get('personal_notes') or text,  # Fallback to original text
                    'other_info': extracted_data.get('other_info') or None
                }
                
                logger.info(f"✅ Final stakeholder_info: {json.dumps(stakeholder_info, indent=2)}")
                
                return jsonify({
                    'success': True,
                    'type': 'stakeholder',
                    'stakeholder_info': stakeholder_info,
                    'confidence': 0.95
                }), 200
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI JSON response: {e}")
                # Fallback to basic extraction
                return jsonify({
                    'success': True,
                    'type': 'stakeholder',
                    'stakeholder_info': {
                        'name': None,
                        'personal_notes': text
                    },
                    'confidence': 0.7
                }), 200
        
        elif content_type == 'task':
            task_prompt = f"""Extract task information from the following text.
Return a JSON object with:
- title: A clear, concise task title
- description: Detailed description or notes
- priority: "low", "medium", "high", or "urgent" based on keywords
- due_date: Due date in YYYY-MM-DD format if mentioned, or null
- status: "todo", "in_progress", "waiting", or "done" based on context

Text: "{text}"

Return ONLY valid JSON, no additional text.
"""
            
            logger.info("🔍 Extracting task information...")
            task_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a task extraction assistant. Return ONLY valid JSON."},
                    {"role": "user", "content": task_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            try:
                task_data = json.loads(task_response.choices[0].message.content)
                return jsonify({
                    'success': True,
                    'type': 'task',
                    'task_info': {
                        'title': task_data.get('title') or text,
                        'description': task_data.get('description') or '',
                        'priority': task_data.get('priority') or 'medium',
                        'due_date': task_data.get('due_date'),
                        'status': task_data.get('status') or 'todo'
                    },
                    'confidence': 0.9
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
                        'status': 'todo'
                    },
                    'confidence': 0.7
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

