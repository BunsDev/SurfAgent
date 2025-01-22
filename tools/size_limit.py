import math

def ensure_size_within_limits(width: int, height: int, max_pixels: int = 33177600) -> tuple:
    """Ensure dimensions are within the pixel limit while maintaining aspect ratio."""
    total_pixels = width * height
    
    max_pixels = int(max_pixels * 0.9)  
    
    if total_pixels <= max_pixels:
        return width, height
    
    # Calculate scaling factor to fit within limit
    scale = math.sqrt(max_pixels / total_pixels)
    new_width = int(width * scale)
    new_height = int(height * scale)
    
    if new_width * new_height > max_pixels:
        scale *= 0.95
        new_width = int(width * scale)
        new_height = int(height * scale)
    
    return new_width, new_height