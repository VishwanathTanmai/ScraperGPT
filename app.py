import streamlit as st
import base64
from datetime import datetime
import time
import json
import os

# Import custom modules
from auth import authentication
from web_scraper import get_search_results
from youtube_scraper import get_youtube_videos
from image_scraper import get_images
from database import (
    create_tables, 
    save_query, 
    get_user_queries, 
    insert_user,
    check_user_exists,
    verify_user,
    clear_user_queries
)
from utils import get_user_avatar, format_time
from ui_components import (
    render_chat_message,
    render_search_results,
    render_videos_section,
    render_images_section
)

# Initialize the app
st.set_page_config(
    page_title="ScrapeGPT",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
create_tables()

# Session state initialization
if "messages" not in st.session_state:
    st.session_state.messages = []
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "user_avatar" not in st.session_state:
    st.session_state.user_avatar = ""
if "cache" not in st.session_state:
    st.session_state.cache = {}
if "chat_id" not in st.session_state:
    st.session_state.chat_id = 1  # For tracking multiple chat sessions

# App title and description
st.markdown("""
<div style='background: linear-gradient(90deg, #4b6cb7 0%, #182848 100%); padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem;'>
    <h1 style='color: white; text-align: center; margin:0;'>🔍 ScrapeGPT</h1>
    <p style='color: white; text-align: center; margin-top: 0.5rem;'></p>
</div>
""", unsafe_allow_html=True)

# Sidebar content
with st.sidebar:
    st.markdown("## 👤 User Profile")
    
    # User Authentication
    authenticated, username = authentication()
    
    # If authenticated, update session state
    if authenticated and username:
        st.session_state.authenticated = True
        st.session_state.username = username
        
        # Always refresh user avatar to get the most current version
        st.session_state.user_avatar = get_user_avatar(username)
        
        # Display user info
        col1, col2 = st.columns([1, 3])
        with col1:
            st.image(st.session_state.user_avatar, width=60)
        with col2:
            st.markdown(f"### Welcome, {username}!")
        
        # Search Settings
        st.markdown("---")
        st.markdown("## ⚙️ Search Settings")
        
        # Initialize search settings in session state if they don't exist
        if "search_limit" not in st.session_state:
            st.session_state.search_limit = 500
        if "links_limit" not in st.session_state:
            st.session_state.links_limit = 10
        if "videos_limit" not in st.session_state:
            st.session_state.videos_limit = 5
        if "images_limit" not in st.session_state:
            st.session_state.images_limit = 12
        
        # Search parameters sliders
        st.session_state.search_limit = st.slider(
            "Maximum search results to retrieve", 
            min_value=50, 
            max_value=500, 
            value=st.session_state.search_limit, 
            step=50,
            help="Higher values provide more comprehensive results but may take longer to process"
        )
        
        st.session_state.links_limit = st.slider(
            "Number of links to display", 
            min_value=3, 
            max_value=20, 
            value=st.session_state.links_limit,
            help="How many search result links to show in responses"
        )
        
        st.session_state.videos_limit = st.slider(
            "Number of videos to display", 
            min_value=0, 
            max_value=10, 
            value=st.session_state.videos_limit,
            help="How many YouTube videos to show in responses"
        )
        
        st.session_state.images_limit = st.slider(
            "Number of images to display", 
            min_value=0, 
            max_value=20, 
            value=st.session_state.images_limit,
            help="How many images to show in responses"
        )
        
        # Search history
        st.markdown("---")
        st.markdown("## 📚 Search History")
        user_queries = get_user_queries(username)
        
        if user_queries:
            for query in user_queries:
                query_text = query[1]
                query_time = format_time(query[2])
                
                with st.container():
                    st.markdown(f"**{query_text}**")
                    st.caption(f"{query_time}")
                    if st.button("Ask Again", key=f"ask_again_{query[0]}"):
                        # Insert the question into the chat
                        new_query = query_text
                        st.session_state.messages.append({"role": "user", "content": new_query, "time": datetime.now().strftime("%H:%M")})
                        st.rerun()
                
                st.markdown("---")
        else:
            st.info("No search history yet.")
    
    # App info
  

# Main chat interface
if st.session_state.authenticated:
    # Chat control buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("🆕 New Chat", key="new_chat"):
            # Clear messages but keep the chat history in database
            st.session_state.messages = []
            st.session_state.chat_id += 1
            st.rerun()
            
    with col3:
        if st.button("🗑️ Delete History", key="delete_history"):
            # Clear both messages and database history
            st.session_state.messages = []
            clear_user_queries(st.session_state.username)
            st.session_state.chat_id += 1
            st.rerun()
    
    # Display a divider
    st.markdown("<hr>", unsafe_allow_html=True)
    
    # Display chat messages
    for message in st.session_state.messages:
        if message["role"] == "user":
            render_chat_message(
                message["content"],
                is_user=True,
                avatar_url=st.session_state.user_avatar,
                time=message.get("time", "")
            )
        else:
            render_chat_message(
                message["content"]["text"],
                is_user=False,
                avatar_url="https://images.unsplash.com/photo-1534527489986-3e3394ca569c",
                time=message.get("time", "")
            )
            
            # Display search results if any
            if "search_results" in message["content"]:
                render_search_results(message["content"]["search_results"])
            
            # Display videos if any
            if "videos" in message["content"]:
                render_videos_section(message["content"]["videos"])
            
            # Display images if any
            if "images" in message["content"]:
                render_images_section(message["content"]["images"])
    
    # User input
    user_query = st.chat_input("Ask something...")
    
    if user_query:
        # Add user message to chat
        current_time = datetime.now().strftime("%H:%M")
        st.session_state.messages.append({"role": "user", "content": user_query, "time": current_time})
        
        # Save query to database
        save_query(st.session_state.username, user_query)
        
        # Check if we have a cached response
        if user_query in st.session_state.cache:
            st.session_state.messages.append({
                "role": "assistant",
                "content": st.session_state.cache[user_query],
                "time": current_time
            })
            st.rerun()
        
        # Show a spinner while processing
        with st.spinner("Searching the web..."):
            # Import the content generator only when needed
            from content_generator import generate_response
            
            # Get the search limits from session state
            search_limit = st.session_state.search_limit
            links_limit = st.session_state.links_limit
            videos_limit = st.session_state.videos_limit
            images_limit = st.session_state.images_limit
            
            # Generate comprehensive response with facts, text, videos and images
            # using the customized search limits
            response = generate_response(
                query=user_query,
                links_limit=links_limit,
                videos_limit=videos_limit,
                images_limit=images_limit,
                search_limit=search_limit
            )
            
            # Cache the response
            st.session_state.cache[user_query] = response
            
            # Add assistant message to chat
            st.session_state.messages.append({
                "role": "assistant",
                "content": response,
                "time": current_time
            })
            
            # Rerun to update the UI
            st.rerun()
else:
    # If not authenticated, display a welcome message
    st.info("👈 Please sign in or create an account to start chatting")
    
    # Display sample chat interface image
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.image("https://images.unsplash.com/photo-1515923256482-1c04580b477c", 
                 caption="Modern chat interface example", use_container_width=True)
