"""Web scraping and search functions"""
import re
import requests
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from ddgs import DDGS
from serpapi import Client
from config import SERPAPI_API_KEY, SNOV_CLIENT_ID, SNOV_CLIENT_SECRET
from urllib.parse import urlparse


def extract_contacts_from_text(text_content, html_content=""):
    """Helper to extract email and phone from text content"""
    # Regex for email - improved to catch more variations
    emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text_content + html_content))

    # Comprehensive phone number regex patterns
    phone_patterns = [
        # International format: +1 123-456-7890, +91 9876543210
        r'\+?\d{1,4}[\s\-\.]?\(?\d{1,4}\)?[\s\-\.]?\d{1,4}[\s\-\.]?\d{1,4}[\s\-\.]?\d{1,4}',
        # US format: (123) 456-7890, 123-456-7890, 123.456.7890
        r'\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4}',
        # Indian format: +91 9876543210, 09876543210
        r'\+?91[\s\-\.]?\d{10}',
        # UK format: +44 20 1234 5678
        r'\+?44[\s\-\.]?\d{2,4}[\s\-\.]?\d{3,4}[\s\-\.]?\d{3,4}',
        # General international: +XX XXXXXXXXXX
        r'\+?\d{2,4}[\s\-\.]?\d{6,12}',
        # Simple 10+ digit numbers
        r'\d{10,15}',
        # Mobile numbers with country codes
        r'\+?\d{1,4}[\s\-\.]?\d{10}',
    ]

    phones = set()
    for pattern in phone_patterns:
        found_phones = re.findall(pattern, text_content)
        phones.update(found_phones)

    # Clean and validate phone numbers
    cleaned_phones = []
    for phone in phones:
        cleaned = re.sub(r'\s+', '', phone)
        cleaned = re.sub(r'[\(\)]', '', cleaned)
        digits_only = re.sub(r'\D', '', cleaned)
        if len(digits_only) >= 7 and len(digits_only) <= 15:
            cleaned_phones.append(cleaned)

    # Filter out common false positives (images, extensions)
    valid_emails = [e for e in emails if not e.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.js', '.css'))]

    # Extract names - look for common name patterns
    name_patterns = [
        r'(?:Contact|Name|Sales|Manager|Director|CEO|Founder|Owner)[\s:]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*-\s*(?:CEO|CTO|CFO|COO|Manager|Director|Sales|Marketing|Founder|Owner)',
        r'\b([A-Z][a-z]{1,15}\s+[A-Z][a-z]{1,15})\b(?!\s*[:-]\s*(?:Street|St|Avenue|Ave|Road|Rd|Email|Phone|Contact|Information|Director|Manager|Sales|CEO|CTO|CFO|COO))',
    ]

    names = set()
    for pattern in name_patterns:
        found_names = re.findall(pattern, text_content, re.IGNORECASE)
        names.update(found_names)

    # Clean and validate names
    cleaned_names = []
    for name in names:
        name = name.strip()
        if (3 <= len(name) <= 30 and re.search(r'[A-Za-z]', name) and
            re.match(r'^[A-Z][a-z]+\s+[A-Z][a-z]+$', name) and
            not any(word in name.lower() for word in ['street', 'avenue', 'road', 'email', 'phone', 'contact', 'information', 'director', 'manager', 'sales', 'tam', 'nadu', 'com', 'for', 'inquiries'])):
            cleaned_names.append(name.title())

    # Extract addresses - look for common address patterns
    address_patterns = [
        r'\d+\s+[A-Za-z0-9\s,.-]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Place|Pl|Court|Ct)\s*,?\s*[A-Za-z\s]+,?\s*\d{5}',
        r'P\.?O\.?\s*Box\s+\d+[A-Za-z0-9\s,.-]*',
        r'[A-Za-z\s]+,?\s*[A-Z]{2}\s+\d{5}',
        r'\d+[A-Za-z0-9\s,.-]+,\s*[A-Za-z\s]+,\s*[A-Za-z\s]+\s*\d{4,6}',
    ]

    addresses = set()
    for pattern in address_patterns:
        found_addresses = re.findall(pattern, text_content, re.IGNORECASE)
        addresses.update(found_addresses)

    # Clean addresses
    cleaned_addresses = []
    for addr in addresses:
        addr = addr.strip()
        if len(addr) > 10 and len(addr) < 200:
            cleaned_addresses.append(addr)

    return list(valid_emails), list(cleaned_phones), list(cleaned_addresses), list(cleaned_names)


def extract_contact_info(url):
    """Helper to scrape email and phone from a website using Playwright (Headless Browser)"""
    print(f"Scraping {url} with Playwright...")

    # Validate and clean URL
    if not url or not url.startswith(('http://', 'https://')):
        print(f"Invalid URL: {url}")
        return [], [], [], []

    # Remove any trailing garbage from URL
    url = url.split(' ')[0].split('\n')[0].split('\t')[0].strip()

    try:
        with sync_playwright() as p:
            # Launch browser with additional options for better compatibility
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu'
                ]
            )

            # Create context with realistic User-Agent to avoid blocking
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 720},
                ignore_https_errors=True
            )

            # Set longer timeout and add retry logic
            max_retries = 2
            for attempt in range(max_retries + 1):
                try:
                    page = context.new_page()
                    page.goto(url, timeout=15000, wait_until="domcontentloaded")
                    text = page.text_content()
                    content = page.content()
                    break
                except Exception as nav_err:
                    if attempt == max_retries:
                        print(f"Failed to load {url} after {max_retries + 1} attempts")
                        browser.close()
                        return [], [], [], []
                    print(f"Retry {attempt + 1}: {nav_err}")

            browser.close()

            # Extract contacts from page content
            emails, phones, addresses, names = extract_contacts_from_text(text, content)
            print(f"Found {len(emails)} emails, {len(phones)} phones, {len(addresses)} addresses, {len(names)} names")
            
            return emails, phones, addresses, names

    except Exception as e:
        print(f"Playwright Scraping error for {url}: {e}")
        return [], [], [], []


