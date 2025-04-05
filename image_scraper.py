import requests
from bs4 import BeautifulSoup
import re
import random
import time

# List of user agents to rotate
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 11.5; rv:90.0) Gecko/20100101 Firefox/90.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_5_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15'
]

def get_random_user_agent():
    """Return a random user agent from the list."""
    return random.choice(USER_AGENTS)

def is_valid_image_url(url):
    """
    Check if URL is a valid image URL.
    """
    if not url:
        return False
    if not url.startswith(('http://', 'https://')):
        return False
    if url.endswith(('.svg', '.gif')):
        return False  # Avoid SVGs and GIFs for reliability
    return True

def get_images_from_bing(query, max_results=6):
    """
    Scrape Bing image search results for a given query.
    
    Args:
        query (str): The search query.
        max_results (int): Maximum number of results to return.
        
    Returns:
        list: List of image URLs.
    """
    images = []
    
    # Format query for URL
    formatted_query = query.replace(' ', '+')
    url = f'https://www.bing.com/images/search?q={formatted_query}&form=HDRSC2&first=1'
    
    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://www.bing.com/',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
    }
    
    try:
        # Try with a longer timeout and multiple attempts
        max_attempts = 2
        for attempt in range(max_attempts):
            try:
                response = requests.get(url, headers=headers, timeout=15)
                response.raise_for_status()
                
                # If we got a response, parse it
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Method 1: Find image elements directly
                img_selectors = ['.mimg', '.img_cont img', '.multimedia img', 'img.mimg', '.iusc img']
                
                for selector in img_selectors:
                    img_elements = soup.select(selector)
                    for img in img_elements:
                        if len(images) >= max_results:
                            break
                        
                        img_url = img.get('src') or img.get('data-src')
                        if is_valid_image_url(img_url):
                            images.append(img_url)
                
                # Method 2: Extract from JSON data in script tags if needed
                if len(images) < max_results:
                    script_tags = soup.find_all('script')
                    for script in script_tags:
                        if script.string and 'iurl' in script.string:
                            img_urls = re.findall(r'"iurl":"([^"]+)"', script.string)
                            for img_url in img_urls:
                                if len(images) >= max_results:
                                    break
                                
                                # Clean up the URL (unescape)
                                img_url = img_url.replace('\\', '')
                                
                                if is_valid_image_url(img_url) and img_url not in images:
                                    images.append(img_url)
                
                # Method 3: Look for all img tags with non-tiny dimensions
                if len(images) < max_results:
                    all_imgs = soup.find_all('img')
                    for img in all_imgs:
                        if len(images) >= max_results:
                            break
                            
                        # Check if the image has width or height attributes indicating it's not a tiny icon
                        width = img.get('width')
                        height = img.get('height')
                        
                        if width and height:
                            try:
                                w = int(width)
                                h = int(height)
                                if w >= 100 and h >= 100:  # Only get reasonably sized images
                                    img_url = img.get('src')
                                    if is_valid_image_url(img_url) and img_url not in images:
                                        images.append(img_url)
                            except (ValueError, TypeError):
                                pass
                
                # If we found images, break the retry loop
                if images:
                    break
                    
                # If no images found, try another attempt with a different user agent
                if attempt < max_attempts - 1:
                    headers['User-Agent'] = get_random_user_agent()
                    time.sleep(2)  # Wait before retrying
                    
            except requests.exceptions.RequestException as req_err:
                print(f"Request error in attempt {attempt+1}: {req_err}")
                # If we have more attempts left, try again
                if attempt < max_attempts - 1:
                    time.sleep(2)  # Wait before retrying
                    headers['User-Agent'] = get_random_user_agent()
                else:
                    raise  # Re-raise on last attempt
                    
    except Exception as e:
        print(f"Error scraping Bing Images: {e}")
    
    # If we still don't have results, try an alternative approach
    if not images:
        try:
            # Try an alternative URL format
            alt_url = f'https://www.bing.com/images/search?q={formatted_query}&qft=+filterui:aspect-square&form=IRFLTR'
            response = requests.get(alt_url, headers=headers, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for any images that might be available
            all_imgs = soup.find_all('img')
            for img in all_imgs:
                if len(images) >= max_results:
                    break
                
                img_url = img.get('src')
                if is_valid_image_url(img_url) and img_url not in images:
                    images.append(img_url)
        except Exception as e:
            print(f"Error with alternative image scraping approach: {e}")
            
    return images

def get_images(query, max_results=6):
    """
    Get images from multiple sources if needed.
    Currently using only Bing Images for simplicity.
    
    Args:
        query (str): The search query.
        max_results (int): Maximum number of results to return.
        
    Returns:
        list: List of image URLs.
    """
    # Add a small delay to avoid rate limiting
    time.sleep(1.5)
    
    # Get images from Bing
    images = get_images_from_bing(query, max_results)
    
    # If no images were found, provide semantic fallback images based on the query
    if not images:
        print(f"No images found for query: {query}. Using fallback images.")
        
        # Topic-specific fallback images
        formatted_query = query.lower()
        
        # Common topics with reasonable placeholder images
        if any(word in formatted_query for word in ['nature', 'landscape', 'mountain', 'forest', 'tree']):
            images = [
                "https://images.unsplash.com/photo-1501854140801-50d01698950b?w=800&auto=format&fit=crop",
                "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=800&auto=format&fit=crop"
            ]
        elif any(word in formatted_query for word in ['city', 'urban', 'building', 'architecture']):
            images = [
                "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=800&auto=format&fit=crop",
                "https://images.unsplash.com/photo-1480714378408-67cf0d13bc1b?w=800&auto=format&fit=crop"
            ]
        elif any(word in formatted_query for word in ['tech', 'technology', 'computer', 'digital', 'software', 'hardware']):
            images = [
                "https://images.unsplash.com/photo-1518770660439-4636190af475?w=800&auto=format&fit=crop",
                "https://images.unsplash.com/photo-1496171367470-9ed9a91ea931?w=800&auto=format&fit=crop"
            ]
        elif any(word in formatted_query for word in ['food', 'cooking', 'meal', 'recipe', 'dish']):
            images = [
                "https://images.unsplash.com/photo-1540189549336-e6e99c3679fe?w=800&auto=format&fit=crop",
                "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=800&auto=format&fit=crop"
            ]
        elif any(word in formatted_query for word in ['business', 'finance', 'money', 'office', 'work']):
            images = [
                "https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=800&auto=format&fit=crop",
                "https://images.unsplash.com/photo-1521791136064-7986c2920216?w=800&auto=format&fit=crop"
            ]
        elif any(word in formatted_query for word in ['education', 'learn', 'school', 'study', 'book', 'read']):
            images = [
                "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=800&auto=format&fit=crop",
                "https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?w=800&auto=format&fit=crop"
            ]
        elif any(word in formatted_query for word in ['health', 'fitness', 'exercise', 'workout', 'gym']):
            images = [
                "https://images.unsplash.com/photo-1486218119243-13883505764c?w=800&auto=format&fit=crop",
                "https://images.unsplash.com/photo-1476480862126-209bfaa8edc8?w=800&auto=format&fit=crop"
            ]
        elif any(word in formatted_query for word in ['music', 'instrument', 'song', 'concert']):
            images = [
                "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=800&auto=format&fit=crop",
                "https://images.unsplash.com/photo-1507838153414-b4b713384a76?w=800&auto=format&fit=crop"
            ]
        elif any(word in formatted_query for word in ['animal', 'pet', 'wildlife', 'dog', 'cat']):
            images = [
                "https://images.unsplash.com/photo-1425082661705-1834bfd09dca?w=800&auto=format&fit=crop",
                "https://images.unsplash.com/photo-1507146426996-ef05306b995a?w=800&auto=format&fit=crop"
            ]
        else:
            # General fallback
            images = [
                "https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=800&auto=format&fit=crop",
                "https://images.unsplash.com/photo-1507842217343-583bb7270b66?w=800&auto=format&fit=crop"
            ]
            
        # Add a note about the image source
        images = images[:max_results]  # Limit to the requested number
        
    return images
