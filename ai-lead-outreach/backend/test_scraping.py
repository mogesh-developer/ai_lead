import re
from playwright.sync_api import sync_playwright

def extract_contact_info(url):
    """Helper to scrape email and phone from a website using Playwright (Headless Browser)"""
    print(f"Scraping {url} with Playwright...")
    try:
        with sync_playwright() as p:
            # Launch browser (headless=True for background)
            browser = p.chromium.launch(headless=True)

            # Create context with realistic User-Agent to avoid blocking
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            try:
                # Navigate and wait for network idle or load
                page.goto(url, timeout=30000, wait_until="domcontentloaded")

                # Wait for potential JS rendering (e.g. React/Vue apps)
                page.wait_for_timeout(3000)

                # Extract text content
                text = page.inner_text('body')

                # Also get HTML for hidden mailto links
                content = page.content()

                # Try to find contact pages if we're on homepage
                if url.endswith('/') or '/home' in url or len(url.split('/')) <= 3:
                    contact_urls = []
                    # Look for contact links in the page
                    contact_links = page.query_selector_all('a[href*="contact"]')
                    for link in contact_links[:3]:  # Limit to first 3 contact links
                        href = link.get_attribute('href')
                        if href:
                            if href.startswith('/'):
                                href = url.rstrip('/') + href
                            elif not href.startswith('http'):
                                href = url.rstrip('/') + '/' + href
                            if href not in contact_urls:
                                contact_urls.append(href)

                    # Scrape contact pages too
                    for contact_url in contact_urls[:2]:  # Limit to 2 contact pages
                        try:
                            page.goto(contact_url, timeout=15000, wait_until="domcontentloaded")
                            page.wait_for_timeout(2000)
                            text += " " + page.inner_text('body')
                            content += " " + page.content()
                        except:
                            continue

            except Exception as nav_err:
                print(f"Navigation error on {url}: {nav_err}")
                browser.close()
                return [], []

            browser.close()

            # Regex for email - improved to catch more variations
            emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text + content))

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

            # Remove duplicates and return
            return list(set(valid_emails)), list(set(cleaned_phones))

    except Exception as e:
        print(f"Playwright Scraping error for {url}: {e}")
        return [], []

# Test the function
if __name__ == "__main__":
    test_urls = [
        "https://www.microsoft.com",
        "https://www.google.com",
        "https://www.apple.com",
        "https://www.amazon.com",
        "https://www.starbucks.com",
        "https://www.netflix.com"
    ]

    for url in test_urls:
        print(f"\n=== Testing {url} ===")
        emails, phones = extract_contact_info(url)
        print(f"Emails found: {emails}")
        print(f"Phones found: {phones}")