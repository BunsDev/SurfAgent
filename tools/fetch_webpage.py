from config.log import logger
from tools.host_tracker import host_tracker 
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urlparse
import time
import io
import base64
from tools.size_limit import ensure_size_within_limits
from tools.capture_ss import capture_full_page_screenshot
from configure.vision import configure_vision_model
from configure.config_llm import configure_llm
from tools.vision_query import generate_vision_query


def fetch_webpage_content(url: str, provider: str, original_query: str) -> str:
    """Fetch webpage content by capturing a screenshot via Selenium and processing it with a vision model."""
    if host_tracker .is_problematic_host(url):
        logger.info(f"Skipping known problematic host: {urlparse(url).netloc}")
        return f"Skipped: Known problematic host"

    try:
        # Set up Selenium (headless Chrome)
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-gpu')  # To avoid potential issues with headless mode
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')  # Hide automation
        chrome_options.add_argument('--disable-notifications')
        
        # Add headers to appear more like a real browser
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
        
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        driver.set_page_load_timeout(60)
        
        # Set cookies and localStorage to bypass some anti-bot measures
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Attempt to load the page
        driver.get(url)
        time.sleep(2)  # Give time for dynamic content to load
        
        # Check for and handle CAPTCHA/cookie popups
        try:
            driver.execute_script("""
                // Remove common overlay elements
                document.querySelectorAll('[class*="cookie"], [class*="popup"], [class*="modal"], [id*="cookie"], [id*="popup"], [id*="modal"]')
                    .forEach(el => el.remove());
                // Remove fixed position elements that might overlay content
                document.querySelectorAll('*').forEach(el => {
                    const style = window.getComputedStyle(el);
                    if (style.position === 'fixed' || style.position === 'sticky') {
                        el.remove();
                    }
                });
            """)
        except Exception as e:
            logger.warning(f"Error handling overlays: {str(e)}")
        
        # Set text size and ensure readability with special handling for financial data
        driver.execute_script("""
            // Set base zoom
            document.body.style.zoom = '200%';  // Increased from 125%
            
            // Function to check if text might be financial data
            function isFinancialData(text) {
                return /\\$|\\d+\\.\\d+|\\d+%|price|stock|market|share/i.test(text);
            }
            
            // Ensure text is readable with special handling for financial data
            document.querySelectorAll('*').forEach(function(el) {
                let style = window.getComputedStyle(el);
                let text = el.textContent || '';
                
                // Special handling for financial data
                if (isFinancialData(text)) {
                    el.style.fontSize = '24px';  // Larger size for financial data
                    el.style.fontWeight = 'bold';
                    el.style.color = '#000000';  // Ensure high contrast
                } else if (parseInt(style.fontSize) < 16) {  // Increased minimum font size
                    el.style.fontSize = '16px';
                }
                
                // Improve contrast
                if (style.color && style.backgroundColor) {
                    let textColor = style.color;
                    let bgColor = style.backgroundColor;
                    if (textColor === bgColor || textColor === 'rgba(0, 0, 0, 0)' || 
                        textColor === 'rgb(255, 255, 255)' || textColor === '#ffffff') {
                        el.style.color = '#000000';
                    }
                }
                
                // Improve visibility of links
                if (el.tagName.toLowerCase() === 'a') {
                    el.style.textDecoration = 'underline';
                }
            });
            
            // Additional handling for table cells (common in financial data)
            document.querySelectorAll('td, th').forEach(function(el) {
                let text = el.textContent || '';
                if (isFinancialData(text)) {
                    el.style.padding = '10px';
                    el.style.fontSize = '24px';
                    el.style.fontWeight = 'bold';
                }
            });
        """)

        # Additional wait for text adjustments
        time.sleep(2)  # Increased wait time
        
        # Get dimensions and ensure they're within limits
        total_height = driver.execute_script("return Math.max(document.documentElement.scrollHeight, document.body.scrollHeight);")
        total_width = driver.execute_script("return Math.max(document.documentElement.scrollWidth, document.body.scrollWidth);")
        
        final_width, final_height = ensure_size_within_limits(total_width, total_height)
        logger.info(f"Adjusted dimensions to {final_width}x{final_height} to stay within pixel limit")
        
        # Set final window size
        driver.set_window_size(final_width, final_height)
        time.sleep(1)
        
        # Capture the screenshot using our improved method
        screenshot_png = capture_full_page_screenshot(driver, url)
        driver.quit()

        # Process the image
        img = Image.open(io.BytesIO(screenshot_png))
        
        # Convert to RGB and enhance readability
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        
        # Enhance image quality with specified values
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.25)  # Modified sharpness value
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.25)  # Modified contrast value
        
        # Save with high quality
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=100, optimize=True)  # Maximum quality
        screenshot_data = output.getvalue()
        
        # Convert to base64
        base64_image = base64.b64encode(screenshot_data).decode('utf-8')
        
        vision_llm = configure_vision_model(provider)
        text_llm = configure_llm(provider)
        
        vision_query = generate_vision_query(text_llm, original_query)
        logger.info(f"Using vision query: {vision_query}")

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": vision_query},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                            "detail": "high"
                        }
                    }
                ]
            }
        ]
        
        logger.info(f"Processing screenshot from {url} with vision model ({provider})")
        vision_response = vision_llm.invoke(messages)
        
        extracted_text = vision_response.content.strip()
        
        print("\n" + "="*80)
        print(f"Vision Model Description for {url}:")
        print("-"*80)
        print(extracted_text)
        print("="*80 + "\n")
        
        logger.info(f"Successfully processed content from {url}")
        return extracted_text
        
    except Exception as e:
        host_tracker .add_failed_host(url)
        logger.error(f"Error processing {url}: {str(e)}")
        return f"Error processing {url}: {str(e)}"