from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
import os
import logging
import requests

linkedin_bp = Blueprint('linkedin', __name__)
logger = logging.getLogger(__name__)

@linkedin_bp.route('/linkedin/fetch-profile', methods=['POST'])
@jwt_required()
def fetch_linkedin_profile():
    """
    Fetch LinkedIn profile information for a person.
    Can use LinkedIn URL, name + company, or other identifiers.
    """
    try:
        data = request.get_json()
        linkedin_url = data.get('linkedin_url', '').strip()
        name = data.get('name', '').strip()
        company = data.get('company', '').strip()
        
        if not linkedin_url and not name:
            return jsonify({
                'success': False,
                'error': 'Either linkedin_url or name is required'
            }), 400
        
        # Try to use RapidAPI LinkedIn scraper if available
        RAPIDAPI_KEY = os.environ.get('RAPIDAPI_KEY')
        RAPIDAPI_HOST = os.environ.get('RAPIDAPI_LINKEDIN_HOST', 'linkedin-api8.p.rapidapi.com')
        
        if RAPIDAPI_KEY and linkedin_url:
            try:
                # Extract LinkedIn username from URL
                import re
                username_match = re.search(r'linkedin\.com/in/([^/?]+)', linkedin_url)
                if username_match:
                    username = username_match.group(1)
                    
                    url = f"https://{RAPIDAPI_HOST}/person/{username}"
                    headers = {
                        "X-RapidAPI-Key": RAPIDAPI_KEY,
                        "X-RapidAPI-Host": RAPIDAPI_HOST
                    }
                    
                    response = requests.get(url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        profile_data = response.json()
                        
                        # Map API response to our stakeholder format
                        extracted_info = {
                            'name': profile_data.get('fullName') or profile_data.get('name') or name,
                            'company': profile_data.get('currentCompany') or profile_data.get('company') or company,
                            'role': profile_data.get('headline') or profile_data.get('title') or None,
                            'job_title': profile_data.get('headline') or profile_data.get('title') or None,
                            'location': profile_data.get('location') or None,
                            'linkedin_url': linkedin_url,
                            'email': profile_data.get('email') or None,
                            'phone': profile_data.get('phone') or None,
                            'personal_notes': profile_data.get('summary') or None,
                            'education': profile_data.get('education') or None,
                            'experience': profile_data.get('experience') or None
                        }
                        
                        return jsonify({
                            'success': True,
                            'stakeholder_info': extracted_info
                        }), 200
            except Exception as e:
                logger.warning(f"RapidAPI LinkedIn fetch failed: {str(e)}")
        
        # Fallback: Use web scraping approach (simpler, no API key needed)
        # Note: This is a basic implementation. For production, consider using a proper LinkedIn API service
        if linkedin_url:
            try:
                # For now, return a structured response indicating we need manual input
                # In production, you could use selenium or playwright to scrape LinkedIn
                return jsonify({
                    'success': False,
                    'error': 'LinkedIn API not configured. Please set RAPIDAPI_KEY environment variable.',
                    'message': 'To enable LinkedIn profile fetching, configure RapidAPI LinkedIn API key in environment variables.'
                }), 503
            except Exception as e:
                logger.error(f"LinkedIn scraping failed: {str(e)}")
        
        # If we have name and company, try to construct a search
        if name and company:
            return jsonify({
                'success': False,
                'error': 'LinkedIn API not configured',
                'message': f'To fetch LinkedIn data for {name} at {company}, please provide a LinkedIn URL or configure the LinkedIn API.'
            }), 503
        
        return jsonify({
            'success': False,
            'error': 'Unable to fetch LinkedIn profile. Please provide a LinkedIn URL or configure LinkedIn API.'
        }), 400
        
    except Exception as e:
        logger.error(f"Error fetching LinkedIn profile: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'Failed to fetch LinkedIn profile: {str(e)}'
        }), 500

