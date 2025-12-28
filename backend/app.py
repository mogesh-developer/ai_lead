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
# import google.generativeai as genai
# # from groq import Groq
# import groq
from dotenv import load_dotenv
from serpapi import Client
import db
import random
import time


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
    # genai.configure(api_key=GEMINI_API_KEY)
    pass

if GROQ_API_KEY:
    # groq_client = groq.Client(api_key=GROQ_API_KEY)
    pass

# --- AI AGENTS ---

def agent_ingest_leads(file_path):
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
                'source': 'upload'
            }
            db.insert_lead(lead_data)
            count += 1
            
        return {"message": f"Successfully ingested {count} leads"}
    except Exception as e:
        return {"error": str(e)}

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
                    db.insert_lead(lead)
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
                    db.insert_lead(lead)
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
                    db.insert_lead(lead)
                    found_leads.append(lead)
                    print(f"Added lead: {company_name} - {email or phone}")
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
            db.insert_lead(lead)
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
    """Agent 3: Business Analysis Agent (Mock for now)"""
    # Mock analysis for demonstration
    import random
    
    # Simple logic based on company name and location
    company_name = lead.get('company', '').lower()
    location = lead.get('location', '').lower()
    
    # Basic scoring logic
    trust_score = 50  # Default
    
    if 'tech' in company_name or 'software' in company_name:
        trust_score += 20
    if 'ltd' in company_name or 'inc' in company_name:
        trust_score += 10
    if 'chennai' in location or 'bangalore' in location:
        trust_score += 15
    
    trust_score = min(100, max(0, trust_score + random.randint(-10, 10)))
    
    # Determine maturity and growth
    if trust_score > 80:
        maturity = "Enterprise"
        growth = "High"
    elif trust_score > 60:
        maturity = "SMB"
        growth = "Medium"
    else:
        maturity = "Startup"
        growth = "Low"
    
    reasoning = f"Analysis based on company name '{lead.get('company', 'Unknown')}' and location '{lead.get('location', 'Unknown')}'. Trust score: {trust_score}/100."
    
    return {
        "trust_score": trust_score,
        "business_maturity": maturity,
        "growth_potential": growth,
        "reasoning": reasoning
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
    """Agent 6: Message Generation Agent (Mock)"""
    name = lead.get('name', 'Valued Partner')
    company = lead.get('company', 'your company')
    
    if strategy == "professional":
        return f"Dear {name},\n\nI hope this email finds you well. We are a digital marketing agency specializing in helping businesses like {company} grow their online presence.\n\nWe would be interested in discussing how we can support your business objectives.\n\nBest regards,\nMogeshwaran\nDigital Marketing Specialist"
    
    elif strategy == "friendly":
        return f"Hi {name},\n\nI came across {company} and was impressed by what you do. We're a digital marketing team that helps businesses expand their reach online.\n\nWould love to chat about how we can help {company} grow!\n\nBest,\nMogeshwaran"
    
    else:  # polite
        return f"Hello {name},\n\nMy name is Mogeshwaran and I work with a digital marketing agency. I noticed {company} and thought we might be able to help with your online marketing needs.\n\nWould you be open to a quick conversation?\n\nThank you,\nMogeshwaran"

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
                
        print("--- Autopilot Cycle Complete ---")

def agent_analyze_response(response_text, lead):
    """Agent 8: Response Analysis Agent (Mock)"""
    text = response_text.lower()
    
    if any(word in text for word in ['yes', 'interested', 'sure', 'okay', 'great']):
        interest_level = "high"
        sentiment = "positive"
        next_action = "continue"
    elif any(word in text for word in ['maybe', 'later', 'busy', 'not sure']):
        interest_level = "medium"
        sentiment = "neutral"
        next_action = "follow_up"
    else:
        interest_level = "low"
        sentiment = "negative"
        next_action = "stop"
    
    return {
        "interest_level": interest_level,
        "sentiment": sentiment,
        "next_action": next_action
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

# --- API ENDPOINTS ---

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
                    db.insert_lead(lead)
                    found_leads.append(lead)
                    print(f"Added lead: {company_name} - {email or phone}")
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
        results = search_the_web(query, max_results=10)
        return jsonify({"results": results})
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
    
    result = agent_ingest_leads(filepath)
    os.remove(filepath) # Cleanup
    return jsonify(result)

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
        db.insert_lead(lead_data)
        return jsonify({"message": "Lead added successfully"}), 201
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

@app.route('/api/outreach/<int:id>', methods=['POST'])
def outreach_lead(id):
    lead = db.get_lead_by_id(id)
    if not lead:
        return jsonify({"error": "Lead not found"}), 404
    
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

