import hashlib
import datetime
import random

import base64
from io import BytesIO
from database import get_user_profile_pic

def get_user_avatar(username):
    """
    Get the user's profile picture if available, or a consistent avatar URL based on their username.
    
    Returns:
        str: If user has a custom profile picture, returns a data URI.
             Otherwise, returns a URL to a predefined avatar.
    """
    # Check if user has a custom profile picture
    profile_pic = get_user_profile_pic(username)
    
    if profile_pic:
        # Return as data URI
        return f"data:image/png;base64,{profile_pic}"
    
    # Fallback to predefined avatars
    # List of avatar URLs from Unsplash
    avatar_urls = [
        "https://images.unsplash.com/photo-1438761681033-6461ffad8d80",
        "https://images.unsplash.com/photo-1568602471122-7832951cc4c5",
        "https://images.unsplash.com/photo-1499557354967-2b2d8910bcca",
        "https://images.unsplash.com/photo-1503235930437-8c6293ba41f5",
        "https://images.unsplash.com/photo-1502323777036-f29e3972d82f",
        "https://images.unsplash.com/photo-1533636721434-0e2d61030955"
    ]
    
    # Generate a deterministic index based on username
    hash_value = int(hashlib.md5(username.encode()).hexdigest(), 16)
    index = hash_value % len(avatar_urls)
    
    return avatar_urls[index]

def format_time(timestamp):
    """
    Format a database timestamp into a user-friendly string.
    """
    if isinstance(timestamp, str):
        try:
            # Parse the timestamp string
            dt = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return timestamp
    else:
        dt = timestamp
    
    now = datetime.datetime.now()
    delta = now - dt
    
    # Format based on time difference
    if delta.days == 0:
        # Today - show time
        return f"Today at {dt.strftime('%H:%M')}"
    elif delta.days == 1:
        # Yesterday
        return f"Yesterday at {dt.strftime('%H:%M')}"
    elif delta.days < 7:
        # This week
        return f"{dt.strftime('%A')} at {dt.strftime('%H:%M')}"
    else:
        # Older
        return dt.strftime('%b %d, %Y')

def truncate_text(text, max_length=150):
    """
    Truncate text to a maximum length and add ellipsis if needed.
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length].rsplit(' ', 1)[0] + '...'
