import trafilatura
from web_scraper import get_search_results, get_website_text
from youtube_scraper import get_youtube_videos
from image_scraper import get_images
import re
import random

# Generate facts and tips based on search results
def generate_facts_and_tips(query, num_facts=5, search_limit=500):
    """
    Generate facts and tips related to the query using web scraping.
    Returns more facts (5 by default) to provide richer responses.
    Facts are organized in a logical sequence for better readability.
    
    Args:
        query (str): The search query
        num_facts (int): Number of facts to return (default: 5)
        search_limit (int): Maximum number of search results to retrieve (default: 500)
    """
    # Common educational topics with prepared content for fallback
    educational_topics = {
        "photosynthesis": [
            "Photosynthesis is the process by which green plants, algae and some bacteria convert light energy from the sun into chemical energy stored in glucose.",
            "During photosynthesis, plants take in carbon dioxide and water and release oxygen as a byproduct.",
            "The overall equation for photosynthesis is: 6CO2 + 6H2O + light energy → C6H12O6 + 6O2.",
            "Chlorophyll, the green pigment in plants, is essential for capturing light energy during photosynthesis.",
            "Photosynthesis occurs primarily in the chloroplasts of plant cells, specifically in the thylakoid membranes."
        ],
        "solar system": [
            "Our solar system consists of the Sun, eight planets, dwarf planets, moons, asteroids, comets and other celestial bodies.",
            "The eight planets in order from the Sun are: Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, and Neptune.",
            "Jupiter is the largest planet in our solar system, while Mercury is the smallest.",
            "The Sun contains 99.86% of the mass in the solar system.",
            "Pluto was reclassified as a dwarf planet in 2006 by the International Astronomical Union."
        ],
        "machine learning": [
            "Machine learning is a branch of artificial intelligence that enables computer systems to learn from data and improve without explicit programming.",
            "The three main types of machine learning are supervised learning, unsupervised learning, and reinforcement learning.",
            "Supervised learning uses labeled training data to make predictions, while unsupervised learning finds patterns in unlabeled data.",
            "Neural networks, decision trees, and support vector machines are common machine learning algorithms.",
            "Deep learning is a subset of machine learning that uses neural networks with multiple layers to analyze complex patterns."
        ]
    }
    
    # Check if query contains any of the educational topics
    for topic, prepared_facts in educational_topics.items():
        if topic in query.lower():
            return prepared_facts[:num_facts]
    
    # Get search results - using customizable search limit for comprehensive coverage
    search_results = get_search_results(query, max_results=search_limit)
    
    facts = []
    
    # Extract facts from search results in order of relevance
    # First, extract from top results (likely more relevant)
    for result in search_results[:10]:
        try:
            # Get URL with default fallback
            result_url = result.get("url", "#")
            if result_url != "#":  # Skip placeholder results
                # Get text from the website
                text = get_website_text(result_url, max_paragraphs=8)
                
                # Clean any HTML tags from the text first
                text = re.sub(r'<.*?>', '', text)
                
                # Extract sentences that contain keywords from the query
                sentences = re.split(r'(?<=[.!?])\s+', text)
                keywords = [word.lower() for word in query.split() if len(word) > 3]
                if not keywords:  # If no long words, use all words
                    keywords = [word.lower() for word in query.split()]
                
                # Look for definition-like sentences first (they make good introductory facts)
                definition_patterns = [
                    f"{query.lower()} is", 
                    f"{query.lower()} are", 
                    f"{query.lower()} refers to",
                    f"definition of {query.lower()}"
                ]
                
                # First pass - look for definition sentences
                for sentence in sentences:
                    if len(sentence) > 30 and any(pattern in sentence.lower() for pattern in definition_patterns):
                        # Clean up the sentence
                        clean_sentence = re.sub(r'\s+', ' ', sentence).strip()
                        # Remove any HTML tags completely
                        clean_sentence = re.sub(r'<[^>]*>', '', clean_sentence)
                        if clean_sentence and clean_sentence not in facts:  # Avoid duplicates and empty strings
                            facts.append(clean_sentence)
                            if len(facts) >= 2:  # Get up to 2 definition sentences
                                break
                
                # Second pass - add other relevant sentences
                for sentence in sentences:
                    if len(sentence) > 30 and any(keyword in sentence.lower() for keyword in keywords):
                        # Clean up the sentence
                        clean_sentence = re.sub(r'\s+', ' ', sentence).strip()
                        # Remove any HTML tags completely
                        clean_sentence = re.sub(r'<[^>]*>', '', clean_sentence)
                        if clean_sentence and clean_sentence not in facts:  # Avoid duplicates and empty strings
                            facts.append(clean_sentence)
                            if len(facts) >= num_facts * 2:  # Get more than we need so we can select the best
                                break
                
                if len(facts) >= num_facts * 2:
                    break
        except Exception as e:
            # Get URL for error message (safely)
            error_url = result.get("url", "unknown URL") if result else "unknown URL"
            print(f"Error extracting facts from {error_url}: {e}")
    
    # Try to extract direct data from search result descriptions if we have fewer than 3 facts
    if len(facts) < 3:
        for result in search_results:
            description = result.get("description", "")
            if len(description) > 30:
                # Clean the description of any HTML
                clean_description = re.sub(r'<[^>]*>', '', description)
                if clean_description and clean_description not in facts:
                    facts.append(clean_description)
    
    # If still no facts were found, return a generic message
    if not facts:
        return ["I couldn't find specific facts for this query. Try searching for a different topic or phrase your question differently."]
    
    # Deduplicate facts
    unique_facts = list(set(facts))
    
    # Organize facts in a logical order:
    # 1. Start with definitions or general explanations
    # 2. Then move to more specific details
    # 3. Sort remaining facts by length for informative content
    
    # Create scores for each fact to determine logical order
    fact_scores = []
    for fact in unique_facts:
        score = 0
        fact_lower = fact.lower()
        
        # Definition-like sentences go first
        if any([
            f"{query.lower()} is" in fact_lower, 
            f"{query.lower()} are" in fact_lower,
            f"{query.lower()} refers to" in fact_lower
        ]):
            score += 1000
            
        # Facts containing "first" or "primary" should come early
        if any(word in fact_lower for word in ["first", "primary", "main", "basic"]):
            score += 500
            
        # Facts with "example" or "application" should come in the middle
        if any(word in fact_lower for word in ["example", "application", "instance"]):
            score += 300
            
        # Facts with technical details or numbers should come later
        if re.search(r'\d+', fact) or any(word in fact_lower for word in ["percent", "technical", "specifically"]):
            score += 100
            
        # Longer facts are generally more informative
        score += min(len(fact) / 10, 50)  # Cap at 50 points for length
        
        fact_scores.append((fact, score))
    
    # Sort facts by their scores in descending order
    sorted_facts = [fact for fact, score in sorted(fact_scores, key=lambda x: x[1], reverse=True)]
    
    # Return the top facts up to the requested number
    return sorted_facts[:num_facts]

