# AI-Powered Smart Add Setup

The Smart Add feature now uses OpenAI's GPT-4o-mini to intelligently parse and structure information from your voice or text input.

## Setup Instructions

### 1. Get an OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the API key (it starts with `sk-`)

### 2. Add API Key to Backend Environment

#### For Render (Production):
1. Go to your Render dashboard
2. Select the `mindflow-backend` service
3. Go to Environment tab
4. Add a new environment variable:
   - **Key**: `OPENAI_API_KEY`
   - **Value**: Your OpenAI API key (e.g., `sk-...`)
5. Save and redeploy

#### For Local Development:
Add to your `.env` file in `mindflow-backend/`:
```
OPENAI_API_KEY=sk-your-api-key-here
```

## How It Works

### For Stakeholders:
When you dictate or type information about a person, the AI will extract:
- **Name**: Full name of the person
- **Company**: Place of work/organization
- **Role/Job Title**: Position (CEO, Manager, etc.)
- **Department**: Department they work in
- **Email**: Email address if mentioned
- **Phone**: Phone number if mentioned
- **Birthday**: Birthday in YYYY-MM-DD format
- **Location**: City/location if mentioned
- **Personal Notes**: History, context, or additional information
- **LinkedIn**: LinkedIn URL if mentioned

### Example Input:
```
"John Smith is the CEO at TechCorp. He's been working there for 5 years. 
His email is john@techcorp.com and phone is 555-1234. 
He's based in San Francisco. We met at the conference last year."
```

### AI Will Extract:
- Name: John Smith
- Company: TechCorp
- Role: CEO
- Email: john@techcorp.com
- Phone: 555-1234
- Location: San Francisco
- Personal Notes: "He's been working there for 5 years. We met at the conference last year."

## Fallback Behavior

If the OpenAI API key is not configured or the API is unavailable, the system will automatically fall back to local regex-based parsing. This ensures the feature always works, even without AI.

## Cost Considerations

- Uses GPT-4o-mini (cost-effective model)
- Only processes text longer than 10 characters
- Typical cost: ~$0.001-0.01 per request
- For 1000 requests: approximately $1-10

## Privacy

- All API calls are made server-side
- Your API key is stored securely in environment variables
- No data is stored by OpenAI beyond the API call
- All extracted information is stored in your own database

