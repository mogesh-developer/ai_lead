"""AI Agent functions for lead extraction and processing"""
import json
import re
from config import GEMINI_API_KEY, GROQ_API_KEY, get_genai, get_groq

# Lazy load genai
genai = None

def agent_ai_clean_search_results(search_results, ai_service="gemini"):
    """Agent: AI Search Result Cleaner (Filters listicles and extracts official sites)
    
    Args:
        search_results: List of search results from web search
        ai_service: 'gemini' (default) or 'groq' - which AI to use
    """
    print(f"DEBUG: Starting AI clean with {ai_service}. GEMINI_API_KEY set: {bool(GEMINI_API_KEY)}, GROQ_API_KEY set: {bool(GROQ_API_KEY)}")
    
    # Convert search results to a readable string for the AI
    results_text = ""
    for i, r in enumerate(search_results):
        results_text += f"Result {i+1}:\nTitle: {r.get('title')}\nURL: {r.get('href')}\nSnippet: {r.get('body')}\n---\n"

    prompt = f"""You are a lead extraction specialist. Extract business information from search results.

You will receive Google search results. Each result may be:
- Official company website
- List article mentioning companies

FOR EACH COMPANY WEBSITE, EXTRACT:
- company_name
- official_website  
- email (if found)
- phone_number (if found)
- full_address (if found)
- city
- state
- country
- confidence_score: High/Medium/Low

OUTPUT ONLY A JSON ARRAY WITH NO EXTRA TEXT:
[{{"company_name":"","official_website":"","email":null,"phone_number":null,"full_address":null,"city":"","state":"","country":"","confidence_score":""}}]

INPUT:
{results_text}"""
    
    # Primary AI service (user's choice)
    if ai_service == "gemini" and GEMINI_API_KEY:
        try:
            print("DEBUG: Attempting Gemini API for cleaning")
            _genai = get_genai()
            if _genai:
                model = _genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(prompt)
                print(f"DEBUG: Gemini response received, length: {len(response.text)}")
                
                # Extract JSON from response
                json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    print(f"DEBUG: Successfully cleaned with Gemini, found {len(result)} results")
                    return result
                else:
                    print(f"DEBUG: No JSON array found in Gemini response")
            else:
                print("DEBUG: Gemini not available")
        except Exception as e:
            print(f"DEBUG: Gemini Cleaning Error: {type(e).__name__}: {e}")
            print(f"DEBUG: Will attempt fallback...")
    
    elif ai_service == "groq":
        groq_client = get_groq()
        if groq_client:
            try:
                print("DEBUG: Using Groq API for cleaning")
                response = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You are a lead extraction specialist. Extract business leads from search results and return ONLY a valid JSON array, no other text."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1
                )
                
                response_text = response.choices[0].message.content
                print(f"DEBUG: Groq response received, length: {len(response_text)}")
                
                # Extract JSON from response
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    print(f"DEBUG: Successfully cleaned with Groq, found {len(result)} results")
                    return result
                else:
                    print(f"DEBUG: No JSON array found in Groq response")
            except Exception as e:
                print(f"DEBUG: Groq Cleaning Error: {type(e).__name__}: {e}")
                print(f"DEBUG: Will attempt fallback...")
    
    # Fallback to the other AI service
    print(f"DEBUG: Attempting fallback to alternative AI service")
    if ai_service != "groq":
        groq_client = get_groq()
        if groq_client:
            try:
                print("DEBUG: Falling back to Groq API for cleaning")
                response = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You are a lead extraction specialist. Extract business leads from search results and return ONLY a valid JSON array, no other text."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1
                )
                
                response_text = response.choices[0].message.content
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    print(f"DEBUG: Successfully cleaned with Groq fallback, found {len(result)} results")
                    return result
            except Exception as e:
                print(f"DEBUG: Groq fallback error: {e}")
    
    elif ai_service != "gemini" and GEMINI_API_KEY:
        try:
            print("DEBUG: Falling back to Gemini API for cleaning")
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                print(f"DEBUG: Successfully cleaned with Gemini fallback, found {len(result)} results")
                return result
        except Exception as e:
            print(f"DEBUG: Gemini fallback error: {e}")
    
    return {"error": "No AI service available. Please configure GEMINI_API_KEY or GROQ_API_KEY."}


