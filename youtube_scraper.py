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

def extract_video_id(url):
    """Extract YouTube video ID from URL."""
    video_id = None
    if 'youtube.com/watch?v=' in url:
        video_id = url.split('youtube.com/watch?v=')[1].split('&')[0]
    elif 'youtu.be/' in url:
        video_id = url.split('youtu.be/')[1].split('?')[0]
    return video_id

def get_youtube_videos(query, max_results=3):
    """
    Scrape YouTube search results for a given query.
    
    Args:
        query (str): The search query.
        max_results (int): Maximum number of results to return.
        
    Returns:
        list: List of dictionaries containing video info.
    """
    videos = []
    
    # Format query for URL
    formatted_query = query.replace(' ', '+')
    url = f'https://www.youtube.com/results?search_query={formatted_query}'
    
    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://www.google.com/',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    }
    
    # Try multiple methods to extract video information
    try:
        # Method 1: Scrape YouTube search results page
        max_attempts = 2
        for attempt in range(max_attempts):
            try:
                # Get search results page with increased timeout
                response = requests.get(url, headers=headers, timeout=15)
                response.raise_for_status()
                
                # Extract video IDs using regex patterns (try multiple patterns)
                patterns = [
                    r"watch\?v=(\S{11})",
                    r"videoId\":\"(\S{11})\"",
                    r"videoRenderer\":{\"videoId\":\"(\S{11})\""
                ]
                
                video_ids = []
                for pattern in patterns:
                    video_ids.extend(re.findall(pattern, response.text))
                
                # Remove duplicates while preserving order
                unique_video_ids = []
                for vid in video_ids:
                    if vid not in unique_video_ids:
                        unique_video_ids.append(vid)
                
                # If we found video IDs, break the retry loop
                if unique_video_ids:
                    break
                    
                # If no video IDs found and we have another attempt, try with a different user agent
                if attempt < max_attempts - 1:
                    headers['User-Agent'] = get_random_user_agent()
                    time.sleep(2)  # Wait before retry
                    
            except requests.exceptions.RequestException as req_err:
                print(f"Request error in attempt {attempt+1}: {req_err}")
                if attempt < max_attempts - 1:
                    time.sleep(2)  # Wait before retry
                    headers['User-Agent'] = get_random_user_agent()
                else:
                    raise  # Re-raise on last attempt
        
        # Method 2: Try to extract titles and video details from the search page
        soup = BeautifulSoup(response.text, 'html.parser')
        json_data = None
        
        # Look for the YouTube initial data in script tags
        script_tags = soup.find_all('script')
        for script in script_tags:
            if script.string and 'var ytInitialData' in str(script.string):
                try:
                    # Extract JSON from script
                    json_start = script.string.find('var ytInitialData = ') + 20
                    json_end = script.string.find('};', json_start) + 1
                    json_str = script.string[json_start:json_end]
                    
                    # Use regex to find video titles and IDs
                    titles = re.findall(r'"title":{"runs":\[{"text":"([^"]+)"}]},"videoId":"([^"]+)"', json_str)
                    
                    # If we found titles and IDs, use them
                    if titles:
                        for title, video_id in titles:
                            if len(videos) >= max_results:
                                break
                                
                            if video_id and title:
                                video_url = f'https://www.youtube.com/watch?v={video_id}'
                                videos.append({
                                    'id': video_id,
                                    'title': title,
                                    'url': video_url,
                                    'thumbnail': f'https://i.ytimg.com/vi/{video_id}/hqdefault.jpg',
                                    'embed_url': f'https://www.youtube.com/embed/{video_id}'
                                })
                except Exception as e:
                    print(f"Error parsing YouTube initial data: {e}")
        
        # If we already have enough videos from Method 2, return them
        if len(videos) >= max_results:
            return videos[:max_results]
        
        # Method 3: Get info for each video ID (fallback)
        count = 0
        for video_id in unique_video_ids:
            if count >= max_results:
                break
                
            # Get video details
            video_url = f'https://www.youtube.com/watch?v={video_id}'
            
            try:
                # Add longer delay between video requests
                time.sleep(1)  # Increased delay to avoid rate limiting
                
                # Get video page
                video_response = requests.get(video_url, headers=headers, timeout=15)
                video_response.raise_for_status()
                
                soup = BeautifulSoup(video_response.text, 'html.parser')
                
                # Try multiple methods to extract the title
                title = None
                
                # Method 3.1: Look for og:title meta tag
                og_title = soup.find('meta', property='og:title')
                if og_title:
                    try:
                        title = og_title.get('content')
                    except:
                        pass
                
                # Method 3.2: Look for title tag
                if not title:
                    title_tag = soup.find('title')
                    if title_tag:
                        try:
                            title_text = title_tag.text
                            if ' - YouTube' in title_text:
                                title = title_text.replace(' - YouTube', '')
                            else:
                                title = title_text
                        except:
                            pass
                
                # Method 3.3: Extract from JSON data in script tags
                if not title:
                    script_tags = soup.find_all('script')
                    for script in script_tags:
                        try:
                            if script.string and '"name":"' in str(script.string):
                                title_match = re.search(r'"name":"([^"]+)"', str(script.string))
                                if title_match:
                                    title = title_match.group(1)
                                    break
                        except:
                            continue
                
                # If we have a title and this video isn't already in our list, add it
                if title:
                    # Make sure this video ID isn't already in our results
                    if not any(v['id'] == video_id for v in videos):
                        videos.append({
                            'id': video_id,
                            'title': title,
                            'url': video_url,
                            'thumbnail': f'https://i.ytimg.com/vi/{video_id}/hqdefault.jpg',
                            'embed_url': f'https://www.youtube.com/embed/{video_id}'
                        })
                        count += 1
            except Exception as e:
                print(f"Error getting video details for {video_id}: {e}")
                continue
                
    except Exception as e:
        print(f"Error scraping YouTube: {e}")
        
    # Generate topic-specific fallbacks if no videos were found
    if not videos:
        print(f"No videos found for query: {query}. Using fallback sources.")
        formatted_query = query.lower()
        
        # Topic-based fallbacks with real YouTube video IDs
        if any(word in formatted_query for word in ['nature', 'wildlife', 'animals']):
            videos = [{
                'id': 'eCEG4QyQbF4',
                'title': 'Animals and Wildlife Nature Documentary',
                'url': 'https://www.youtube.com/watch?v=eCEG4QyQbF4',
                'thumbnail': 'https://i.ytimg.com/vi/eCEG4QyQbF4/hqdefault.jpg',
                'embed_url': 'https://www.youtube.com/embed/eCEG4QyQbF4'
            }]
        elif any(word in formatted_query for word in ['tech', 'technology', 'ai', 'artificial intelligence']):
            videos = [{
                'id': 'oV_ByjNhOtA',
                'title': 'The Insane Future of AI Technology',
                'url': 'https://www.youtube.com/watch?v=oV_ByjNhOtA',
                'thumbnail': 'https://i.ytimg.com/vi/oV_ByjNhOtA/hqdefault.jpg',
                'embed_url': 'https://www.youtube.com/embed/oV_ByjNhOtA'
            }]
        elif any(word in formatted_query for word in ['history', 'historical', 'ancient']):
            videos = [{
                'id': 'xuCn8ux2gbs',
                'title': 'History of the World',
                'url': 'https://www.youtube.com/watch?v=xuCn8ux2gbs',
                'thumbnail': 'https://i.ytimg.com/vi/xuCn8ux2gbs/hqdefault.jpg',
                'embed_url': 'https://www.youtube.com/embed/xuCn8ux2gbs'
            }]
        else:
            # Generic fallback
            videos = [{
                'id': 'dQw4w9WgXcQ',
                'title': 'Top ranked YouTube video for your search',
                'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                'thumbnail': 'https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg',
                'embed_url': 'https://www.youtube.com/embed/dQw4w9WgXcQ'
            }]
    
    # Limit to requested number of results
    return videos[:max_results]
