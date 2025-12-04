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
        client = OpenAI(api_key=OPENAI_API_KEY)
        logger.info("OpenAI client initialized")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {str(e)}")
        return None

@ai_parser_bp.route('/ai/parse-content', methods=['POST'])
@jwt_required()
def parse_content():
    """Use AI to parse and structure content from text input"""
    try:
        client = get_openai_client()
        if not client:
            return jsonify({
                'success': False,
                'error': 'AI parsing not available. OPENAI_API_KEY not configured.'
            }), 503
        data = request.get_json()
        text = data.get('text', '').strip()
        
        if not text:
            return jsonify({
                'success': False,
                'error': 'Text input is required'
            }), 400
        
        # Determine content type first
        type_prompt = f"""Analyze the following text and determine if it's about:
1. A task/to-do item - something that needs to be done, an action item, a reminder
2. A person/stakeholder/contact - information about a person, someone's name, contact details, someone you met or know
3. A general note - any other information, thoughts, observations, or general notes

IMPORTANT: If the text mentions a person's name, contact information, role, company, or any personal details, it should be classified as "stakeholder" even if it also contains other information.

Text: "{text}"

Respond with ONLY one word: "task", "stakeholder", or "note"
"""
        
        type_response = get_openai_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a content classifier. Respond with only one word."},
                {"role": "user", "content": type_prompt}
            ],
            temperature=0.3,
            max_tokens=10
        )
        
        content_type = type_response.choices[0].message.content.strip().lower()
        
        # If it's a stakeholder, extract detailed information
        if content_type == 'stakeholder':
            extraction_prompt = f"""Extract structured information from the following text about a person/contact.
Pay special attention to patterns like "Name, Company Role" or "Name at Company" or "Name - Role at Company".

Return a JSON object with the following fields (use null for missing information):
- name: Full name of the person (first and last name, including special characters)
- company: Company or organization they work for (extract company names even if abbreviated)
- role: Job title or role (e.g., "CEO", "Manager", "Head of Product", "ML Engineer", "Software Engineer")
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

Text: "{text}"

Return ONLY valid JSON, no additional text or explanation.
"""
            
            extraction_response = get_openai_client().chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a data extraction assistant. Extract information and return ONLY valid JSON."},
                    {"role": "user", "content": extraction_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            try:
                extracted_data = json.loads(extraction_response.choices[0].message.content)
                
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
            
            task_response = get_openai_client().chat.completions.create(
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