def agent_ai_extract_leads(text, ai_service="gemini"):
    """Agent: AI Lead Extraction Agent (Cleans and aligns pasted data)
    
    Args:
        text: Text to extract leads from
        ai_service: 'gemini' (default) or 'groq' - which AI to use
    """
    print(f"DEBUG: Starting AI extraction with {ai_service}. GEMINI_API_KEY set: {bool(GEMINI_API_KEY)}")
    print(f"DEBUG: GROQ_API_KEY set: {bool(GROQ_API_KEY)}")
    
    # Primary AI service (user's choice)
    if ai_service == "gemini" and GEMINI_API_KEY:
        try:
            prompt = f"""
    Extract business leads from the following text. 
    The text might be messy, copied from search results or websites.
    Extract: Name, Email, Phone, Company, Position, and Website if available.
    
    Text:
    {text}
    
    Return the results as a JSON array of objects. 
    Each object should have keys: 'name', 'email', 'phone', 'company', 'position', 'website'.
    If a field is missing, use an empty string.
    Return ONLY the JSON array, no other text.
    """
            
            _genai = get_genai()
            if not _genai:
                raise Exception("Gemini API not configured")
            model = _genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            print(f"DEBUG: Gemini response received: {response.text[:200]}...")
            
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
            if json_match:
                leads = json.loads(json_match.group(0))
                print(f"DEBUG: Successfully extracted {len(leads)} leads with Gemini")
                return leads
            else:
                print(f"AI Response did not contain JSON array: {response.text}")
                print(f"DEBUG: Will attempt fallback...")
                return []
        except Exception as e:
            print(f"Gemini AI Extraction Error: {e}")
            print(f"DEBUG: Error type: {type(e).__name__}")
            print(f"DEBUG: Will attempt fallback...")
    
    elif ai_service == "groq":
        groq_client = get_groq_client()
        if groq_client:
            try:
                print("DEBUG: Using Groq API for extraction")
                prompt = f"""
    Extract business leads from the following text. 
    The text might be messy, copied from search results or websites.
    Extract: Name, Email, Phone, Company, Position, and Website if available.
    
    Text:
    {text}
    
    Return the results as a JSON array of objects. 
    Each object should have keys: 'name', 'email', 'phone', 'company', 'position', 'website'.
    If a field is missing, use an empty string.
    Return ONLY the JSON array, no other text.
    """
                
                response = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You are a lead extraction specialist. Extract business leads from text and return ONLY a valid JSON array."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1
                )
                
                response_text = response.choices[0].message.content
                print(f"DEBUG: Groq response received: {response_text[:200]}...")
                
                # Extract JSON from response
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if json_match:
                    leads = json.loads(json_match.group(0))
                    print(f"DEBUG: Successfully extracted {len(leads)} leads with Groq")
                    return leads
                else:
                    print(f"Groq response did not contain JSON array: {response_text}")
                    print(f"DEBUG: Will attempt fallback...")
                    return []
            except Exception as e:
                print(f"Groq AI Extraction Error: {e}")
                print(f"DEBUG: Will attempt fallback...")
    
    # Fallback to the other AI service
    print(f"DEBUG: Attempting fallback to alternative AI service")
    if ai_service != "groq":
        groq_client = get_groq_client()
        if groq_client:
            try:
                print("DEBUG: Falling back to Groq API for extraction")
                prompt = f"""
    Extract business leads from the following text. 
    The text might be messy, copied from search results or websites.
    Extract: Name, Email, Phone, Company, Position, and Website if available.
    
    Text:
    {text}
    
    Return the results as a JSON array of objects. 
    Each object should have keys: 'name', 'email', 'phone', 'company', 'position', 'website'.
    If a field is missing, use an empty string.
    Return ONLY the JSON array, no other text.
    """
                
                response = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You are a lead extraction specialist. Extract business leads from text and return ONLY a valid JSON array."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1
                )
                
                response_text = response.choices[0].message.content
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if json_match:
                    leads = json.loads(json_match.group(0))
                    print(f"DEBUG: Successfully extracted {len(leads)} leads with Groq fallback")
                    return leads
            except Exception as e:
                print(f"Groq fallback error: {e}")
    
    elif ai_service != "gemini" and GEMINI_API_KEY:
        try:
            print("DEBUG: Falling back to Gemini API for extraction")
            prompt = f"""
    Extract business leads from the following text. 
    The text might be messy, copied from search results or websites.
    Extract: Name, Email, Phone, Company, Position, and Website if available.
    
    Text:
    {text}
    
    Return the results as a JSON array of objects. 
    Each object should have keys: 'name', 'email', 'phone', 'company', 'position', 'website'.
    If a field is missing, use an empty string.
    Return ONLY the JSON array, no other text.
    """
            
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
            if json_match:
                leads = json.loads(json_match.group(0))
                print(f"DEBUG: Successfully extracted {len(leads)} leads with Gemini fallback")
                return leads
        except Exception as e:
            print(f"Gemini fallback error: {e}")
    
    return {"error": "No AI service available. Please set GEMINI_API_KEY or GROQ_API_KEY."}


