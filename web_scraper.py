import requests
from bs4 import BeautifulSoup
import html2text
import re
import random
import time

# List of user agents to rotate and avoid being blocked
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

def clean_text(text):
    """Clean scraped text by removing extra whitespace and normalizing."""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespace
    text = text.strip()
    return text

def get_duckduckgo_results(query, max_results=500):
    """
    Scrape DuckDuckGo search results for a given query.
    Increased maximum results to 500 for more comprehensive search.
    Supports multi-page fetching to gather more results.
    
    Args:
        query (str): The search query.
        max_results (int): Maximum number of results to return (up to 500).
        
    Returns:
        list: List of dictionaries containing title, description, and URL.
    """
    results = []
    # Initialize pages counter to track pages fetched
    pages_fetched = 0
    
    # Format query for URL
    formatted_query = query.replace(' ', '+')
    url = f'https://html.duckduckgo.com/html/?q={formatted_query}'
    
    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://duckduckgo.com/',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
    }
    
    try:
        # Keep track of pages we've fetched
        max_pages = 5  # Lower safety limit to prevent too many requests
        current_url = url
        
        # Continue fetching pages until we reach max results or max pages
        while len(results) < max_results and pages_fetched < max_pages:
            # Fetch current page with a longer timeout
            try:
                response = requests.get(current_url, headers=headers, timeout=15)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Try different selectors for search results
                search_results = soup.find_all('div', class_='result')
                
                # If the primary selector doesn't work, try alternative selectors
                if not search_results:
                    # Try alternative class for results
                    search_results = soup.find_all('div', class_='result__body')
                
                if not search_results:
                    # Try another alternative structure
                    search_results = soup.find_all('div', class_='links_main')
                
                if not search_results:
                    # As a last resort, get all article tags
                    search_results = soup.find_all('article')
                
                # If we still have no results, check if we're being blocked
                if not search_results:
                    if 'captcha' in response.text.lower() or 'blocked' in response.text.lower():
                        print("DuckDuckGo may be blocking our requests. Adding fallback results.")
                        break
                
                # Track if we found any new results on this page
                new_results_found = False
                
                # Process all results on the page
                for result in search_results:
                    if len(results) >= max_results:
                        break
                    
                    # Try different selectors for title and description
                    title_elem = result.find('a', class_='result__a')
                    if not title_elem:
                        title_elem = result.find('a', class_='result-link')
                    if not title_elem:
                        title_elem = result.find('h2').find('a') if result.find('h2') else None
                        
                    description_elem = result.find('a', class_='result__snippet')
                    if not description_elem:
                        description_elem = result.find('div', class_='result__snippet')
                    if not description_elem:
                        description_elem = result.find('p')
                    
                    if title_elem:
                        title = title_elem.text.strip()
                        try:
                            url = title_elem.get('href')
                        except:
                            # If we can't get href directly, look for other url patterns
                            url_elem = result.find('a', href=True)
                            url = url_elem.get('href') if url_elem else '#'
                        
                        # Extract description, falling back to a default if necessary
                        description = description_elem.text.strip() if description_elem else "No description available."
                        
                        # Get real URL from DuckDuckGo redirect
                        if url and url.startswith('/'):
                            url_parts = url.split('uddg=')
                            if len(url_parts) > 1:
                                url = url_parts[1].split('&')[0]
                        
                        # Check if the result is valid and not a duplicate
                        if title and url and url != '#' and not any(r['url'] == url for r in results):
                            results.append({
                                'title': title,
                                'description': description,
                                'url': url
                            })
                            new_results_found = True
                
                # Increment page counter
                pages_fetched += 1
                
                # If we've reached max results or found no new results, break the loop
                if len(results) >= max_results or not new_results_found:
                    break
                    
                # Try to find the "More Results" button for the next page
                more_button = soup.find('input', {'class': 'btn', 'value': 'More Results'})
                if more_button:
                    form = more_button.find_parent('form')
                    if form:
                        # Get the form data
                        action = form.get('action')
                        if action and isinstance(action, str):
                            current_url = 'https://html.duckduckgo.com/html/' + action
                            
                            # Small delay to avoid rate limiting
                            time.sleep(2)  # Increased delay
                        else:
                            # If no action attribute, we can't continue
                            break
                    else:
                        # If no form, we can't continue
                        break
                else:
                    # If no more button, we can't continue
                    break
            
            except requests.exceptions.RequestException as e:
                print(f"Request error while scraping DuckDuckGo: {e}")
                # Add longer delay before retrying
                time.sleep(3)
                # If we've had multiple failures, break the loop
                if pages_fetched > 0:
                    break
                                    
    except Exception as e:
        print(f"Error scraping DuckDuckGo: {e}")
    
    # Generate fallback results if we couldn't get any real search results
    if not results:
        print("Using fallback search results for query: " + query)
        # Create some fallback results based on the query
        results = [
            {
                'title': f"Search for '{query}'",
                'description': f"Search the web for information about '{query}' using your favorite search engine.",
                'url': f"https://www.google.com/search?q={formatted_query}"
            },
            {
                'title': f"Wikipedia - {query}",
                'description': f"Find information about '{query}' on Wikipedia, the free encyclopedia.",
                'url': f"https://en.wikipedia.org/wiki/Special:Search?search={formatted_query}"
            },
            {
                'title': f"YouTube - {query}",
                'description': f"Watch videos related to '{query}' on YouTube.",
                'url': f"https://www.youtube.com/results?search_query={formatted_query}"
            }
        ]
    
    # Get page count safely, defaulting to 0 if undefined
    pages = pages_fetched if 'pages_fetched' in locals() else 0
    print(f"Found {len(results)} search results for query: {query} across {pages} pages")
    return results

