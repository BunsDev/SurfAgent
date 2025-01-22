from config.log import logger
from PIL import Image
import io
import math
import time
from tools.size_limit import ensure_size_within_limits

def capture_full_page_screenshot(driver, url: str) -> bytes:
    """Capture a full page screenshot by scrolling and stitching."""
    try:
        # Get initial dimensions
        total_height = driver.execute_script("return Math.max(document.documentElement.scrollHeight, document.body.scrollHeight);")
        total_width = driver.execute_script("return Math.max(document.documentElement.scrollWidth, document.body.scrollWidth);")
        
        # Calculate viewport height
        viewport_height = driver.execute_script("return window.innerHeight;")
        
        # Pre-calculate final dimensions to ensure they're within limits
        MAX_PIXELS = 33177600 * 0.9  # 10% safety margin
        
        # If the page is very long, we'll split it into sections
        if total_height > 15000 or (total_width * total_height) > MAX_PIXELS:
            # Calculate maximum height that would fit within pixel limit
            max_safe_height = int(MAX_PIXELS / total_width)
            
            # Adjust section size based on max safe height
            section_height = min(viewport_height, max_safe_height // 4)  # Use quarter of max safe height per section
            
            sections = []
            offset = 0
            while offset < total_height:
                # Scroll to position
                driver.execute_script(f"window.scrollTo(0, {offset});")
                time.sleep(0.5)  # Wait for scroll and content to load
                
                # Capture viewport
                section_png = driver.get_screenshot_as_png()
                section = Image.open(io.BytesIO(section_png))
                
                # Ensure section is within limits
                if section.height > section_height:
                    section = section.crop((0, 0, section.width, section_height))
                
                sections.append(section)
                offset += section_height
            
            # Calculate final dimensions ensuring they're within limits
            final_width = min(total_width, 1920)  # Cap width at 1920px
            final_height = min(total_height, int(MAX_PIXELS / final_width))
            
            # Create new image with calculated dimensions
            final_image = Image.new('RGB', (final_width, final_height))
            y_offset = 0
            
            for section in sections:
                if y_offset + section.height > final_height:
                    # Crop section if it would exceed final height
                    remaining_height = final_height - y_offset
                    if remaining_height <= 0:
                        break
                    section = section.crop((0, 0, section.width, remaining_height))
                
                final_image.paste(section, (0, y_offset))
                y_offset += section.height
                if y_offset >= final_height:
                    break
            
            # Verify final size
            if final_image.width * final_image.height > MAX_PIXELS:
                # Resize if somehow still too large
                scale = math.sqrt(MAX_PIXELS / (final_image.width * final_image.height))
                new_width = int(final_image.width * scale)
                new_height = int(final_image.height * scale)
                final_image = final_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to PNG
            output = io.BytesIO()
            final_image.save(output, format='PNG', optimize=True)
            return output.getvalue()
        else:
            # For shorter pages, still ensure we're within limits
            final_width, final_height = ensure_size_within_limits(total_width, total_height)
            driver.set_window_size(final_width, final_height)
            time.sleep(0.5)
            return driver.get_screenshot_as_png()
            
    except Exception as e:
        logger.error(f"Error in full page capture: {str(e)}")
        # Fallback to a safe capture
        safe_width, safe_height = ensure_size_within_limits(1920, 1080)
        driver.set_window_size(safe_width, safe_height)
        return driver.get_screenshot_as_png()