def agent_generate_outreach_message(lead, tone="professional", template="default", ai_service="gemini"):
    """Agent: Generate personalized outreach message for a lead
    
    Args:
        lead: dict with {name, company, email, phone, position, industry, pain_points}
        tone: "professional", "casual", "urgent", "friendly"
        template: "email", "linkedin", "whatsapp", "default"
        ai_service: 'gemini' (default) or 'groq' - which AI to use
    
    Returns:
        dict with {subject, message, success, api_used}
    """
    print(f"DEBUG: Generating outreach message for {lead.get('name', 'Unknown')} with {ai_service}")
    
    lead_info = f"""
Lead Name: {lead.get('name', 'Unknown')}
Company: {lead.get('company', 'Unknown')}
Position: {lead.get('position', 'Unknown')}
Industry: {lead.get('industry', 'Unknown')}
Email: {lead.get('email', 'Not provided')}
Phone: {lead.get('phone', 'Not provided')}
Pain Points: {lead.get('pain_points', 'General')}
"""
    
    template_prompt = {
        "email": "Write a professional cold email subject line and body. Format: SUBJECT: ... \\n BODY: ...",
        "linkedin": "Write a LinkedIn connection message introduction. Keep it under 300 characters.",
        "whatsapp": "Write a WhatsApp/SMS outreach message. Keep it casual and under 160 characters.",
        "default": "Write a professional outreach message that can be used for multiple channels."
    }
    
    tone_instruction = {
        "professional": "Use formal, business-like language with proper structure.",
        "casual": "Use friendly, conversational tone without being too formal.",
        "urgent": "Emphasize urgency and create a sense of need to act now.",
        "friendly": "Be warm and approachable, establish personal connection."
    }
    
    prompt = f"""You are an expert sales copywriter specializing in B2B lead outreach.

TONE: {tone_instruction.get(tone, 'professional')}
TEMPLATE: {template_prompt.get(template, 'Write a professional outreach message')}

LEAD INFORMATION:
{lead_info}

Your task: Generate a compelling, personalized outreach message for this lead.
- Reference their company or industry
- Show you've done research
- Focus on value, not features
- Include clear call-to-action
- Keep it concise

Return the response in JSON format:
{{
    "subject": "email subject or message title",
    "message": "the actual outreach message",
    "cta": "call to action (e.g., Schedule a 15min call)",
    "preview": "first 50 characters as preview"
}}
Return ONLY the JSON, no other text."""
    
    # Primary AI service (user's choice)
    if ai_service == "gemini" and GEMINI_API_KEY:
        try:
            print("DEBUG: Attempting Gemini API for outreach message generation")
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                print(f"DEBUG: Successfully generated outreach message with Gemini")
                return {
                    "success": True,
                    "subject": result.get("subject", ""),
                    "message": result.get("message", ""),
                    "cta": result.get("cta", ""),
                    "preview": result.get("preview", ""),
                    "api_used": "gemini"
                }
        except Exception as e:
            print(f"DEBUG: Gemini Outreach Error: {type(e).__name__}: {e}")
            print(f"DEBUG: Will attempt fallback...")
    
    elif ai_service == "groq":
        groq_client = get_groq_client()
        if groq_client:
            try:
                print("DEBUG: Using Groq API for outreach message generation")
                response = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You are an expert B2B sales copywriter. Generate personalized, compelling outreach messages. Return ONLY valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7
                )
                
                response_text = response.choices[0].message.content
                
                # Extract JSON from response
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    print(f"DEBUG: Successfully generated outreach message with Groq")
                    return {
                        "success": True,
                        "subject": result.get("subject", ""),
                        "message": result.get("message", ""),
                        "cta": result.get("cta", ""),
                        "preview": result.get("preview", ""),
                        "api_used": "groq"
                    }
            except Exception as e:
                print(f"DEBUG: Groq Outreach Error: {type(e).__name__}: {e}")
                print(f"DEBUG: Will attempt fallback...")
    
    # Fallback to the other AI service
    print(f"DEBUG: Attempting fallback to alternative AI service")
    if ai_service != "groq" and GEMINI_API_KEY:
        try:
            print("DEBUG: Falling back to Gemini API for outreach message generation")
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    "success": True,
                    "subject": result.get("subject", ""),
                    "message": result.get("message", ""),
                    "cta": result.get("cta", ""),
                    "preview": result.get("preview", ""),
                    "api_used": "gemini"
                }
        except Exception as e:
            print(f"DEBUG: Gemini fallback error: {e}")
    
    elif ai_service != "gemini":
        groq_client = get_groq_client()
        if groq_client:
            try:
                print("DEBUG: Falling back to Groq API for outreach message generation")
                response = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You are an expert B2B sales copywriter. Generate personalized, compelling outreach messages. Return ONLY valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7
                )
                
                response_text = response.choices[0].message.content
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    return {
                        "success": True,
                        "subject": result.get("subject", ""),
                        "message": result.get("message", ""),
                        "cta": result.get("cta", ""),
                        "preview": result.get("preview", ""),
                        "api_used": "groq"
                    }
            except Exception as e:
                print(f"DEBUG: Groq fallback error: {e}")
    
    return {
        "success": False,
        "error": "No AI service available for outreach message generation"
    }


