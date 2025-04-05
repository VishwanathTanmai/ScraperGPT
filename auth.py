import streamlit as st
import re
import time
import base64
from io import BytesIO
from PIL import Image
from database import insert_user, check_user_exists, verify_user, update_user_profile_pic, get_user_profile_pic

def is_valid_email(email):
    """Check if the email is valid using a regex pattern."""
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None

def is_valid_password(password):
    """Check if the password is at least 6 characters long."""
    return len(password) >= 6

def image_to_base64(img):
    """Convert a PIL Image to base64 string."""
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

def base64_to_image(base64_str):
    """Convert a base64 string to PIL Image."""
    if not base64_str:
        return None
    try:
        img_data = base64.b64decode(base64_str)
        return Image.open(BytesIO(img_data))
    except Exception as e:
        st.error(f"Error loading image: {e}")
        return None

def profile_settings(username):
    """Display profile settings section allowing users to upload profile pictures."""
    st.subheader("Profile Settings")
    
    # Get current profile picture if exists
    current_pic = get_user_profile_pic(username)
    
    # Display current profile picture
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if current_pic:
            try:
                img = base64_to_image(current_pic)
                if img:
                    st.image(img, width=100, caption="Current Profile Picture")
            except:
                st.write("Unable to display current profile picture")
        else:
            st.write("No profile picture set")
    
    with col2:
        # Upload new profile picture
        uploaded_file = st.file_uploader("Choose a profile picture", type=['jpg', 'jpeg', 'png'])
        
        if uploaded_file is not None:
            try:
                # Read and display the uploaded image
                image = Image.open(uploaded_file)
                
                # Resize image to a standard size (e.g., 200x200)
                image = image.resize((200, 200))
                
                # Display the resized image
                st.image(image, width=150, caption="Preview")
                
                # Convert image to base64 for storage
                img_base64 = image_to_base64(image)
                
                # Save button
                if st.button("Save Profile Picture"):
                    # Update user's profile picture in the database
                    if update_user_profile_pic(username, img_base64):
                        st.success("Profile picture updated successfully!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Failed to update profile picture")
            except Exception as e:
                st.error(f"Error processing image: {e}")

def authentication():
    """Handle user authentication using Streamlit components."""
    # Return values
    authenticated = False
    username = ""
    
    # Check if user is already authenticated
    if st.session_state.get("authenticated", False):
        username = st.session_state.username
        
        # Check if user wants to view profile settings
        if st.sidebar.checkbox("Show Profile Settings", key="show_profile"):
            profile_settings(username)
            
        return True, username
    
    # Initialize tab based auth
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    # Login tab
    with tab1:
        st.subheader("Login to your account")
        login_email = st.text_input("Email", key="login_email")
        login_password = st.text_input("Password", type="password", key="login_password")
        
        login_button = st.button("Login", key="login_button")
        
        if login_button:
            if not login_email or not login_password:
                st.error("Please enter both email and password")
            elif not is_valid_email(login_email):
                st.error("Please enter a valid email")
            else:
                # Check user credentials
                user = verify_user(login_email, login_password)
                if user:
                    st.success("Login successful!")
                    authenticated = True
                    username = user[1]  # Username is the 2nd element in the user tuple
                    
                    # Try to get profile pic, with fallback if not available
                    try:
                        profile_pic = user[2] if len(user) > 2 else None
                    except (IndexError, TypeError):
                        profile_pic = None
                    
                    # Set session state
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    if profile_pic:
                        st.session_state.profile_pic = profile_pic
                    
                    # Add a slight delay for the success message to appear
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Invalid email or password")
    
    # Sign up tab
    with tab2:
        st.subheader("Create a new account")
        signup_username = st.text_input("Username", key="signup_username")
        signup_email = st.text_input("Email", key="signup_email")
        signup_password = st.text_input("Password", type="password", key="signup_password")
        signup_confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm_password")
        
        # Profile picture upload
        st.write("Profile Picture (optional)")
        uploaded_file = st.file_uploader("Choose an image", type=['jpg', 'jpeg', 'png'], key="signup_profile_pic")
        
        profile_pic_base64 = None
        if uploaded_file is not None:
            try:
                # Read and display the uploaded image
                image = Image.open(uploaded_file)
                
                # Resize image to a standard size (e.g., 200x200)
                image = image.resize((200, 200))
                
                # Display the resized image
                st.image(image, width=150, caption="Preview")
                
                # Convert image to base64 for storage
                profile_pic_base64 = image_to_base64(image)
            except Exception as e:
                st.error(f"Error processing image: {e}")
        
        signup_button = st.button("Sign Up", key="signup_button")
        
        if signup_button:
            if not signup_username or not signup_email or not signup_password or not signup_confirm_password:
                st.error("Please fill in all required fields")
            elif not is_valid_email(signup_email):
                st.error("Please enter a valid email")
            elif not is_valid_password(signup_password):
                st.error("Password must be at least 6 characters long")
            elif signup_password != signup_confirm_password:
                st.error("Passwords do not match")
            elif check_user_exists(signup_email):
                st.error("Email already registered")
            else:
                # Create new user with optional profile picture
                insert_user(signup_username, signup_email, signup_password, profile_pic_base64)
                st.success("Account created successfully! You can now log in.")
                
                # Switch to login tab
                time.sleep(1)
                st.rerun()
    
    return authenticated, username
