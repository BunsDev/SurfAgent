from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import io
from PIL import Image
from tools.size_limit import ensure_size_within_limits
from config.log import logger

def test_selenium() -> bool:
    """Test if Selenium can run and capture a screenshot of a test page using Chrome."""
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-gpu')  # To avoid potential issues with headless mode
        
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        driver.set_page_load_timeout(20)
        driver.get("https://example.com")
        
        # Set zoom level for better text legibility
        driver.execute_script("document.body.style.zoom = '200%'")  # Increased from 150%
        
        # Ensure text is readable
        driver.execute_script(""" 
            document.querySelectorAll('*').forEach(function(el) {
                let style = window.getComputedStyle(el);
                if (parseInt(style.fontSize) < 16) {  // Increased minimum font size
                    el.style.fontSize = '16px';
                }
                // Improve contrast
                if (style.color && style.backgroundColor) {
                    let textColor = style.color;
                    let bgColor = style.backgroundColor;
                    if (textColor === bgColor || textColor === 'rgba(0, 0, 0, 0)') {
                        el.style.color = '#000000';
                    }
                }
            });
        """)
        
        # Additional wait for text scaling
        time.sleep(1)
        
        # Get page dimensions with padding for better quality
        total_height = driver.execute_script("return Math.max(document.documentElement.scrollHeight, document.body.scrollHeight);")
        total_width = driver.execute_script("return Math.max(document.documentElement.scrollWidth, document.body.scrollWidth);")
        
        # Add padding and ensure minimum dimensions
        total_width = max(total_width, 1920)
        total_height = int(total_height * 1.1)
        
        # Ensure dimensions are within pixel limit
        final_width, final_height = ensure_size_within_limits(total_width, total_height)
        
        # Set window size with the adjusted dimensions
        driver.set_window_size(final_width, final_height)
        
        # Wait for any dynamic content to load
        time.sleep(1)
        
        # Capture full screenshot in memory with high quality
        screenshot_png = driver.get_screenshot_as_png()
        driver.quit()

        # Decode and verify image
        img = Image.open(io.BytesIO(screenshot_png))
        img.verify()
        logger.info(f"✅ Selenium is running with Chrome and captured screenshot ({img.size[0]}x{img.size[1]} px)")
        return True
    except Exception as e:
        logger.error(f"❌ Selenium test failed: {str(e)}")
        return False