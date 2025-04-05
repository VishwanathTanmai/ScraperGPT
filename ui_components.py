import streamlit as st

def render_chat_message(message, is_user=False, avatar_url=None, time=None):
    """
    Render a chat message in the UI.
    
    Args:
        message (str): The message content.
        is_user (bool): True if the message is from the user, False if from the assistant.
        avatar_url (str): URL to the avatar image.
        time (str): Time the message was sent.
    """
    # Calculate column widths for layout
    avatar_col_width = 1
    time_col_width = 2
    message_col_width = 9
    
    # Set alignment based on who sent the message
    if is_user:
        cols = st.columns([message_col_width, time_col_width, avatar_col_width])
        align = "right"
        bg_color = "#2b313e"
        border_radius = "15px 0px 15px 15px"
    else:
        cols = st.columns([avatar_col_width, message_col_width, time_col_width])
        align = "left"
        bg_color = "#3b4453"
        border_radius = "0px 15px 15px 15px"
    
    # Clean message of any unexpected HTML
    import re
    # More comprehensive HTML tag cleaning
    # First remove complete HTML tags
    message = re.sub(r'<[^>]*>', '', message)
    # Then remove any leftover partial HTML tags
    message = re.sub(r'</?\w+.*?>', '', message)
    # Clean any HTML entities
    message = re.sub(r'&[a-z]+;', '', message)
    # Normalize whitespace
    message = re.sub(r'\s+', ' ', message).strip()
    
    # Render the message
    if is_user:
        # User message: message | time | avatar
        with cols[0]:
            st.markdown(
                f"""
                <div style="background-color: {bg_color}; 
                            padding: 10px 15px; 
                            border-radius: {border_radius}; 
                            margin: 5px 0; 
                            text-align: {align};">
                    {message}
                </div>
                """, 
                unsafe_allow_html=True
            )
        with cols[1]:
            if time:
                st.markdown(f"<div style='color: #7f8694; font-size: 0.8em; text-align: center; padding-top: 10px;'>{time}</div>", unsafe_allow_html=True)
        with cols[2]:
            if avatar_url:
                st.image(avatar_url, width=45)
    else:
        # Assistant message: avatar | message | time
        with cols[0]:
            if avatar_url:
                st.image(avatar_url, width=45)
        with cols[1]:
            st.markdown(
                f"""
                <div style="background-color: {bg_color}; 
                            padding: 10px 15px; 
                            border-radius: {border_radius}; 
                            margin: 5px 0; 
                            text-align: {align};">
                    {message}
                </div>
                """, 
                unsafe_allow_html=True
            )
        with cols[2]:
            if time:
                st.markdown(f"<div style='color: #7f8694; font-size: 0.8em; text-align: center; padding-top: 10px;'>{time}</div>", unsafe_allow_html=True)

def render_search_results(results):
    """
    Render search results in the UI.
    
    Args:
        results (list): List of dictionaries containing search results.
    """
    if not results:
        st.info("No search results found.")
        return
    
    with st.container():
        st.markdown("### 🔍 Search Results")
        
        for result in results:
            # Clean all text fields of HTML tags
            import re
            
            # Clean title
            title = result.get('title', 'No title')
            title = re.sub(r'<[^>]*>', '', title)
            title = re.sub(r'</?\w+.*?>', '', title)
            title = re.sub(r'&[a-z]+;', '', title)
            title = re.sub(r'\s+', ' ', title).strip()
            
            # Clean URL
            url = result.get('url', '#')
            
            # Clean description
            description = result.get('description', 'No description available')
            description = re.sub(r'<[^>]*>', '', description)
            description = re.sub(r'</?\w+.*?>', '', description)
            description = re.sub(r'&[a-z]+;', '', description)
            description = re.sub(r'\s+', ' ', description).strip()
            
            # Create card-like container for each result
            with st.container():
                st.markdown(
                    f"""
                    <div style="
                        background-color: #2b313e;
                        border-radius: 10px;
                        padding: 15px;
                        margin-bottom: 10px;
                    ">
                        <a href="{url}" style="color: #4287f5; text-decoration: none; font-weight: bold; font-size: 1.1em;" target="_blank">
                            {title}
                        </a>
                        <p style="color: #7f8694; font-size: 0.8em; margin: 5px 0;">{url}</p>
                        <p style="margin-top: 10px;">{description}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

def render_videos_section(videos):
    """
    Render video results in the UI.
    
    Args:
        videos (list): List of dictionaries containing video information.
    """
    if not videos:
        return
    
    with st.container():
        st.markdown("### 📹 Videos")
        
        # Use columns for videos
        cols = st.columns(min(len(videos), 3))
        
        for i, video in enumerate(videos):
            # Clean HTML tags from video title
            import re
            title = video.get('title', 'Video')
            title = re.sub(r'<[^>]*>', '', title)
            title = re.sub(r'</?\w+.*?>', '', title)
            title = re.sub(r'&[a-z]+;', '', title)
            title = re.sub(r'\s+', ' ', title).strip()
            
            # Get other video properties
            url = video.get('url', '#')
            thumbnail = video.get('thumbnail', '')
            embed_url = video.get('embed_url', '')
            
            with cols[i % len(cols)]:
                # Create expandable section for each video
                with st.expander(title, expanded=False):
                    # Display thumbnail with link
                    if thumbnail:
                        st.markdown(
                            f"""
                            <a href="{url}" target="_blank">
                                <img src="{thumbnail}" style="width: 100%; border-radius: 5px;">
                            </a>
                            """,
                            unsafe_allow_html=True
                        )
                    
                    # Show embedded player if available
                    if embed_url:
                        try:
                            st.components.v1.iframe(
                                src=embed_url,
                                height=200,
                                scrolling=False
                            )
                        except Exception as e:
                            st.error(f"Failed to load video player: {e}")
                            # Provide a direct link as fallback
                            st.markdown(f"[Watch on YouTube]({url})")
                    else:
                        st.markdown(f"[Watch on YouTube]({url})")

def render_images_section(images):
    """
    Render image results in the UI.
    
    Args:
        images (list): List of image URLs.
    """
    if not images:
        return
    
    with st.container():
        st.markdown("### 🖼️ Images")
        
        # Calculate number of columns based on number of images
        num_cols = min(3, len(images))
        cols = st.columns(num_cols)
        
        # Display images in columns
        for i, img_url in enumerate(images):
            with cols[i % num_cols]:
                try:
                    st.image(img_url, use_container_width=True)
                except Exception as e:
                    st.error(f"Failed to load image: {e}")
