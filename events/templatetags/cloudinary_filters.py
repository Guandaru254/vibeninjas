"""
Cloudinary Image Optimization Template Filters
Creates optimized, responsive images with automatic WebP/AVIF delivery
"""

from django import template
import re

register = template.Library()


@register.filter
def cloudinary_optimize(image_url, width=700):
    """
    Optimizes Cloudinary images with width, format, and quality params
    
    Args:
        image_url: The original Cloudinary image URL
        width: Desired width in pixels (default: 700)
    
    Returns:
        Optimized URL with transformations
        
    Example:
        {{ event.image.url|cloudinary_optimize:700 }}
        
    Transformations applied:
        - w_700: Resize to 700px width
        - c_limit: Don't upscale if image is smaller
        - f_auto: Auto-format (WebP for Chrome, AVIF for newer browsers)
        - q_auto: Auto-quality (balances file size vs visual quality)
    """
    if not image_url or 'cloudinary.com' not in str(image_url):
        return image_url
    
    # Convert to string in case it's a file object
    url = str(image_url)
    
    # Insert transformation parameters after /upload/
    pattern = r'/upload/'
    replacement = f'/upload/w_{width},c_limit,f_auto,q_auto/'
    
    optimized_url = re.sub(pattern, replacement, url, count=1)
    return optimized_url


@register.filter
def cloudinary_thumbnail(image_url, size=300):
    """
    Creates square thumbnails for cards, avatars, etc.
    
    Args:
        image_url: The original Cloudinary image URL
        size: Desired size in pixels (default: 300)
    
    Returns:
        Optimized thumbnail URL
        
    Example:
        {{ user.profile_pic.url|cloudinary_thumbnail:150 }}
        
    Transformations:
        - w_300,h_300: Square dimensions
        - c_fill: Crop to fill the square
        - g_auto: Smart cropping (face detection)
        - f_auto,q_auto: Format and quality optimization
    """
    if not image_url or 'cloudinary.com' not in str(image_url):
        return image_url
    
    url = str(image_url)
    pattern = r'/upload/'
    replacement = f'/upload/w_{size},h_{size},c_fill,g_auto,f_auto,q_auto/'
    
    optimized_url = re.sub(pattern, replacement, url, count=1)
    return optimized_url


@register.filter
def cloudinary_responsive(image_url):
    """
    Creates a responsive image with srcset support
    Returns a dictionary with different sizes
    
    Args:
        image_url: The original Cloudinary image URL
    
    Returns:
        Dictionary with 'small', 'medium', 'large' URLs
        
    Example in template:
        {% with responsive=event.image.url|cloudinary_responsive %}
            <img srcset="{{ responsive.small }} 400w,
                         {{ responsive.medium }} 700w,
                         {{ responsive.large }} 1080w"
                 sizes="(max-width: 768px) 100vw, 700px"
                 src="{{ responsive.medium }}">
        {% endwith %}
    """
    if not image_url or 'cloudinary.com' not in str(image_url):
        return {
            'small': image_url,
            'medium': image_url,
            'large': image_url
        }
    
    url = str(image_url)
    pattern = r'/upload/'
    
    return {
        'small': re.sub(pattern, '/upload/w_400,c_limit,f_auto,q_auto/', url, count=1),
        'medium': re.sub(pattern, '/upload/w_700,c_limit,f_auto,q_auto/', url, count=1),
        'large': re.sub(pattern, '/upload/w_1080,c_limit,f_auto,q_auto/', url, count=1),
    }


@register.filter
def cloudinary_blur_placeholder(image_url):
    """
    Creates a tiny blurred placeholder for progressive loading
    
    Args:
        image_url: The original Cloudinary image URL
    
    Returns:
        Base64-ready tiny blurred image URL
        
    Example:
        <img src="{{ event.image.url|cloudinary_blur_placeholder }}"
             data-src="{{ event.image.url|cloudinary_optimize }}"
             class="lazy-load">
    """
    if not image_url or 'cloudinary.com' not in str(image_url):
        return image_url
    
    url = str(image_url)
    pattern = r'/upload/'
    replacement = '/upload/w_40,h_40,c_fill,e_blur:1000,f_auto,q_auto/'
    
    optimized_url = re.sub(pattern, replacement, url, count=1)
    return optimized_url