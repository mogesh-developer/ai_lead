import os
import json
import pandas as pd
import smtplib
import re
import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from playwright.sync_api import sync_playwright
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify
from flask_cors import CORS
# from flask_apscheduler import APScheduler
import google.generativeai as genai
# # from groq import Groq
# import groq
from dotenv import load_dotenv
from serpapi import Client
import db
import random
import time
from justdial_scraper import JustDialScraper

# Load environment variables
load_dotenv()


app = Flask(__name__)
CORS(app)
# scheduler = APScheduler()

# Initialize DB
db.init_db()

# AI Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"Failed to configure Gemini: {e}")

def optimize_lead_data_with_ai(lead_data):
    """Uses AI to clean and infer missing lead data"""
    if not GEMINI_API_KEY:
        return lead_data
        
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        prompt = f"""
        Analyze and improve this lead data. 
        Input: {json.dumps(lead_data)}
        
        Tasks:
        1. Fix capitalization in Name and Company.
        2. If Company is missing but can be inferred from email domain (e.g. bob@google.com -> Google), fill it.
        3. Format phone number to standard international format if possible.
        4. Return ONLY the valid JSON object with the same keys.
        """
        
        response = model.generate_content(prompt)
        cleaned_json = response.text.strip()
        # Remove markdown code blocks if present
        if cleaned_json.startswith('```json'):
            cleaned_json = cleaned_json[7:-3]
        elif cleaned_json.startswith('```'):
            cleaned_json = cleaned_json[3:-3]
            
        return json.loads(cleaned_json)
    except Exception as e:
        print(f"AI Optimization failed: {e}")
        return lead_data

def agent_ingest_leads(file_path, campaign_id=None):
    """Agent 1: Lead Ingestion Agent"""
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_path)
        else:
            return {"error": "Unsupported file format"}
        
        # Normalize columns
        df.columns = [c.lower().replace(' ', '_') for c in df.columns]
        
        count = 0
        for _, row in df.iterrows():
            # Basic mapping, assuming columns exist
            lead_data = {
                'name': row.get('name', 'Unknown'),
                'email': row.get('email', ''),
                'phone': str(row.get('phone', '')),
                'company': row.get('company', ''),
                'location': row.get('location', ''),
                'source': 'upload',
                'campaign_id': campaign_id
            }
            db.insert_lead(lead_data)
            count += 1
            
        return {"message": f"Successfully ingested {count} leads"}
    except Exception as e:
        return {"error": str(e)}

def agent_verify_lead(lead):
    """Agent 2: Lead Verification Agent (Mock)"""
    # Mock verification
    return True

def scrape_justdial_url(url):
    """Specialized scraper for JustDial business listings"""
    print(f"🔍 Scraping JustDial URL: {url}")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            page.goto(url, timeout=30000)
            page.wait_for_timeout(2000)
            
            # JustDial specific selectors
            company_name = page.title().split('-')[0].strip() or "JustDial Business"
            
            # Look for phone numbers in JustDial specific elements
            phones = []
            phone_selectors = [
                '.tel', '.phone', '.contact-number',
                '[data-phone]', '.mob',
                'span.tel', 'div.tel'
            ]
            
            for selector in phone_selectors:
                try:
                    elements = page.query_selector_all(selector)
                    for element in elements:
                        text = element.inner_text().strip()
                        if text and len(text) >= 7:
                            phones.append(text)
                except:
                    continue
            
            # If no phones found with selectors, try regex on page content
            if not phones:
                content = page.inner_text('body')
                phone_patterns = [r'\d{10}', r'\+91\s*\d{10}', r'\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4}']
                for pattern in phone_patterns:
                    found = re.findall(pattern, content)
                    phones.extend(found)
            
            # Clean and deduplicate phones
            cleaned_phones = list(set([re.sub(r'\D', '', p) for p in phones if len(re.sub(r'\D', '', p)) >= 7]))
            
            browser.close()
            
            leads = []
            if cleaned_phones:
                for phone in cleaned_phones[:3]:  # Limit to 3 phones
                    lead = {
                        'name': f'Contact at {company_name}',
                        'email': '',  # JustDial rarely shows emails
                        'phone': phone,
                        'company': company_name,
                        'location': 'Chennai',  # Extract from URL or page
                        'source': 'justdial_scrape'
                    }
                    # db.insert_lead(lead) # Don't insert yet
                    leads.append(lead)
            
            print(f"✅ JustDial scraping found {len(cleaned_phones)} phones")
            return leads
            
    except Exception as e:
        print(f"❌ JustDial scraping error: {e}")
        return []

