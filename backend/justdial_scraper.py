import time
import random
import re
from playwright.sync_api import sync_playwright
from fake_useragent import UserAgent
from bs4 import BeautifulSoup

class JustDialScraper:
    def __init__(self):
        self.ua = UserAgent()
        # Known mapping for Justdial icons (may change)
        self.icon_map = {
            'icon-dc': '+',
            'icon-fe': '(',
            'icon-hg': ')',
            'icon-ba': '-',
            'icon-acb': '0',
            'icon-yz': '1',
            'icon-wx': '2',
            'icon-vu': '3',
            'icon-ts': '4',
            'icon-rq': '5',
            'icon-po': '6',
            'icon-nm': '7',
            'icon-lk': '8',
            'icon-ji': '9'
        }

    def scrape(self, url):
        results = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            
            # Use a random user agent
            user_agent = self.ua.random
            print(f"Using User-Agent: {user_agent}")
            
            context = browser.new_context(
                user_agent=user_agent,
                viewport={'width': 1920, 'height': 1080}
            )
            
            # Add stealth scripts
            context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            page = context.new_page()
            
            try:
                print(f"Navigating to {url}...")
                page.goto(url, timeout=60000, wait_until='domcontentloaded')
                
                # Wait for some content to load
                page.wait_for_selector('.resultbox, .store-details, #tab-5', timeout=10000)
                
                # Scroll to load more (Justdial uses infinite scroll or pagination)
                # We'll scroll a bit to get initial results
                for _ in range(5):
                    page.mouse.wheel(0, 1000)
                    time.sleep(random.uniform(0.5, 1.5))
                
                content = page.content()
                results = self.parse_html(content)
                
            except Exception as e:
                print(f"Scraping error: {e}")
            finally:
                browser.close()
                
        return results

    def parse_html(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        # Select all listing items
        # Justdial uses different classes for different layouts
        items = soup.select('.resultbox') or soup.select('.store-details') or soup.select('.cntanr')
        
        print(f"Found {len(items)} potential items")
        
        for item in items:
            try:
                # Extract Name
                name_el = item.select_one('.store-name') or item.select_one('.lng_cont_name') or item.select_one('h2')
                name = name_el.get_text(strip=True) if name_el else "Unknown"
                
                # Extract Rating
                rating_el = item.select_one('.green-box') or item.select_one('.rating')
                rating = rating_el.get_text(strip=True) if rating_el else "0.0"
                
                # Extract Address
                address_el = item.select_one('.cont_fl_addr') or item.select_one('.address-info') or item.select_one('.adrsstr')
                address = address_el.get_text(strip=True) if address_el else ""
                
                # Extract Phone
                phone = self.extract_phone(item)
                
                # Extract Image
                img_el = item.select_one('img.lazy') or item.select_one('.thumb_img')
                image = img_el.get('data-original') or img_el.get('src') if img_el else ""

                if name != "Unknown":
                    results.append({
                        "company": name,
                        "phone": phone,
                        "address": address,
                        "rating": rating,
                        "image": image,
                        "source": "Justdial"
                    })
            except Exception as e:
                print(f"Error parsing item: {e}")
                continue
                
        return results

    def extract_phone(self, item):
        # Method 1: Look for mobilesv class (often contains the phone number hidden in CSS classes)
        phone_icons = item.select('.mobilesv')
        if phone_icons:
            number = ""
            for icon in phone_icons:
                # Get all classes
                classes = icon.get('class', [])
                for cls in classes:
                    if cls in self.icon_map:
                        number += self.icon_map[cls]
            if number:
                return number

        # Method 2: Look for 'callcontent' or similar text
        call_el = item.select_one('.callcontent')
        if call_el:
            text = call_el.get_text(strip=True)
            # Extract digits
            phones = re.findall(r'\d{10,}', text)
            if phones:
                return phones[0]
                
        # Method 3: Look for any text that looks like a phone number in the item
        text = item.get_text()
        phones = re.findall(r'(?:\+91|0)?[ -]?\d{3,5}[ -]?\d{6,8}', text)
        if phones:
            # Filter out short numbers
            valid_phones = [p for p in phones if len(re.sub(r'\D', '', p)) >= 10]
            if valid_phones:
                return valid_phones[0]

        return "Not Available"

if __name__ == "__main__":
    # Test
    scraper = JustDialScraper()
    # Example URL (replace with a valid one for testing)
    url = "https://www.justdial.com/Chennai/Nursery-Gardens" 
    data = scraper.scrape(url)
    print(f"Scraped {len(data)} leads")
    for lead in data:
        print(lead)