def agent_generate_campaign_strategy(leads_count, industry, objective, ai_service="gemini"):
    """Agent: Generate a campaign strategy for lead outreach
    
    Args:
        leads_count: Number of leads to outreach
        industry: Target industry/vertical
        objective: Campaign objective (e.g., "Schedule demos", "Generate leads")
        ai_service: 'gemini' (default) or 'groq' - which AI to use
    
    Returns:
        dict with campaign strategy and api_used
    """
    print(f"DEBUG: Generating campaign strategy with {ai_service} for {leads_count} leads in {industry}")
    
    prompt = f"""You are an expert sales strategy consultant specializing in B2B lead outreach campaigns.

Create a comprehensive outreach campaign strategy:

CAMPAIGN DETAILS:
- Number of Leads: {leads_count}
- Target Industry: {industry}
- Objective: {objective}

PROVIDE:
1. Campaign Overview: Brief description
2. Target Audience Profile: Who we should focus on
3. Outreach Sequence: Step-by-step outreach plan (email → follow-up → phone)
4. Messaging Strategy: Key talking points and value propositions
5. Timings: Best days/times to outreach
6. Success Metrics: How to measure campaign success
7. Response Handling: How to handle different response types
8. Escalation Path: When to escalate to sales team

Return as JSON:
{{
    "campaign_overview": "...",
    "target_audience": "...",
    "sequence": {{"step_1": "...", "step_2": "...", ...}},
    "messaging_strategy": "...",
    "timings": "...",
    "success_metrics": ["metric1", "metric2", ...],
    "response_handling": "...",
    "escalation_path": "..."
}}

Return ONLY the JSON, no other text."""
    
    # Primary AI service (user's choice)
    if ai_service == "gemini" and GEMINI_API_KEY:
        try:
            print("DEBUG: Attempting Gemini API for campaign strategy")
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                print(f"DEBUG: Successfully generated campaign strategy with Gemini")
                return {
                    "success": True,
                    "strategy": result,
                    "api_used": "gemini"
                }
        except Exception as e:
            print(f"DEBUG: Gemini Campaign Error: {type(e).__name__}: {e}")
            print(f"DEBUG: Will attempt fallback...")
    
    elif ai_service == "groq":
        groq_client = get_groq_client()
        if groq_client:
            try:
                print("DEBUG: Using Groq API for campaign strategy")
                response = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You are a B2B sales strategy expert. Create detailed outreach campaign strategies. Return ONLY valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7
                )
                
                response_text = response.choices[0].message.content
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    print(f"DEBUG: Successfully generated campaign strategy with Groq")
                    return {
                        "success": True,
                        "strategy": result,
                        "api_used": "groq"
                    }
            except Exception as e:
                print(f"DEBUG: Groq Campaign Error: {type(e).__name__}: {e}")
                print(f"DEBUG: Will attempt fallback...")
    
    # Fallback to the other AI service
    print(f"DEBUG: Attempting fallback to alternative AI service")
    if ai_service != "groq" and GEMINI_API_KEY:
        try:
            print("DEBUG: Falling back to Gemini API for campaign strategy")
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    "success": True,
                    "strategy": result,
                    "api_used": "gemini"
                }
        except Exception as e:
            print(f"DEBUG: Gemini fallback error: {e}")
    
    elif ai_service != "gemini":
        groq_client = get_groq_client()
        if groq_client:
            try:
                print("DEBUG: Falling back to Groq API for campaign strategy")
                response = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You are a B2B sales strategy expert. Create detailed outreach campaign strategies. Return ONLY valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7
                )
                
                response_text = response.choices[0].message.content
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    return {
                        "success": True,
                        "strategy": result,
                        "api_used": "groq"
                    }
            except Exception as e:
                print(f"DEBUG: Groq fallback error: {e}")
    
    return {
        "success": False,
        "error": "No AI service available for campaign strategy generation"
    }