def search_with_serpapi(query, max_results=5):
    """Search with SerpApi (Google)"""
    if not SERPAPI_API_KEY:
        return []
    print(f"Performing search with SerpApi: {query}")
    try:
        client = Client(api_key=SERPAPI_API_KEY)
        results = client.search(q=query, engine="google", num=max_results)
        organic_results = results.get("organic_results", [])
        # Adapt SerpApi results to the format of DDGS results
        adapted_results = []
        for r in organic_results:
            adapted_results.append({
                'title': r.get('title'),
                'href': r.get('link'),
                'body': r.get('snippet')
            })
        return adapted_results
    except Exception as e:
        print(f"SerpApi query failed: {e}")
        return []


def search_the_web(query, max_results=5):
    """Optimized web search using SerpApi as primary engine since API key is available."""
    all_results = []
    seen_links = set()

    # Primary: Use SerpApi if key is available (more reliable and comprehensive)
    if SERPAPI_API_KEY:
        try:
            print(f"Performing search with SerpApi: {query}")
            results = search_with_serpapi(query, max_results=max_results)
            print(f"SerpApi search returned {len(results)} results.")
            for r in results:
                link = r.get('href', '')
                if link and link not in seen_links:
                    all_results.append(r)
                    seen_links.add(link)
        except Exception as e:
            print(f"SerpApi query failed: {e}")

    # Fallback: Use DDGS if SerpApi fails or not enough results
    if len(all_results) < max_results:
        try:
            print(f"Fallback: Performing search with DDGS: {query}")
            results = DDGS().text(query, max_results=max_results - len(all_results))
            print(f"DDGS search returned {len(results)} additional results.")
            for r in results:
                link = r.get('href', '')
                if link and link not in seen_links:
                    all_results.append(r)
                    seen_links.add(link)
        except Exception as e:
            print(f"DDGS query failed: {e}")

    return all_results


def get_snov_token():
    """Get access token from Snov.io"""
    if not SNOV_CLIENT_ID or not SNOV_CLIENT_SECRET:
        print("Snov.io credentials missing")
        return None
    
    try:
        url = "https://api.snov.io/v1/oauth/access_token"
        data = {
            'grant_type': 'client_credentials',
            'client_id': SNOV_CLIENT_ID,
            'client_secret': SNOV_CLIENT_SECRET
        }
        response = requests.post(url, data=data)
        response.raise_for_status()
        return response.json().get('access_token')
    except Exception as e:
        print(f"Error getting Snov.io token: {e}")
        return None