# Get comprehensive content for a webpage
def get_webpage_content(url):
    """
    Extract main content from a webpage using trafilatura.
    """
    if not url or url == "#":
        return "No URL provided."
        
    try:
        downloaded = trafilatura.fetch_url(url)
        text = trafilatura.extract(downloaded)
        return text if text else "Could not extract content from the webpage."
    except Exception as e:
        print(f"Error extracting content from {url}: {e}")
        return "Error extracting content."

# Generate a comprehensive response
def generate_response(query, links_limit=10, videos_limit=5, images_limit=12, search_limit=500):
    """
    Generate a comprehensive response based on web search, including 
    text summaries, images and videos.
    Content is organized in a logical sequence for better user experience.
    
    Args:
        query (str): The search query
        links_limit (int): Maximum number of links to display (default: 10)
        videos_limit (int): Maximum number of videos to display (default: 5)
        images_limit (int): Maximum number of images to display (default: 12)
        search_limit (int): Maximum number of search results to retrieve (default: 500)
    """
    # Step 1: Get search results - using search_limit for customizable comprehensive results
    # This needs to be done first as subsequent steps depend on the search results
    search_results = get_search_results(query, max_results=search_limit)
    
    # Filter the search results to only include ones with good content
    filtered_search_results = [
        result for result in search_results 
        if result.get("title") and result.get("url") and result.get("description")
    ]
    
    # Step 2: Generate facts and tips in a logical sequence
    # Facts will be organized with definitions first, then details
    facts = generate_facts_and_tips(query, search_limit=search_limit)
    
    # Step 3: Get visual content - this can happen in parallel with text content
    # Get YouTube videos with customizable limit
    videos = get_youtube_videos(query, max_results=videos_limit)
    
    # Get images with customizable limit
    images = get_images(query, max_results=images_limit)
    
    # Step 4: Format the textual facts in a clean, logical sequence
    facts_text = ""
    if facts:
        facts_text = "Here are some key points I found:\n\n"
        for i, fact in enumerate(facts, 1):
            # More comprehensive cleaning of HTML tags
            # First remove any complete HTML tags
            clean_fact = re.sub(r'<[^>]*>', '', fact)
            # Then remove any leftover HTML entities or fragment tags
            clean_fact = re.sub(r'</?\w+.*?>', '', clean_fact)
            # Clean any HTML entities
            clean_fact = re.sub(r'&[a-z]+;', '', clean_fact)
            # Normalize whitespace
            clean_fact = re.sub(r'\s+', ' ', clean_fact).strip()
            
            # Only add the fact if it's not empty after cleaning
            if clean_fact:
                facts_text += f"{i}. {clean_fact}\n\n"
    
    # Construct the response introduction
    introduction = f"Here's what I found for: '{query}'"
    
    # Prepare the full text response in a logical sequence:
    # 1. Introduction
    # 2. Key facts and information
    text = f"{introduction}\n\n{facts_text}"
    
    # Step 5: Organize search results by relevance and quality
    # Sort search results by relevance (keeping the top ones)
    # with preference for those that have longer, more informative descriptions
    
    # First, add a relevance score to each result
    scored_results = []
    for i, result in enumerate(filtered_search_results[:min(50, len(filtered_search_results))]):  # Consider up to 50 results
        score = 100 - i  # Base score by position (higher for earlier results)
        
        # Add points for results that contain the exact query in title
        if query.lower() in result.get('title', '').lower():
            score += 50
            
        # Add points for longer descriptions (likely more informative)
        desc_length = len(result.get('description', ''))
        score += min(desc_length / 20, 30)  # Up to 30 points for description length
        
        # Add the scored result
        scored_results.append((result, score))
        
    # Sort by score and take top links_limit
    displayed_results = [r for r, _ in sorted(scored_results, key=lambda x: x[1], reverse=True)][:links_limit]
    
    # Step 6: Create the final response object with all content
    # organized in a logical presentation order
    response = {
        "text": text,
        "search_results": displayed_results,  # Showing high-quality results sorted by relevance
        "videos": videos,
        "images": images
    }
    
    return response