def scrape_yellowpages_url(url):
    """Specialized scraper for YellowPages business listings"""
    print(f"🔍 Scraping YellowPages URL: {url}")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            page.goto(url, timeout=30000)
            page.wait_for_timeout(2000)
            
            company_name = page.title().split('-')[0].strip() or "YellowPages Business"
            
            # YellowPages specific selectors
            phones = []
            phone_selectors = [
                '.phone', '.telephone', '.phone-number',
                '[data-track="phone"]', '.track-phone',
                '.primary-phone', '.phone-link'
            ]
            
            for selector in phone_selectors:
                try:
                    elements = page.query_selector_all(selector)
                    for element in elements:
                        text = element.inner_text().strip()
                        if text and len(text) >= 7:
                            phones.append(text)
                except:
                    continue
            
            # Regex fallback
            if not phones:
                content = page.inner_text('body')
                phone_patterns = [r'\d{10}', r'\+?\d{1,3}[\s\-\.]?\d{10}', r'\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4}']
                for pattern in phone_patterns:
                    found = re.findall(pattern, content)
                    phones.extend(found)
            
            cleaned_phones = list(set([re.sub(r'\D', '', p) for p in phones if len(re.sub(r'\D', '', p)) >= 7]))
            
            browser.close()
            
            leads = []
            if cleaned_phones:
                for phone in cleaned_phones[:3]:
                    lead = {
                        'name': f'Contact at {company_name}',
                        'email': '',
                        'phone': phone,
                        'company': company_name,
                        'location': 'Location Unknown',
                        'source': 'yellowpages_scrape'
                    }
                    # db.insert_lead(lead) # Don't insert yet
                    leads.append(lead)
            
            print(f"✅ YellowPages scraping found {len(cleaned_phones)} phones")
            return leads
            
    except Exception as e:
        print(f"❌ YellowPages scraping error: {e}")
        return []



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
        # Remove extra spaces and normalize
        cleaned = re.sub(r'\s+', '', phone)
        cleaned = re.sub(r'[\(\)]', '', cleaned)

        # Basic validation - must have at least 7 digits
        digits_only = re.sub(r'\D', '', cleaned)
        if len(digits_only) >= 7 and len(digits_only) <= 15:
            # Format nicely
            if cleaned.startswith('+'):
                cleaned_phones.append(cleaned)
            elif len(digits_only) == 10:  # Assume US format
                cleaned_phones.append(f"({digits_only[:3]}) {digits_only[3:6]}-{digits_only[6:]}")
            elif len(digits_only) == 12 and digits_only.startswith('91'):  # Indian format
                cleaned_phones.append(f"+91 {digits_only[2:7]} {digits_only[7:]}")
            else:
                cleaned_phones.append(cleaned)

    # Filter out common false positives (images, extensions)
    valid_emails = [e for e in emails if not e.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.js', '.css'))]

    # Extract names - look for common name patterns
    name_patterns = [
        # Common contact name patterns with colons
        r'(?:Contact|Name|Sales|Manager|Director|CEO|Founder|Owner)[\s:]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        # Names followed by titles with dashes
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*-\s*(?:CEO|CTO|CFO|COO|Manager|Director|Sales|Marketing|Founder|Owner)',
        # Simple proper name patterns (First Last) - exclude common words
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
        # Basic validation - reasonable name length, contains letters, not common false positives
        if (3 <= len(name) <= 30 and
            re.search(r'[A-Za-z]', name) and
            re.match(r'^[A-Z][a-z]+\s+[A-Z][a-z]+$', name) and  # Must be First Last format
            not any(word in name.lower() for word in ['street', 'avenue', 'road', 'email', 'phone', 'contact', 'information', 'director', 'manager', 'sales', 'tam', 'nadu', 'com', 'for', 'inquiries'])):
            # Capitalize properly
            cleaned_names.append(name.title())

    # Extract addresses - look for common address patterns
    address_patterns = [
        # Street address patterns
        r'\d+\s+[A-Za-z0-9\s,.-]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Place|Pl|Court|Ct)\s*,?\s*[A-Za-z\s]+,?\s*\d{5}',
        # PO Box patterns
        r'P\.?O\.?\s*Box\s+\d+[A-Za-z0-9\s,.-]*',
        # City, State ZIP patterns
        r'[A-Za-z\s]+,?\s*[A-Z]{2}\s+\d{5}',
        # International address patterns
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
        if len(addr) > 10 and len(addr) < 200:  # Reasonable address length
            cleaned_addresses.append(addr)

    return list(valid_emails), list(cleaned_phones), list(cleaned_addresses), list(cleaned_names)

def extract_contact_info(url):
    """Helper to scrape email and phone from a website using Playwright (Headless Browser)"""
    print(f"Scraping {url} with Playwright...")

    # Validate and clean URL
    if not url or not url.startswith(('http://', 'https://')):
        print(f"Invalid URL: {url}")
        return [], []

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

                    # Navigate with different wait conditions
                    response = page.goto(url, timeout=45000, wait_until="domcontentloaded")

                    if not response or response.status >= 400:
                        print(f"HTTP {response.status if response else 'unknown'} for {url}")
                        page.close()
                        if attempt < max_retries:
                            continue
                        browser.close()
                        return [], [], [], []

                    # Wait for potential JS rendering (e.g. React/Vue apps)
                    page.wait_for_timeout(5000)  # Increased wait time

                    # Try to find contact pages if we're on homepage
                    if url.endswith('/') or '/home' in url or len(url.split('/')) <= 3:
                        contact_urls = []
                        # Look for contact links in the page
                        try:
                            contact_links = page.query_selector_all('a[href*="contact"]')
                            for link in contact_links[:3]:  # Limit to first 3 contact links
                                href = link.get_attribute('href')
                                if href:
                                    if href.startswith('/'):
                                        href = url.rstrip('/') + href
                                    elif not href.startswith('http'):
                                        href = url.rstrip('/') + '/' + href
                                    if href not in contact_urls and href != url:
                                        contact_urls.append(href)
                        except:
                            pass

                        # Scrape contact pages too
                        for contact_url in contact_urls[:2]:  # Limit to 2 contact pages
                            try:
                                page.goto(contact_url, timeout=20000, wait_until="domcontentloaded")
                                page.wait_for_timeout(3000)
                                break  # Use the first working contact page
                            except Exception as e:
                                print(f"Failed to load contact page {contact_url}: {e}")
                                continue

                    # Extract text content
                    text = page.inner_text('body')

                    # Also get HTML for hidden mailto links
                    content = page.content()

                    page.close()
                    break  # Success, exit retry loop

                except Exception as nav_err:
                    print(f"Navigation attempt {attempt + 1} failed for {url}: {nav_err}")
                    try:
                        page.close()
                    except:
                        pass

                    if attempt < max_retries:
                        print(f"Retrying in 2 seconds...")
                        time.sleep(2)
                        continue
                    else:
                        browser.close()
                        return [], [], [], []

            browser.close()

            # Regex for email - improved to catch more variations
            emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text + content))

            # Extract names - look for common name patterns
            name_patterns = [
                # Common contact name patterns with colons
                r'(?:Contact|Name|Sales|Manager|Director|CEO|Founder|Owner)[\s:]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                # Names followed by titles with dashes
                r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*-\s*(?:CEO|CTO|CFO|COO|Manager|Director|Sales|Marketing|Founder|Owner)',
                # Simple proper name patterns (First Last) - exclude common words
                r'\b([A-Z][a-z]{1,15}\s+[A-Z][a-z]{1,15})\b(?!\s*[:-]\s*(?:Street|St|Avenue|Ave|Road|Rd|Email|Phone|Contact|Information|Director|Manager|Sales|CEO|CTO|CFO|COO))',
            ]

            names = set()
            for pattern in name_patterns:
                found_names = re.findall(pattern, text, re.IGNORECASE)
                names.update(found_names)

            # Clean and validate names
            cleaned_names = []
            for name in names:
                name = name.strip()
                # Basic validation - reasonable name length, contains letters, not common false positives
                if (3 <= len(name) <= 30 and
                    re.search(r'[A-Za-z]', name) and
                    re.match(r'^[A-Z][a-z]+\s+[A-Z][a-z]+$', name) and  # Must be First Last format
                    not any(word in name.lower() for word in ['street', 'avenue', 'road', 'email', 'phone', 'contact', 'information', 'director', 'manager', 'sales', 'tam', 'nadu', 'com', 'for', 'inquiries'])):
                    # Capitalize properly
                    cleaned_names.append(name.title())

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
                found_phones = re.findall(pattern, text)
                phones.update(found_phones)

            # Clean and validate phone numbers
            cleaned_phones = []
            for phone in phones:
                # Remove extra spaces and normalize
                cleaned = re.sub(r'\s+', '', phone)
                cleaned = re.sub(r'[\(\)]', '', cleaned)

                # Basic validation - must have at least 7 digits
                digits_only = re.sub(r'\D', '', cleaned)
                if len(digits_only) >= 7 and len(digits_only) <= 15:
                    # Format nicely
                    if cleaned.startswith('+'):
                        cleaned_phones.append(cleaned)
                    elif len(digits_only) == 10:  # Assume US format
                        cleaned_phones.append(f"({digits_only[:3]}) {digits_only[3:6]}-{digits_only[6:]}")
                    elif len(digits_only) == 12 and digits_only.startswith('91'):  # Indian format
                        cleaned_phones.append(f"+91 {digits_only[2:7]} {digits_only[7:]}")
                    else:
                        cleaned_phones.append(cleaned)

            # Filter out common false positives (images, extensions)
            valid_emails = [e for e in emails if not e.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.js', '.css'))]

            # Extract addresses - look for common address patterns
            address_patterns = [
                # Street address patterns
                r'\d+\s+[A-Za-z0-9\s,.-]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Place|Pl|Court|Ct)\s*,?\s*[A-Za-z\s]+,?\s*\d{5}',
                # PO Box patterns
                r'P\.?O\.?\s*Box\s+\d+[A-Za-z0-9\s,.-]*',
                # City, State ZIP patterns
                r'[A-Za-z\s]+,?\s*[A-Z]{2}\s+\d{5}',
                # International address patterns
                r'\d+[A-Za-z0-9\s,.-]+,\s*[A-Za-z\s]+,\s*[A-Za-z\s]+\s*\d{4,6}',
            ]

            addresses = set()
            for pattern in address_patterns:
                found_addresses = re.findall(pattern, text, re.IGNORECASE)
                addresses.update(found_addresses)

            # Clean addresses
            cleaned_addresses = []
            for addr in addresses:
                addr = addr.strip()
                if len(addr) > 10 and len(addr) < 200:  # Reasonable address length
                    cleaned_addresses.append(addr)

            print(f"Found {len(valid_emails)} emails, {len(cleaned_phones)} phones, {len(cleaned_addresses)} addresses, {len(cleaned_names)} names")
            # Remove duplicates and return
            return list(set(valid_emails)), list(set(cleaned_phones)), list(set(cleaned_addresses)), list(set(cleaned_names))

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


def agent_discovery(industry, location):
    """Agent 1.5: Lead Discovery Agent (Real Web Search & Scraping)"""
    print(f"🔍 Searching for {industry} in {location}...")
    
    found_leads = []
    
    # Try multiple query variations optimized for finding contact information
    queries = [
        f'"{industry}" companies in "{location}" contact email phone',
        f'{industry} companies {location} email address contact',
        f'list of {industry} companies in {location} with contact details',
        f'{industry} agencies {location} email phone number',
        f'{industry} firms {location} contact information'
    ]
    
    all_results = []
    seen_links = set()

    try:
        for query in queries:
            results = search_the_web(query, max_results=8)  # Increased from 5 to 8 for more results
            for r in results:
                link = r.get('href', '')
                if link and link not in seen_links:
                    all_results.append(r)
                    seen_links.add(link)
            
            if len(all_results) >= 15:  # Increased threshold
                break
        
        if not all_results:
            print("❌ No results from any search engine. Returning empty list.")
            return []

        print(f"✅ Found {len(all_results)} total raw results.")

        # Filter results to only include relevant ones (contain industry or location in title/href)
        filtered_results = []
        industry_lower = industry.lower()
        location_lower = location.lower()
        
        # Split industry into keywords for broader matching
        industry_keywords = industry_lower.split()
        
        for r in all_results:
            title = r.get('title', '').lower()
            href = r.get('href', '').lower()
            snippet = r.get('body', '').lower()
            
            # Check if any industry keyword is present
            industry_match = any(k in title for k in industry_keywords) or any(k in snippet for k in industry_keywords)
            location_match = location_lower in title or location_lower in snippet
            
            if industry_match or location_match:
                filtered_results.append(r)
        
        if not filtered_results:
            print("⚠️ No strictly relevant results found after filtering. Using top raw results.")
            filtered_results = all_results[:5] # Fallback to top 5 raw results
        else:
            print(f"✅ Filtered down to {len(filtered_results)} relevant results.")

        for i, r in enumerate(filtered_results[:10]):  # Process top 10 filtered results
            print(f"--- Processing result {i+1} ---")
            title = r.get('title', 'Unknown Company')
            link = r.get('href', '')
            snippet = r.get('body', '')
            print(f"Title: {title}")
            print(f"Link: {link}")
            
            # Skip only social media and irrelevant directories
            if any(x in link.lower() for x in ['linkedin.com', 'facebook.com', 'twitter.com', 'instagram.com']):
                print("Skipping social media link.")
                continue
            
            # Skip aggregators and listicles if user wants "official pages"
            # Common patterns for listicles: "top-10", "best-20", "clutch.co", "yelp.com", "justdial.com", "sulekha.com"
            # But wait, user might WANT justdial if they are scraping it specifically. 
            # However, for "Web Search" (Smart Lead Finder), we usually want direct company sites.
            # The user specifically asked to avoid "Top 20" etc.
            
            skip_keywords = ['top-', 'best-', 'list-of', 'directory', 'clutch.co', 'yelp.com', 'sulekha.com', 'justdial.com', 'yellowpages', 'thumbtack', 'upwork', 'fiverr']
            if any(k in link.lower() for k in skip_keywords) or any(k in title.lower() for k in ['top ', 'best ', 'list of ']):
                print(f"Skipping aggregator/listicle: {link}")
                continue

            print(f"Scraping {link}...")
            emails, phones, addresses, names = extract_contact_info(link)
            print(f"Scraping result: {len(emails)} emails, {len(phones)} phones, {len(addresses)} addresses, {len(names)} names")

            # If no email found on page, try to guess from snippet
            email = emails[0] if emails else ''
            phone = phones[0] if phones else ''
            address = addresses[0] if addresses else ''
            name = names[0] if names else ''

            # If we still don't have an email, try to find email in snippet
            if not email:
                snippet_emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', snippet)
                if snippet_emails:
                    email = snippet_emails[0]
                    print(f"Found email in snippet: {email}")

            # Extract company name from title
            company_name = title.split('-')[0].split('|')[0].strip()
            if len(company_name) < 3:
                company_name = "Unknown Company"

            # Create lead if we have either email or phone
            if email or phone:
                # Use extracted name if available, otherwise create a generic one
                contact_name = name if name else f'Contact at {company_name}'
                lead = {
                    'name': contact_name,
                    'email': email,
                    'phone': phone,
                    'company': company_name,
                    'location': location,
                    'source': 'ai_discovery_web'
                }

                # Check if we already have this lead (basic duplicate check)
                existing = db.get_lead_by_email(email) if email else None
                if not existing:
                    # Optimize with AI before returning
                    lead = optimize_lead_data_with_ai(lead)
                    
                    # db.insert_lead(lead) # Don't insert yet, just return
                    found_leads.append(lead)
                    print(f"Found candidate lead: {company_name} - {email or phone}")
                else:
                    print(f"Duplicate lead skipped: {email or phone}")
            else:
                print("No email or phone found for this lead.")
                
    except Exception as e:
        import traceback
        print(f"Discovery Error: {e}")
        traceback.print_exc()
        # Fallback to mock if search fails completely (e.g. rate limits)
        return []
            
    print(f"--- Discovery finished. Found {len(found_leads)} total leads. ---")
    return found_leads

def agent_scrape_specific_url(url):
    """Enhanced Agent: Scrape specific URL for comprehensive lead information"""
    print(f"🚀 STARTING SCRAPING for URL: {url}")
    if 'justdial.com' in url.lower():
        print("🔍 Detected JustDial URL - using specialized scraping")
        return scrape_justdial_url(url)
    elif 'yellowpages.com' in url.lower():
        print("🔍 Detected YellowPages URL - using specialized scraping")
        return scrape_yellowpages_url(url)
    
    # For other URLs, use the main contact info extraction
    try:
        emails, phones, addresses, names = extract_contact_info(url)
        leads = []
        if emails or phones:
            company_name = "Unknown Company"
            try:
                # Try to get company name from URL
                company_name = url.split('/')[2].replace('www.', '').split('.')[0]
            except:
                pass

            contact_name = names[0] if names else f'Contact at {company_name}'
            lead = {
                'name': contact_name,
                'email': emails[0] if emails else '',
                'phone': phones[0] if phones else '',
                'company': company_name,
                'location': addresses[0] if addresses else 'Unknown',
                'source': 'url_scrape'
            }
            # Optimize with AI
            lead = optimize_lead_data_with_ai(lead)
            
            # db.insert_lead(lead) # Don't insert yet
            leads.append(lead)
        
        return leads
    except Exception as e:
        print(f"❌ Scraping failed: {e}")
        return []

def agent_verify_lead(lead):
    """Agent 2: Lead Verification Agent (Mock)"""
    # Mock verification
    return True

    # if not GEMINI_API_KEY:
    #     return True  # Mock verification if no API key
    
    # prompt = f"""
    # Verify the following lead contact information for validity:
    # Name: {lead['name']}
    # Email: {lead['email']}
    # Phone: {lead['phone']}
    # Company: {lead['company']}
    # Location: {lead['location']}
    
    # Check if:
    # 1. Email format is valid
    # 2. Phone number format is reasonable
    # 3. Information appears legitimate
    
    # Return only: VALID or INVALID with a brief reason.
    # """
    
    # try:
    #     model = genai.GenerativeModel('gemini-1.5-flash')  # Gemini 3 Flash equivalent
    #     response = model.generate_content(prompt)
    #     result = response.text.strip().upper()
    #     return "VALID" in result
    # except Exception as e:
    #     print(f"Gemini Verification Error: {e}")
    #     return True  # Default to valid if API fails

def agent_analyze_business(lead):
    """Agent 3: Business Analysis Agent (Real AI)"""
    
    # Fallback to mock if no API key
    if not GEMINI_API_KEY:
        print("⚠️ No Gemini API Key found. Using mock analysis.")
        import random
        company_name = lead.get('company', '').lower()
        location = lead.get('location', '').lower()
        trust_score = 50
        if 'tech' in company_name or 'software' in company_name: trust_score += 20
        if 'ltd' in company_name or 'inc' in company_name: trust_score += 10
        if 'chennai' in location or 'bangalore' in location: trust_score += 15
        trust_score = min(100, max(0, trust_score + random.randint(-10, 10)))
        
        if trust_score > 80: maturity, growth = "Enterprise", "High"
        elif trust_score > 60: maturity, growth = "SMB", "Medium"
        else: maturity, growth = "Startup", "Low"
        
        return {
            "trust_score": trust_score,
            "business_maturity": maturity,
            "growth_potential": growth,
            "reasoning": f"Mock analysis (No API Key). Score: {trust_score}"
        }

    try:
        print(f"🤖 Analyzing business with Gemini: {lead.get('company')}")
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        prompt = f"""
        Analyze this business lead for a B2B service provider (Digital Marketing/Tech Services).
        
        Lead Details:
        Company: {lead.get('company', 'Unknown')}
        Location: {lead.get('location', 'Unknown')}
        Email: {lead.get('email', 'Unknown')}
        Phone: {lead.get('phone', 'Unknown')}
        
        Task:
        1. Estimate 'trust_score' (0-100) based on company name professionalism, location, and contact info quality.
        2. Classify 'business_maturity' as 'Startup', 'SMB', or 'Enterprise'.
        3. Estimate 'growth_potential' as 'Low', 'Medium', or 'High'.
        4. Provide a short 'reasoning' (max 2 sentences).
        
        Return ONLY a valid JSON object with keys: trust_score, business_maturity, growth_potential, reasoning.
        """
        
        response = model.generate_content(prompt)
        cleaned_json = response.text.strip()
        if cleaned_json.startswith('```json'):
            cleaned_json = cleaned_json[7:-3]
        elif cleaned_json.startswith('```'):
            cleaned_json = cleaned_json[3:-3]
            
        analysis = json.loads(cleaned_json)
        
        # Ensure types are correct
        analysis['trust_score'] = int(analysis.get('trust_score', 50))
        
        return analysis
        
    except Exception as e:
        print(f"❌ AI Analysis Failed: {e}")
        # Fallback to mock on error
        return {
            "trust_score": 50,
            "business_maturity": "Unknown",
            "growth_potential": "Unknown",
            "reasoning": f"AI Analysis failed: {str(e)}"
        }

def agent_decide_outreach(analysis):
    """Agent 4: Decision Agent (Mock)"""
    trust_score = analysis.get('trust_score', 0)
    maturity = analysis.get('business_maturity', 'Unknown')
    growth = analysis.get('growth_potential', 'Low')
    
    # Simple decision logic
    if trust_score >= 60:
        return "OUTREACH"
    elif trust_score >= 40 and growth in ['Medium', 'High']:
        return "OUTREACH"
    elif maturity == "Enterprise":
        return "OUTREACH"
    else:
        return "SKIP"

def agent_message_strategy(lead, analysis):
    """Agent 5: Message Strategy Agent (Mock)"""
    maturity = analysis.get('business_maturity', 'SMB')
    trust_score = analysis.get('trust_score', 0)
    
    if maturity == "Enterprise" or trust_score > 80:
        return "professional"
    elif maturity == "SMB" and trust_score > 60:
        return "polite"
    else:
        return "friendly"

def agent_generate_message(lead, strategy="polite"):
    """Agent 6: Message Generation Agent (Real AI with Multi-language Support)"""
    name = lead.get('name', 'Valued Partner')
    company = lead.get('company', 'your company')
    location = lead.get('location', 'Unknown')
    
    # Fallback to mock if no API key
    if not GEMINI_API_KEY:
        if strategy == "professional":
            return f"Dear {name},\n\nI hope this email finds you well. We are a digital marketing agency specializing in helping businesses like {company} grow their online presence.\n\nWe would be interested in discussing how we can support your business objectives.\n\nBest regards,\nMogeshwaran\nDigital Marketing Specialist"
        elif strategy == "friendly":
            return f"Hi {name},\n\nI came across {company} and was impressed by what you do. We're a digital marketing team that helps businesses expand their reach online.\n\nWould love to chat about how we can help {company} grow!\n\nBest,\nMogeshwaran"
        else:  # polite
            return f"Hello {name},\n\nMy name is Mogeshwaran and I work with a digital marketing agency. I noticed {company} and thought we might be able to help with your online marketing needs.\n\nWould you be open to a quick conversation?\n\nThank you,\nMogeshwaran"

    try:
        print(f"🤖 Generating message with Gemini for {company} ({strategy})")
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        prompt = f"""
        Write a cold outreach email for a digital marketing agency.
        
        Recipient: {name} from {company}
        Location: {location}
        Tone: {strategy} (Professional, Polite, or Friendly)
        Goal: Schedule a quick call to discuss marketing services.
        
        Requirements:
        1. Keep it short (under 150 words).
        2. Be personalized to the company/industry if possible.
        3. If the location is in Tamil Nadu (Chennai, Coimbatore, etc.), include a greeting or small phrase in Thanglish (Tamil written in English) to build rapport.
        4. If the location is in a Hindi-speaking region (Delhi, Mumbai, etc.), include a small Hindi phrase in English script.
        5. Otherwise, keep it fully English.
        
        Return ONLY the email body text. No subject line.
        """
        
        response = model.generate_content(prompt)
        return response.text.strip()
        
    except Exception as e:
        print(f"❌ AI Message Generation Failed: {e}")
        return f"Hello {name},\n\nI noticed {company} and thought we might be able to help with your online marketing needs.\n\nWould you be open to a quick conversation?\n\nThank you,\nMogeshwaran"

def agent_send_outreach(lead, message):
    """Agent 7: Outreach Agent (Real SMTP + Mock Fallback)"""
    
    # Try sending real email if credentials exist
    sent_real = False
    if SMTP_EMAIL and SMTP_PASSWORD:
        try:
            msg = MIMEMultipart()
            msg['From'] = SMTP_EMAIL
            msg['To'] = lead['email']
            msg['Subject'] = f"Partnership Opportunity with {lead['company']}"
            msg.attach(MIMEText(message, 'plain'))
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
            sent_real = True
            print(f"REAL EMAIL SENT to {lead['email']}")
        except Exception as e:
            print(f"SMTP Error: {e}. Falling back to mock.")
    
    if not sent_real:
        # Mock sending
        print(f"MOCK EMAIL SENT to {lead['email']}: {message[:50]}...")
        
    db.log_outreach(lead['id'], 'email', message)
    return True

def autonomous_loop():
    """Background task for Autopilot Mode"""
    with app.app_context():
        autopilot = db.get_setting('autopilot')
        if autopilot != 'true':
            return

        print("--- Autopilot Running ---")
        pending_leads = db.get_pending_leads()
        
        for lead in pending_leads:
            if lead['status'] == 'new':
                print(f"Auto-Analyzing lead: {lead['id']}")
                analysis = agent_analyze_business(lead)
                decision = agent_decide_outreach(analysis)
                status = 'analyzed' if decision == 'OUTREACH' else 'skipped'
                db.update_lead_analysis(lead['id'], json.dumps(analysis), analysis.get('trust_score', 0), status)
                
            elif lead['status'] == 'analyzed':
                print(f"Auto-Outreach lead: {lead['id']}")
                # Get analysis for strategy determination
                analysis = json.loads(lead.get('ai_analysis', '{}'))
                strategy = agent_message_strategy(lead, analysis)
                message = agent_generate_message(lead, strategy)
                agent_send_outreach(lead, message)
                
            elif lead['status'] == 'outreach_sent' and lead.get('campaign_id'):
                # Check for drip sequence
                campaign_id = lead['campaign_id']
                sequences = db.get_campaign_sequences(campaign_id)
                current_step = lead.get('current_sequence_step', 0)
                last_outreach = lead.get('last_outreach_at')
                
                # Find next step
                next_step = None
                for seq in sequences:
                    if seq['day_offset'] > current_step: # Assuming current_step stores the day_offset of last sent
                         # Actually, let's store the index or just check day_offset logic
                         # Simplified: current_sequence_step is the index of the last sent sequence. 0 means initial.
                         pass

                # Better logic:
                # current_sequence_step = 0 (Initial sent)
                # We look for a sequence with day_offset > 0
                
                # Let's assume sequences are ordered by day_offset
                # If current_sequence_step is 0, we look for the first follow up (e.g. day 3)
                
                # Find the sequence that corresponds to the *next* step
                # We need to know what "step 1" means. Is it the 1st follow up? Yes.
                
                # Let's say current_sequence_step = 0.
                # We want to find a sequence where day_offset is appropriate.
                
                if not last_outreach:
                    continue
                    
                import datetime
                days_since_last = (datetime.datetime.now() - last_outreach).days
                
                # Find the next sequence to send
                target_seq = None
                for seq in sequences:
                    # If this sequence hasn't been sent yet (we can track this by storing the last sent day_offset in current_sequence_step)
                    # Let's say current_sequence_step stores the day_offset of the last email.
                    # Initial email is day_offset 0.
                    
                    if seq['day_offset'] > lead.get('current_sequence_step', 0):
                        # This is a potential next step
                        # Check if enough time has passed from INITIAL outreach? Or LAST outreach?
                        # Usually drip is "Day 3" means 3 days after start.
                        
                        # We need the date of the FIRST outreach to calculate absolute day offset.
                        # Or we just use relative gaps.
                        
                        # Simple approach: Day 3 means 3 days after the previous step? Or 3 days from start?
                        # Standard is days from start.
                        # But we only have last_outreach_at.
                        
                        # Let's use relative for simplicity in this MVP.
                        # If seq['day_offset'] is 3, it means 3 days after the previous email.
                        
                        if days_since_last >= seq['day_offset']:
                            target_seq = seq
                            break
                
                if target_seq:
                    print(f"Auto-Drip lead: {lead['id']} - Step {target_seq['day_offset']}")
                    # Generate message using template
                    # We can use AI to personalize the template
                    template = target_seq['template_body']
                    # Simple variable substitution
                    message = template.replace('{name}', lead.get('name', 'there')).replace('{company}', lead.get('company', 'your company'))
                    
                    # Send
                    agent_send_outreach(lead, message)
                    
                    # Update state
                    # We use the day_offset as the step indicator
                    db.update_lead_sequence_step(lead['id'], target_seq['day_offset'])
                
        print("--- Autopilot Cycle Complete ---")

def agent_analyze_response(response_text, lead):
    """Agent 8: Response Analysis Agent (Real AI)"""
    
    # Fallback to mock if no API key
    if not GEMINI_API_KEY:
        print("⚠️ No Gemini API Key found. Using mock response analysis.")
        text = response_text.lower()
        if any(word in text for word in ['yes', 'interested', 'sure', 'okay', 'great']):
            return {"interest_level": "high", "sentiment": "positive", "next_action": "continue", "reasoning": "Mock analysis: Positive keywords found."}
        elif any(word in text for word in ['maybe', 'later', 'busy', 'not sure']):
            return {"interest_level": "medium", "sentiment": "neutral", "next_action": "follow_up", "reasoning": "Mock analysis: Neutral keywords found."}
        else:
            return {"interest_level": "low", "sentiment": "negative", "next_action": "stop", "reasoning": "Mock analysis: No positive keywords."}

    try:
        print(f"🤖 Analyzing response with Gemini...")
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        prompt = f"""
        Analyze this email response from a lead.
        
        Lead: {lead.get('name', 'Unknown')} ({lead.get('company', 'Unknown Company')})
        Response Text: "{response_text}"
        
        Task:
        1. Determine 'sentiment' (Positive, Neutral, Negative).
        2. Estimate 'interest_level' (High, Medium, Low).
        3. Recommend 'next_action' (reply_immediately, schedule_meeting, send_info, follow_up_later, do_not_contact).
        4. Provide a short 'reasoning'.
        
        Return ONLY a valid JSON object with keys: sentiment, interest_level, next_action, reasoning.
        """
        
        response = model.generate_content(prompt)
        cleaned_json = response.text.strip()
        if cleaned_json.startswith('```json'):
            cleaned_json = cleaned_json[7:-3]
        elif cleaned_json.startswith('```'):
            cleaned_json = cleaned_json[3:-3]
            
        analysis = json.loads(cleaned_json)
        return analysis
        
    except Exception as e:
        print(f"❌ AI Response Analysis Failed: {e}")
        return {
            "interest_level": "medium",
            "sentiment": "neutral",
            "next_action": "manual_review",
            "reasoning": f"AI Analysis failed: {str(e)}"
        }

def agent_followup_logic(lead, response_analysis, follow_up_count):
    """Agent 9: Follow-up Agent (Mock)"""
    interest_level = response_analysis.get('interest_level', 'low')
    sentiment = response_analysis.get('sentiment', 'neutral')
    
    # Simple logic: continue if interested and under 3 follow-ups
    if interest_level in ['high', 'medium'] and sentiment != 'negative' and follow_up_count < 3:
        return True
    else:
        return False

def agent_targeted_search(location, niche, offering):
    """Agent 1.7: Targeted Lead Finder (Smart Search)"""
    print(f"🎯 Targeted Search: {niche} in {location} for {offering}")
    
    # Negative keywords to exclude aggregators and listicles
    negatives = '-site:justdial.com -site:sulekha.com -site:indiamart.com -site:tripadvisor.com -site:yelp.com -"top 10" -"top 20" -"best 10" -"list of"'
    
    queries = []
    if offering == "Landing Page":
        # Strategy: Find businesses that rely on social media or free emails (likely no website)
        queries = [
            f'site:facebook.com "{niche}" "{location}" "phone" "gmail.com"',
            f'site:instagram.com "{niche}" "{location}" "contact" "gmail.com"',
            f'"{niche}" "{location}" "@gmail.com" {negatives}', 
            f'"{niche}" "{location}" "contact number" {negatives}'
        ]
    elif offering == "Billing Software":
        # Strategy: Find retail/wholesale businesses that have high transaction volume
        queries = [
            f'"{niche}" "{location}" "store" contact email {negatives}',
            f'"{niche}" "{location}" "distributors" contact {negatives}',
            f'"{niche}" shop "{location}" phone number {negatives}',
            f'"{niche}" wholesalers "{location}" contact {negatives}'
        ]
    else:
        # General search
        queries = [f'"{niche}" in "{location}" contact details email phone {negatives}']

    found_leads = []
    seen_urls = set()

    # Keywords that indicate a listicle or directory in the title
    listicle_indicators = ['top 10', 'top 20', 'top 50', 'best ', 'list of', 'directory', 'yellow pages', 'listings', 'providers in']

    for query in queries:
        print(f"   Running query: {query}")
        try:
            results = search_the_web(query, max_results=15)
            
            for r in results:
                link = r.get('href', '')
                title = r.get('title', '').lower()
                snippet = r.get('body', '').lower()

                if link in seen_urls:
                    continue
                
                # Filter out listicles/directories based on title
                if any(indicator in title for indicator in listicle_indicators):
                    print(f"      Skipping listicle/directory: {title}")
                    continue

                seen_urls.add(link)
                
                # Extract emails from snippet
                emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', snippet)
                # Extract phones (simple pattern for Indian numbers often found in snippets)
                phones = re.findall(r'(?:\+91[\-\s]?)?[6789]\d{9}', snippet)
                
                email = emails[0] if emails else ''
                phone = phones[0] if phones else ''
                
                # Clean up company name
                company_name = r.get('title', '').split('-')[0].split('|')[0].split(':')[0].strip()
                if "profile" in company_name.lower() or "login" in company_name.lower():
                    continue

                # If we found at least one contact method
                if email or phone:
                    lead = {
                        'name': f"Owner/Manager",
                        'email': email,
                        'phone': phone,
                        'company': company_name,
                        'location': location,
                        'source': f'targeted_{offering.lower().replace(" ", "_")}',
                        'status': 'new',
                        'trust_score': 60
                    }
                    
                    # Deduplicate by email or phone locally before adding
                    if not any(l['email'] == email for l in found_leads if email) and \
                       not any(l['phone'] == phone for l in found_leads if phone):
                        
                        # AI Optimization (Optional, can be slow)
                        # lead = optimize_lead_data_with_ai(lead)
                        
                        found_leads.append(lead)
                        print(f"      Found lead: {company_name} ({email or phone})")
        except Exception as e:
            print(f"    Query failed: {e}")
            continue

    return found_leads

# --- API ENDPOINTS ---

@app.route('/api/targeted-search', methods=['POST'])
def targeted_search():
    data = request.json
    location = data.get('location', 'Tamil Nadu')
    niche = data.get('niche', 'Small Business')
    offering = data.get('offering', 'General')
    
    if not location or not niche:
        return jsonify({"error": "Missing location or niche"}), 400
        
    leads = agent_targeted_search(location, niche, offering)
    
    # Save to DB
    saved_count = 0
    for lead in leads:
        # Check if exists
        existing = None
        if lead['email']:
            existing = db.get_lead_by_email(lead['email'])
        
        if not existing:
            db.insert_lead(lead)
            saved_count += 1
            
    return jsonify({
        "message": f"Search complete. Found {len(leads)} leads, {saved_count} new added.", 
        "leads": leads
    })

def agent_keyword_search(keywords):
    """Agent 1.6: Lead Discovery Agent (Keyword Search)"""
    print(f"Searching for keywords: {keywords}...")
    
    found_leads = []
    query = f"{keywords} contact email"
    
    try:
        results = search_the_web(query, max_results=10)
        
        for r in results:
            title = r.get('title', 'Unknown Company')
            link = r.get('href', '')
            snippet = r.get('body', '')
            
            if any(x in link.lower() for x in ['linkedin.com', 'facebook.com', 'twitter.com', 'instagram.com']):
                continue

            print(f"Scraping {link}...")
            emails, phones, addresses, names = extract_contact_info(link)

            email = emails[0] if emails else ''
            phone = phones[0] if phones else ''
            address = addresses[0] if addresses else 'Unknown'
            name = names[0] if names else ''

            if not email:
                snippet_emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', snippet)
                if snippet_emails:
                    email = snippet_emails[0]

            company_name = title.split('-')[0].split('|')[0].strip()
            if len(company_name) < 3:
                company_name = "Unknown Company"

            if email or phone:
                contact_name = name if name else f'Contact at {company_name}'
                lead = {
                    'name': contact_name,
                    'email': email,
                    'phone': phone,
                    'company': company_name,
                    'location': address,
                    'source': 'ai_keyword_search'
                }

                existing = db.get_lead_by_email(email) if email else None
                if not existing:
                    # Optimize with AI
                    lead = optimize_lead_data_with_ai(lead)
                    
                    # db.insert_lead(lead) # Don't insert yet
                    found_leads.append(lead)
                    print(f"Found candidate lead: {company_name} - {email or phone}")
                else:
                    print(f"Duplicate lead skipped: {email or phone}")
                
    except Exception as e:
        print(f"Keyword Discovery Error: {e}")
        return []
            
    return found_leads

@app.route('/api/web-search', methods=['POST'])
def web_search():
    data = request.json
    query = data.get('query')
    
    if not query:
        return jsonify({"error": "Missing query"}), 400
        
    try:
        results = search_the_web(query, max_results=20) # Fetch more to allow for filtering
        
        filtered_results = []
        # Keywords to skip (directories, listicles, aggregators)
        skip_keywords = [
            'top-', 'best-', 'list-of', 'directory', 'clutch.co', 'yelp.com', 
            'sulekha.com', 'justdial.com', 'yellowpages', 'thumbtack', 'upwork', 
            'fiverr', 'linkedin.com', 'facebook.com', 'instagram.com', 'glassdoor',
            'goodfirms', 'designrush', 'sortlist', 'themanifest'
        ]
        
        skip_titles = ['top 10', 'top 20', 'top 30', 'top 50', 'top 100', 'best ', 'list of ', 'directory', 'reviews']

        for r in results:
            link = r.get('href', '')
            title = r.get('title', '').lower()
            
            if not link: continue
            
            # Check URL patterns
            if any(k in link.lower() for k in skip_keywords):
                continue
                
            # Check Title patterns
            if any(k in title for k in skip_titles):
                continue
                
            filtered_results.append(r)
            
        return jsonify({"results": filtered_results[:10]}) # Return top 10 filtered
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/keyword-search', methods=['POST'])
def keyword_search():
    data = request.json
    keywords = data.get('keywords')
    
    if not keywords:
        return jsonify({"error": "Missing keywords"}), 400
        
    leads = agent_keyword_search(keywords)
    return jsonify({"message": f"Found and added {len(leads)} leads", "leads": leads})

@app.route('/api/search-leads', methods=['POST'])
def search_leads():
    data = request.json
    industry = data.get('industry')
    location = data.get('location')
    
    if not industry or not location:
        return jsonify({"error": "Missing industry or location"}), 400
        
    leads = agent_discovery(industry, location)
    return jsonify({"message": f"Found and added {len(leads)} leads", "leads": leads})

@app.route('/api/scrape-url', methods=['POST'])
def scrape_url():
    data = request.json
    url = data.get('url')
    
    print(f"🔍 API called with URL: {url}")
    
    if not url:
        return jsonify({"error": "Missing URL"}), 400
        
    print("🔍 About to call agent_scrape_specific_url...")
    leads = agent_scrape_specific_url(url)
    print(f"🔍 Function returned {len(leads)} leads")
    
    # Prepare a more detailed response
    lead_details = []
    for lead in leads:
        lead_details.append({
            "company": lead.get("company"),
            "name": lead.get("name"),
            "email": lead.get("email"),
            "phone": lead.get("phone")
        })

    return jsonify({
        "message": f"Successfully scraped {len(leads)} lead(s) from the URL.",
        "leads": lead_details,
        "debug": {
            "url": url,
            "leads_count": len(leads),
            "api_called": True
        }
    })

@app.route('/api/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        data = request.json
        db.update_setting('autopilot', str(data.get('autopilot', 'false')).lower())
        return jsonify({"message": "Settings updated"})
    else:
        val = db.get_setting('autopilot')
        return jsonify({"autopilot": val == 'true'})

@app.route('/api/upload-leads', methods=['POST'])

def upload_leads():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    filepath = os.path.join('uploads', file.filename)
    os.makedirs('uploads', exist_ok=True)
    file.save(filepath)
    
    campaign_id = request.form.get('campaign_id')
    if campaign_id == 'null' or campaign_id == 'undefined':
        campaign_id = None
        
    result = agent_ingest_leads(filepath, campaign_id)
    os.remove(filepath) # Cleanup
    return jsonify(result)

@app.route('/api/export-leads', methods=['GET'])
def export_leads():
    try:
        leads = db.get_all_leads()
        if not leads:
            return jsonify({"error": "No leads to export"}), 404
            
        # Convert to DataFrame
        df = pd.DataFrame(leads)
        
        # Select relevant columns
        cols = ['id', 'name', 'email', 'phone', 'company', 'location', 'status', 'trust_score', 'business_maturity', 'growth_potential', 'campaign_id', 'created_at']
        # Filter cols that exist in df
        cols = [c for c in cols if c in df.columns]
        df = df[cols]
        
        # Create CSV in memory
        csv_data = df.to_csv(index=False)
        
        from flask import Response
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=leads_export.csv"}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/templates', methods=['GET', 'POST'])
def handle_templates():
    if request.method == 'POST':
        data = request.json
        name = data.get('name')
        subject = data.get('subject')
        body = data.get('body')
        
        if not name or not subject or not body:
            return jsonify({"error": "Name, subject, and body are required"}), 400
            
        db.add_template(name, subject, body)
        return jsonify({"message": "Template created"})
    else:
        templates = db.get_templates()
        return jsonify(templates)

@app.route('/api/templates/<int:id>', methods=['DELETE'])
def delete_template(id):
    db.delete_template(id)
    return jsonify({"message": "Template deleted"})

@app.route('/api/campaigns', methods=['GET', 'POST'])
def handle_campaigns():
    if request.method == 'POST':
        data = request.json
        name = data.get('name')
        description = data.get('description', '')
        if not name:
            return jsonify({"error": "Campaign name is required"}), 400
            
        campaign_id = db.create_campaign(name, description)
        return jsonify({"message": "Campaign created", "id": campaign_id})
    else:
        campaigns = db.get_campaigns()
        return jsonify(campaigns)

@app.route('/api/leads/bulk', methods=['POST'])
def add_leads_bulk():
    data = request.get_json()
    if not data or 'leads' not in data:
        return jsonify({"error": "No leads provided"}), 400
    
    leads = data['leads']
    added_count = 0
    
    for lead_data in leads:
        # Validate required fields
        if not lead_data.get('name'):
            continue
            
        # Ensure defaults
        lead_data['status'] = lead_data.get('status', 'new')
        lead_data['trust_score'] = lead_data.get('trust_score', 0)
        lead_data['source'] = lead_data.get('source', 'bulk_import')
        
        try:
            # Check for duplicates again just in case
            existing = db.get_lead_by_email(lead_data.get('email')) if lead_data.get('email') else None
            if not existing:
                db.insert_lead(lead_data)
                added_count += 1
        except Exception as e:
            print(f"Error adding lead in bulk: {e}")
            continue
            
    return jsonify({"message": f"Successfully added {added_count} leads"}), 201

@app.route('/api/leads', methods=['POST'])
def add_lead():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    # Validate required fields
    if not data.get('name'):
        return jsonify({"error": "Name is required"}), 400
    
    lead_data = {
        'name': data.get('name'),
        'email': data.get('email', ''),
        'phone': data.get('phone', ''),
        'company': data.get('company', ''),
        'location': data.get('location', ''),
        'status': data.get('status', 'new'),
        'trust_score': data.get('trust_score', 0),
        'source': 'manual'
    }
    
    try:
        lead_id = db.insert_lead(lead_data)
        return jsonify({"message": "Lead added successfully", "id": lead_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/dashboard-stats', methods=['GET'])
def dashboard_stats():
    stats = db.get_dashboard_stats()
    return jsonify(stats)

@app.route('/api/leads', methods=['GET'])
def get_leads():
    leads = db.get_all_leads()
    return jsonify(leads)

@app.route('/api/leads/<int:id>', methods=['GET'])
def get_lead(id):
    lead = db.get_lead_by_id(id)
    if lead:
        # Parse JSON string if it exists
        if lead['ai_analysis'] and isinstance(lead['ai_analysis'], str):
             try:
                 lead['ai_analysis'] = json.loads(lead['ai_analysis'])
             except:
                 pass
        return jsonify(lead)
    return jsonify({"error": "Lead not found"}), 404

@app.route('/api/campaigns/<int:id>/sequences', methods=['GET', 'POST'])
def handle_campaign_sequences(id):
    if request.method == 'POST':
        data = request.json
        day_offset = data.get('day_offset')
        subject = data.get('subject')
        body = data.get('body')
        
        if day_offset is None or not subject or not body:
            return jsonify({"error": "Missing fields"}), 400
            
        db.add_campaign_sequence(id, day_offset, subject, body)
        return jsonify({"message": "Sequence step added"})
    else:
        sequences = db.get_campaign_sequences(id)
        return jsonify(sequences)

@app.route('/api/analyze/<int:id>', methods=['POST'])
def analyze_lead(id):
    lead = db.get_lead_by_id(id)
    if not lead:
        return jsonify({"error": "Lead not found"}), 404
    
    analysis = agent_analyze_business(lead)
    decision = agent_decide_outreach(analysis)
    
    status = 'analyzed' if decision == 'OUTREACH' else 'skipped'
    
    db.update_lead_analysis(id, json.dumps(analysis), analysis.get('trust_score', 0), status)
    
    return jsonify({"analysis": analysis, "decision": decision})


@app.route('/api/bulk-scrape-simple', methods=['POST'])
def bulk_scrape_simple():
    try:
        data = request.get_json()
        if not data:
             return jsonify({"error": "Invalid JSON data"}), 400
             
        urls = data.get('urls', [])
        keyword = data.get('keyword') # Optional keyword search mode
        
        results = []
        
        # Suppress SSL warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # If keyword is provided, perform a search first to get URLs
        if keyword and not urls:
            print(f"Performing keyword search for: {keyword}")
            search_results = search_the_web(keyword, max_results=20)
            
            # Filter out listicles/aggregators
            skip_keywords = [
                'top-', 'best-', 'list-of', 'directory', 'clutch.co', 'yelp.com', 
                'sulekha.com', 'justdial.com', 'yellowpages', 'thumbtack', 'upwork', 
                'fiverr', 'linkedin.com', 'facebook.com', 'instagram.com', 'glassdoor',
                'goodfirms', 'designrush', 'sortlist', 'themanifest'
            ]
            skip_titles = ['top 10', 'top 20', 'top 30', 'top 50', 'top 100', 'best ', 'list of ', 'directory', 'reviews']
            
            for r in search_results:
                link = r.get('href', '')
                title = r.get('title', '').lower()
                
                if not link: continue
                
                # Skip aggregators
                if any(k in link.lower() for k in skip_keywords):
                    print(f"Skipping aggregator/listicle (URL): {link}")
                    continue
                    
                if any(k in title for k in skip_titles):
                    print(f"Skipping aggregator/listicle (Title): {title}")
                    continue
                    
                urls.append(link)
            
            # Limit to top 10 to avoid long wait times
            urls = urls[:10]
            print(f"Found {len(urls)} official URLs to scrape.")

        for url in urls:
            if not url.startswith('http'):
                url = 'https://' + url
                
            try:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                # verify=False to avoid SSL errors, timeout=15 for slower sites
                response = requests.get(url, headers=headers, timeout=15, verify=False)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    # Use separator to avoid merging text from adjacent elements
                    text = soup.get_text(separator=' ')
                    
                    # Extract Emails
                    raw_emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
                    # Filter valid emails
                    emails = []
                    for e in set(raw_emails):
                        if not e.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.js', '.css')):
                             emails.append(e)
                    
                    # Extract Phones (Improved Regex)
                    # Matches: (123) 456-7890, 123-456-7890, +1 123 456 7890, 123.456.7890
                    phone_pattern = r'(?:\+?\d{1,3}[ -.]?)?\(?\d{3}\)?[ -.]?\d{3}[ -.]?\d{4}'
                    phones = list(set(re.findall(phone_pattern, text)))
                    
                    results.append({
                        "url": url,
                        "title": soup.title.string.strip() if soup.title else url,
                        "emails": emails,
                        "phones": phones,
                        "status": "success"
                    })
                else:
                    results.append({
                        "url": url,
                        "status": "failed",
                        "error": f"Status code: {response.status_code}"
                    })
                    
            except Exception as e:
                print(f"Error scraping {url}: {e}")
                results.append({
                    "url": url,
                    "status": "failed",
                    "error": str(e)
                })
            
        return jsonify({"results": results})
    except Exception as e:
        print(f"Bulk scrape error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/scrape-justdial', methods=['POST'])
def scrape_justdial():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({"error": "URL is required"}), 400
        
    try:
        scraper = JustDialScraper()
        leads = scraper.scrape(url)
        return jsonify({"message": "Scraping successful", "leads": leads})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/outreach/<int:id>', methods=['POST'])
def outreach_lead(id):
    lead = db.get_lead_by_id(id)
    if not lead:
        return jsonify({"error": "Lead not found"}), 404
    
    data = request.json or {}
    outreach_type = data.get('outreach_type', 'ai') # 'ai', 'template', 'manual'
    
    message = ""
    strategy = "Manual/Template"
    
    if outreach_type == 'template':
        template_id = data.get('template_id')
        if not template_id:
             return jsonify({"error": "Template ID missing"}), 400
        
        template = db.get_template_by_id(template_id)
        if not template:
             return jsonify({"error": "Template not found"}), 404
             
        # Simple variable substitution
        message = template['body']
        message = message.replace('{{name}}', lead.get('name', ''))
        message = message.replace('{{company}}', lead.get('company', ''))
             
    elif outreach_type == 'manual':
        message = data.get('manual_body')
        if not message:
             return jsonify({"error": "Message body missing"}), 400

    else: # AI
        # Ensure analysis exists
        if not lead['ai_analysis']:
            analysis = agent_analyze_business(lead)
            db.update_lead_analysis(id, json.dumps(analysis), analysis.get('trust_score', 0), 'analyzed')
        else:
            if isinstance(lead['ai_analysis'], str):
                 try:
                     analysis = json.loads(lead['ai_analysis'])
                 except:
                     analysis = {}
            else:
                analysis = lead['ai_analysis']
                
        # Generate content
        strategy = agent_message_strategy(lead, analysis)
        message = agent_generate_message(lead, strategy)
    
    # Send
    success = agent_send_outreach(lead, message)
    
    if success:
        # Update status
        db.update_lead_status(id, 'outreach_sent')
        return jsonify({
            "message": "Outreach sent successfully", 
            "content": message,
            "strategy": strategy
        })
    else:
        return jsonify({"error": "Failed to send outreach"}), 500

@app.route('/api/leads/<int:id>/notes', methods=['PUT'])
def update_lead_notes(id):
    data = request.get_json()
    notes = data.get('notes', '')
    
    try:
        db.update_lead_notes(id, notes)
        return jsonify({"message": "Notes updated successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Start Scheduler
    # scheduler.add_job(id='autopilot_task', func=autonomous_loop, trigger='interval', seconds=30)
    # scheduler.init_app(app)
    # scheduler.start()
    
    app.run(debug=True, port=5000, use_reloader=False) # use_reloader=False to prevent double scheduler