def search_snov_domain(domain):
    """Search for emails in a domain using Snov.io with fallback methods
    
    Tries multiple methods:
    1. Snov.io v2 API (POST)
    2. Snov.io v1 API fallback
    3. Direct website scraping (if Snov fails)
    """
    # Clean domain: remove http, https, www, and trailing slashes
    domain = domain.lower().strip()
    if domain.startswith('http'):
        domain = urlparse(domain).netloc
    if domain.startswith('www.'):
        domain = domain[4:]
    domain = domain.split('/')[0]
    
    print(f"\n🔍 DOMAIN SEARCH INITIATED FOR: {domain}")
    print(f"{'='*60}")
    
    # Try Snov.io first
    leads = search_snov_domain_api(domain)
    
    if leads and len(leads) > 0:
        print(f"✅ SUCCESS: Snov.io found {len(leads)} emails")
        return leads
    
    print(f"⚠️  Snov.io returned 0 results, trying direct extraction...")
    print(f"{'='*60}")
    
    # If Snov fails, try direct extraction from website
    direct_leads = extract_domain_emails_direct(domain)
    
    if direct_leads and len(direct_leads) > 0:
        print(f"✅ SUCCESS: Direct extraction found {len(direct_leads)} emails")
        return direct_leads
    
    print(f"⚠️  Both methods returned 0 results for {domain}")
    print(f"{'='*60}")
    
    # Return empty list (not None) to maintain consistency
    return []


