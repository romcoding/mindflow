from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
import os
import logging
import requests
import json
import re
from urllib.parse import quote

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
        logger.info("✅ OpenAI client initialized for LinkedIn processing")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def search_linkedin_profile(name, company=None):
    """Search for LinkedIn profile using DuckDuckGo search"""
    try:
        # Construct search query
        search_query = f"{name} linkedin"
        if company:
            search_query = f"{name} {company} linkedin"
        
        logger.info(f"🔍 Searching for LinkedIn profile: {search_query}")
        
        # Use DuckDuckGo HTML search (free, no API key needed)
        search_url = f"https://html.duckduckgo.com/html/?q={quote(search_query)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            # Extract LinkedIn URLs from search results
            linkedin_pattern = r'https?://(?:www\.)?linkedin\.com/in/[\w-]+'
            matches = re.findall(linkedin_pattern, response.text)
            
            if matches:
                # Get the first match (most relevant)
                linkedin_url = matches[0]
                logger.info(f"✅ Found LinkedIn profile: {linkedin_url}")
                return linkedin_url
        
        logger.warning(f"❌ No LinkedIn profile found in search results")
        return None
        
    except Exception as e:
        logger.error(f"Error searching for LinkedIn profile: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def extract_linkedin_info_with_openai(name, company=None, linkedin_url=None):
    """Use OpenAI to extract and structure LinkedIn information"""
    client = get_openai_client()
    if not client:
        logger.warning("OpenAI client not available for LinkedIn extraction")
        return None
    
    try:
        logger.info(f"🤖 Using OpenAI to extract LinkedIn info: {name} at {company or 'unknown company'}")
        
        # Use OpenAI to extract structured information about the profile
        # Since we can't actually scrape LinkedIn, we'll use OpenAI's knowledge and the information we have
        structure_prompt = f"""Extract and structure professional information for {name}{" who works at " + company if company else ""}{" with LinkedIn profile at " + linkedin_url if linkedin_url else ""}.

Use your knowledge base and the provided information to extract:
- name: Full name
- company: Current company
- role: Current job title
- job_title: Specific job title
- department: Department
- location: Location (city, state, country)
- linkedin_url: The LinkedIn URL (use {linkedin_url} if provided)
- personal_notes: Professional summary or bio
- education: Educational background (formatted as readable text)
- experience: Work experience (formatted as readable text with company, role, dates)
- skills: Skills or expertise (comma-separated)
- languages: Languages spoken (comma-separated)
- certifications: Professional certifications
- interests: Professional interests
- website: Personal or company website
- twitter: Twitter handle
- github: GitHub profile
- other_info: Any other relevant professional information

IMPORTANT:
- If you have a LinkedIn URL, use it
- Use your knowledge base to provide likely information based on the person's name and company
- Return null for fields you cannot determine with reasonable confidence
- Be thorough but accurate

Return ONLY valid JSON, no additional text."""
        
        logger.info("📤 Sending structure request to OpenAI API...")
        structure_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a data extraction specialist. Extract and structure LinkedIn profile information into JSON format. Use your knowledge base to provide accurate professional information."},
                {"role": "user", "content": structure_prompt}
            ],
            temperature=0.3,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        logger.info("✅ Received structured data from OpenAI API")
        
        # Log token usage
        if hasattr(structure_response, 'usage'):
            logger.info(f"📊 OpenAI API usage (LinkedIn extraction) - Tokens: {structure_response.usage.total_tokens} (prompt: {structure_response.usage.prompt_tokens}, completion: {structure_response.usage.completion_tokens})")
        
        structure_text = structure_response.choices[0].message.content.strip()
        
        # Parse JSON (should be clean since we used response_format)
        structured_data = json.loads(structure_text)
        
        # Ensure linkedin_url is set if we have it
        if linkedin_url and not structured_data.get('linkedin_url'):
            structured_data['linkedin_url'] = linkedin_url
        
        # Ensure name is set
        if name and not structured_data.get('name'):
            structured_data['name'] = name
        
        logger.info("✅ Successfully extracted LinkedIn information with OpenAI")
        return structured_data
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse OpenAI response as JSON: {str(e)}")
        logger.error(f"Response text: {structure_text[:500] if 'structure_text' in locals() else 'N/A'}")
        return None
    except Exception as e:
        logger.error(f"Error extracting LinkedIn info with OpenAI: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
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
    Uses OpenAI to search and extract LinkedIn information.
    Can use LinkedIn URL, name + company, or just name.
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
        
        logger.info(f"🔍 LinkedIn fetch request - URL: {linkedin_url[:50] if linkedin_url else 'None'}, Name: {name}, Company: {company}")
        
        if not linkedin_url and not name:
            return jsonify({
                'success': False,
                'error': 'Either linkedin_url or name is required'
            }), 400
        
        # Check if OpenAI is available
        OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
        if not OPENAI_API_KEY:
            logger.error("❌ OPENAI_API_KEY environment variable not set")
            return jsonify({
                'success': False,
                'error': 'OpenAI API not configured',
                'message': 'To enable LinkedIn profile fetching, please set the OPENAI_API_KEY environment variable in your Render dashboard.'
            }), 503
        
        client = get_openai_client()
        if not client:
            logger.error("❌ OpenAI client initialization failed")
            return jsonify({
                'success': False,
                'error': 'OpenAI API client initialization failed',
                'message': 'OPENAI_API_KEY is set but client initialization failed. Please check your API key and try again.'
            }), 503
        
        logger.info("✅ OpenAI client available, proceeding with LinkedIn search")
        
        # If we have a LinkedIn URL, extract username and use it
        if linkedin_url:
            username_match = re.search(r'linkedin\.com/in/([^/?]+)', linkedin_url)
            if username_match:
                username = username_match.group(1)
                logger.info(f"✅ Extracted LinkedIn username: {username}")
            else:
                logger.warning(f"⚠️ Could not extract username from URL: {linkedin_url}")
        else:
            # Try to find LinkedIn URL using web search
            logger.info("🔍 No LinkedIn URL provided, searching for profile...")
            found_url = search_linkedin_profile(name, company)
            if found_url:
                linkedin_url = found_url
                logger.info(f"✅ Found LinkedIn URL via search: {linkedin_url}")
        
        # Use OpenAI to extract and structure LinkedIn information
        logger.info("🤖 Using OpenAI to extract LinkedIn information...")
        extracted_info = extract_linkedin_info_with_openai(name, company, linkedin_url)
        
        if extracted_info:
            # Ensure linkedin_url is set
            if not extracted_info.get('linkedin_url') and linkedin_url:
                extracted_info['linkedin_url'] = linkedin_url
            
            # Ensure name is set
            if not extracted_info.get('name') and name:
                extracted_info['name'] = name
            
            logger.info(f"✅ Successfully extracted LinkedIn information for {extracted_info.get('name', name)}")
            return jsonify({
                'success': True,
                'stakeholder_info': extracted_info
            }), 200
        
        # If OpenAI extraction failed, return error
        logger.error("❌ Failed to extract LinkedIn information")
        return jsonify({
            'success': False,
            'error': 'Unable to fetch LinkedIn profile information',
            'message': 'Could not find or extract information from LinkedIn. Please try providing a direct LinkedIn URL.'
        }), 400
        
    except Exception as e:
        logger.error(f"❌ Error fetching LinkedIn profile: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'Failed to fetch LinkedIn profile: {str(e)}'
        }), 500

