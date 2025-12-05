from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
import os
import logging
import requests
import json

linkedin_bp = Blueprint('linkedin', __name__)
logger = logging.getLogger(__name__)

def get_openai_client():
    """Get OpenAI client for processing LinkedIn data"""
    try:
        OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
        if not OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY not set - LinkedIn data will not be processed with AI")
            return None
        
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        return client
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {str(e)}")
        return None

def process_linkedin_data_with_ai(raw_data, name=None, company=None):
    """Use OpenAI to structure and extract all relevant information from LinkedIn data"""
    client = get_openai_client()
    if not client:
        return None
    
    try:
        # Convert raw data to a readable text format
        data_text = json.dumps(raw_data, indent=2) if isinstance(raw_data, dict) else str(raw_data)
        
        prompt = f"""Extract and structure all relevant information from this LinkedIn profile data into a standardized format.

Raw LinkedIn Data:
{data_text}

Extract and return a JSON object with the following fields (use null for missing information):
- name: Full name (first and last name, properly capitalized)
- company: Current company or organization
- role: Current job title or role
- job_title: Specific job title (same as role if role is a full job title)
- department: Department they work in
- location: City, state, country (formatted nicely)
- email: Email address if available
- phone: Phone number if available
- linkedin_url: LinkedIn profile URL
- personal_notes: Professional summary, bio, or about section (formatted as a paragraph)
- education: List of educational institutions and degrees (formatted as a readable string)
- experience: List of work experience (formatted as a readable string with company, role, and dates)
- skills: List of skills or expertise areas (comma-separated)
- languages: Languages spoken (comma-separated)
- certifications: Professional certifications (formatted as a readable string)
- interests: Professional interests or hobbies mentioned
- birthday: Birthday if mentioned (YYYY-MM-DD format)
- website: Personal or company website URL
- twitter: Twitter handle or URL
- github: GitHub profile URL
- other_info: Any other relevant professional information

IMPORTANT:
- Clean and format all text properly (remove extra whitespace, fix capitalization)
- Extract dates from experience/education and format them nicely
- Combine related information intelligently
- If the raw data has nested structures (like experience array), flatten and format them as readable text
- Be thorough - extract all available information

Return ONLY valid JSON, no additional text or explanation.
"""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a data extraction specialist. Extract and structure information from LinkedIn profiles into JSON format."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Try to parse JSON from the response
        # Sometimes the response might have markdown code blocks
        if result_text.startswith('```'):
            # Extract JSON from code block
            result_text = result_text.split('```')[1]
            if result_text.startswith('json'):
                result_text = result_text[4:]
            result_text = result_text.strip()
        
        extracted_data = json.loads(result_text)
        logger.info("✅ Successfully processed LinkedIn data with AI")
        return extracted_data
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response as JSON: {str(e)}")
        logger.error(f"Response text: {result_text[:500]}")
        return None
    except Exception as e:
        logger.error(f"Error processing LinkedIn data with AI: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

@linkedin_bp.route('/linkedin/fetch-profile', methods=['POST'])
@jwt_required()
def fetch_linkedin_profile():
    """
    Fetch LinkedIn profile information for a person.
    Can use LinkedIn URL, name + company, or other identifiers.
    Uses OpenAI to structure and extract all relevant information.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required'
            }), 400
        
        linkedin_url = data.get('linkedin_url', '').strip() if data.get('linkedin_url') else ''
        name = data.get('name', '').strip() if data.get('name') else ''
        company = data.get('company', '').strip() if data.get('company') else ''
        
        logger.info(f"LinkedIn fetch request - URL: {linkedin_url[:50] if linkedin_url else 'None'}, Name: {name}, Company: {company}")
        
        if not linkedin_url and not name:
            return jsonify({
                'success': False,
                'error': 'Either linkedin_url or name is required'
            }), 400
        
        # Try to use RapidAPI LinkedIn scraper if available
        RAPIDAPI_KEY = os.environ.get('RAPIDAPI_KEY')
        RAPIDAPI_HOST = os.environ.get('RAPIDAPI_LINKEDIN_HOST', 'linkedin-api8.p.rapidapi.com')
        
        raw_profile_data = None
        
        if RAPIDAPI_KEY and linkedin_url:
            try:
                # Extract LinkedIn username from URL
                import re
                username_match = re.search(r'linkedin\.com/in/([^/?]+)', linkedin_url)
                if username_match:
                    username = username_match.group(1)
                    logger.info(f"Extracted LinkedIn username: {username}")
                    
                    url = f"https://{RAPIDAPI_HOST}/person/{username}"
                    headers = {
                        "X-RapidAPI-Key": RAPIDAPI_KEY,
                        "X-RapidAPI-Host": RAPIDAPI_HOST
                    }
                    
                    logger.info(f"Making request to RapidAPI: {url}")
                    response = requests.get(url, headers=headers, timeout=15)
                    logger.info(f"RapidAPI response status: {response.status_code}")
                    
                    if response.status_code == 200:
                        try:
                            raw_profile_data = response.json()
                            logger.info(f"Successfully fetched LinkedIn data from RapidAPI")
                        except ValueError as e:
                            logger.error(f"Failed to parse RapidAPI response as JSON: {str(e)}")
                            logger.error(f"Response text: {response.text[:500]}")
                            raw_profile_data = None
                    else:
                        logger.warning(f"RapidAPI returned status {response.status_code}: {response.text[:200]}")
                else:
                    logger.warning(f"Could not extract username from LinkedIn URL: {linkedin_url}")
            except requests.exceptions.RequestException as e:
                logger.warning(f"RapidAPI LinkedIn fetch failed (network error): {str(e)}")
            except Exception as e:
                logger.warning(f"RapidAPI LinkedIn fetch failed: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
        
        # Process the raw data with OpenAI if available
        extracted_info = None
        
        if raw_profile_data:
            # Try AI processing first
            ai_processed = process_linkedin_data_with_ai(raw_profile_data, name, company)
            if ai_processed:
                extracted_info = ai_processed
                # Ensure linkedin_url is set
                if not extracted_info.get('linkedin_url') and linkedin_url:
                    extracted_info['linkedin_url'] = linkedin_url
            else:
                # Fallback to manual mapping if AI processing fails
                logger.info("AI processing not available, using manual mapping")
                extracted_info = {
                    'name': raw_profile_data.get('fullName') or raw_profile_data.get('name') or name,
                    'company': raw_profile_data.get('currentCompany') or raw_profile_data.get('company') or company,
                    'role': raw_profile_data.get('headline') or raw_profile_data.get('title') or None,
                    'job_title': raw_profile_data.get('headline') or raw_profile_data.get('title') or None,
                    'location': raw_profile_data.get('location') or None,
                    'linkedin_url': linkedin_url,
                    'email': raw_profile_data.get('email') or None,
                    'phone': raw_profile_data.get('phone') or None,
                    'personal_notes': raw_profile_data.get('summary') or None,
                    'education': json.dumps(raw_profile_data.get('education')) if raw_profile_data.get('education') else None,
                    'experience': json.dumps(raw_profile_data.get('experience')) if raw_profile_data.get('experience') else None
                }
        
        # If we got data, return it
        if extracted_info:
            return jsonify({
                'success': True,
                'stakeholder_info': extracted_info
            }), 200
        
        # If no API key or fetch failed, return helpful error
        if not RAPIDAPI_KEY:
            return jsonify({
                'success': False,
                'error': 'LinkedIn API not configured',
                'message': 'To enable LinkedIn profile fetching, configure RAPIDAPI_KEY environment variable.'
            }), 503
        
        # If we have name and company but no URL, suggest providing URL
        if name and company and not linkedin_url:
            return jsonify({
                'success': False,
                'error': 'LinkedIn URL required',
                'message': f'To fetch LinkedIn data for {name} at {company}, please provide a LinkedIn profile URL.'
            }), 400
        
        # Generic error
        return jsonify({
            'success': False,
            'error': 'Unable to fetch LinkedIn profile',
            'message': 'Please check that the LinkedIn URL is valid and the API is properly configured.'
        }), 400
        
    except Exception as e:
        logger.error(f"Error fetching LinkedIn profile: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'Failed to fetch LinkedIn profile: {str(e)}'
        }), 500