def search_snov_domain_api(domain):
    """Call Snov.io API to search for domain emails"""
    token = get_snov_token()
    if not token:
        print("❌ Failed to get Snov token - cannot call API")
        return []
    
    try:
        # Try v2 endpoint first (latest)
        url = "https://api.snov.io/v2/domain-emails"
        headers = {'Authorization': f'Bearer {token}'}
        
        # Try with POST request (sometimes more reliable than GET)
        payload = {
            'domain': domain,
            'limit': 100,
        }
        
        print(f"📤 Calling Snov.io API v2 with domain: {domain}")
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        print(f"📥 Snov API response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"⚠️ Snov API v2 returned status {response.status_code}: {response.text[:200]}")
            # Try fallback endpoint
            return search_snov_domain_api_fallback(domain, token)
        
        data = response.json()
        print(f"DEBUG: Full Snov response structure: {list(data.keys())}")
        
        # Handle various response formats from Snov.io
        leads = []
        
        # Format 1: emails array at root level
        if 'emails' in data and isinstance(data['emails'], list):
            emails_data = data['emails']
            print(f"✅ Snov returned {len(emails_data)} emails (format: root level)")
            for item in emails_data:
                if isinstance(item, dict):
                    leads.append({
                        'email': item.get('email', ''),
                        'name': f"{item.get('firstName', '')} {item.get('lastName', '')}".strip() or item.get('name', ''),
                        'position': item.get('position', '') or item.get('title', ''),
                        'phone': item.get('phone', ''),
                        'company': domain,
                        'source': 'Snov.io',
                        'method': 'v2 API'
                    })
                elif isinstance(item, str):
                    leads.append({'email': item, 'company': domain, 'source': 'Snov.io'})
        
        # Format 2: data.emails (nested)
        elif 'data' in data and isinstance(data['data'], dict) and 'emails' in data['data']:
            emails_data = data['data']['emails']
            print(f"✅ Snov returned {len(emails_data)} emails (format: nested in data)")
            for item in emails_data:
                if isinstance(item, dict):
                    leads.append({
                        'email': item.get('email', ''),
                        'name': f"{item.get('firstName', '')} {item.get('lastName', '')}".strip() or item.get('name', ''),
                        'position': item.get('position', '') or item.get('title', ''),
                        'company': domain,
                        'source': 'Snov.io',
                        'method': 'v2 API'
                    })
        
        # Format 3: pagination with different structure
        elif 'results' in data:
            emails_data = data['results']
            print(f"✅ Snov returned {len(emails_data)} results (format: results array)")
            for item in emails_data:
                if isinstance(item, dict):
                    leads.append({
                        'email': item.get('email', ''),
                        'name': f"{item.get('firstName', '')} {item.get('lastName', '')}".strip(),
                        'position': item.get('position', '') or item.get('title', ''),
                        'company': domain,
                        'source': 'Snov.io',
                        'method': 'v2 API'
                    })
        
        else:
            print(f"⚠️ Snov returned data but no recognized email format. Keys: {list(data.keys())}")
        
        # Filter out empty emails
        leads = [lead for lead in leads if lead.get('email', '').strip()]
        print(f"✅ Snov API (v2) found {len(leads)} valid email records")
        return leads
        
    except requests.exceptions.Timeout:
        print(f"⏱️ Snov API request timed out")
        return []
    except Exception as e:
        print(f"❌ Snov API (v2) error: {type(e).__name__}: {str(e)[:100]}")
        return []


def search_snov_domain_api_fallback(domain, token):
    """Fallback method for Snov domain search using v1 endpoint"""
    try:
        print(f"🔄 Trying Snov.io v1 endpoint as fallback")
        url = "https://api.snov.io/v1/get-domain-emails"
        headers = {'Authorization': f'Bearer {token}'}
        
        payload = {
            'domain': domain,
            'limit': 100
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"⚠️ Snov v1 API returned status {response.status_code}")
            return []
        
        data = response.json()
        print(f"DEBUG: Snov v1 response keys: {list(data.keys())}")
        
        leads = []
        emails_data = data.get('emails', []) or data.get('data', {}).get('emails', [])
        
        if emails_data:
            print(f"✅ Snov v1 returned {len(emails_data)} emails")
        
        for item in emails_data:
            if isinstance(item, dict):
                leads.append({
                    'email': item.get('email', ''),
                    'name': f"{item.get('firstName', '')} {item.get('lastName', '')}".strip(),
                    'position': item.get('position', ''),
                    'company': domain,
                    'source': 'Snov.io',
                    'method': 'v1 API'
                })
        
        leads = [lead for lead in leads if lead.get('email', '').strip()]
        print(f"✅ Snov v1 fallback found {len(leads)} valid emails")
        return leads
        
    except Exception as e:
        print(f"❌ Snov v1 fallback failed: {type(e).__name__}: {str(e)[:100]}")
        return []


def extract_domain_emails_direct(domain):
    """Fallback: Extract emails directly from domain website"""
    try:
        print(f"🌐 Attempting direct domain website scraping")
        
        # Ensure domain has protocol
        if not domain.startswith('http'):
            domain_url = f"https://{domain}"
        else:
            domain_url = domain
        
        # Extract domain name for later use
        domain_name = urlparse(domain_url).netloc.replace('www.', '')
        
        print(f"📄 Scraping website: {domain_url}")
        emails, phones, addresses, names = extract_contact_info(domain_url)
        
        leads = []
        for email in emails:
            if email and '@' in email:
                leads.append({
                    'email': email,
                    'company': domain_name,
                    'source': 'Website Scrape',
                    'method': 'Direct extraction'
                })
        
        if leads:
            print(f"✅ Website scraping found {len(leads)} emails")
        else:
            print(f"⚠️ No emails found by website scraping")
        
        return leads
    except Exception as e:
        print(f"⚠️ Website scraping failed: {type(e).__name__}: {str(e)[:100]}")
        return []


def is_listicle(title, url=""):
    """Check if a title or URL looks like a listicle or directory"""
    title_lower = title.lower()
    url_lower = url.lower()
    
    # Listicle patterns in title
    title_patterns = [
        r'\btop\b', r'\blist\b', r'\bbest\b', r'companies\s+in', r'startups\s+in',
        r'agencies\s+in', r'firms\s+in', r'jobs\b', r'directory', r'reviews',
        r'ranking', r'hiring', r'careers', r'guide\b', r'resource\b',
        r'collection\b', r'popular\b'
    ]
    
    if any(re.search(pattern, title_lower) for pattern in title_patterns):
        return True
        
    # Check for titles starting with a number
    if re.match(r'^\d+\s+', title_lower):
        return True
        
    # Directory/Social/Aggregator domains
    excluded_domains = [
        'linkedin.com', 'facebook.com', 'twitter.com', 'instagram.com', 'yelp.com',
        'yellowpages.com', 'justdial.com', 'glassdoor', 'indeed.com', 'naukri.com',
        'wellfound.com', 'angel.co', 'crunchbase.com', 'clutch.co', 'g2.com',
        'capterra.com', 'reddit.com', 'quora.com', 'medium.com', 'builtinchennai.in',
        'getlatka.com', 'f6s.com', 'hoodshub.tech', 'saasboomi.org', 'youtube.com',
        'vimeo.com', 'pinterest.com', 'github.com', 'upwork.com', 'freelancer.com',
        'toptal.com', 'indiamart.com', 'tradeindia.com', 'sulekha.com', 'bark.com',
        'trustpilot.com', 'sortlist.com', 'goodfirms.co', 'designrush.com',
        'themanifest.com', 'upcity.com', 'zoominfo.com', 'apollo.io', 'lusha.com',
        'rocketreach.co', 'hunter.io', 'skrapp.io', 'snov.io'
    ]
    
    if any(domain in url_lower for domain in excluded_domains):
        return True
        
    # Check for deep paths that look like articles or lists
    path_patterns = [
        '/articles/', '/blog/', '/blogs/', '/list/', '/top-', '/best-',
        '/jobs/', '/careers/', '/collections/'
    ]
    
    try:
        parsed_url = urlparse(url)
        if any(pattern in parsed_url.path.lower() for pattern in path_patterns):
            return True
    except:
        pass
        
    return False