def get_search_results(query, max_results=500):
    """
    Get search results from multiple search engines if needed.
    Currently using only DuckDuckGo for simplicity.
    Increased max_results to 500 for more comprehensive results.
    
    Args:
        query (str): The search query.
        max_results (int): Maximum number of results to return, up to 500.
        
    Returns:
        list: List of dictionaries containing title, description, and URL.
    """
    # Add a small delay to avoid rate limiting
    time.sleep(1)
    
    # Limit max_results to 500 to prevent excessive requests
    effective_max = min(max_results, 500)
    
    # Get results from DuckDuckGo
    results = get_duckduckgo_results(query, effective_max)
    
    # If no results were found, include a fallback that explains how to search
    if not results:
        results = [{
            'title': 'No results found',
            'description': 'Try rephrasing your query or using different search terms.',
            'url': '#'
        }]
    
    return results

def get_website_text(url, max_paragraphs=3):
    """
    Extract main text content from a website.
    
    Args:
        url (str): The URL to scrape.
        max_paragraphs (int): Maximum number of paragraphs to extract.
        
    Returns:
        str: Extracted text content.
    """
    import trafilatura
    
    headers = {'User-Agent': get_random_user_agent()}
    
    try:
        # First try with trafilatura for better content extraction
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            extracted_text = trafilatura.extract(downloaded)
            if extracted_text and len(extracted_text) > 100:
                # Take only a portion of the text to avoid overwhelming
                paragraphs = extracted_text.split('\n\n')
                selected_paragraphs = paragraphs[:max_paragraphs]
                return '\n\n'.join(selected_paragraphs)
        
        # Fallback to BeautifulSoup method
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
        
        # Get paragraphs
        paragraphs = soup.find_all('p')
        
        # Get plain text from paragraphs
        text = ""
        for i, p in enumerate(paragraphs):
            if i >= max_paragraphs:
                break
            
            p_text = p.get_text()
            if len(p_text.strip()) > 20:  # Only include paragraphs with meaningful content
                text += p_text + "\n\n"
        
        return clean_text(text)
    except Exception as e:
        print(f"Error extracting text from {url}: {e}")
        return "Information could not be retrieved from this website."
