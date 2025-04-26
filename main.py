import streamlit as st
from pytubefix import YouTube
import os
import ssl
import uuid

# Create a dedicated downloads folder
DOWNLOAD_FOLDER = "youtube_downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def download_video(url):
    # Configure SSL certificate verification
    ssl._create_default_https_context = ssl._create_unverified_context
    
    try:
        # Initialize YouTube object with proper parameters
        yt = YouTube(url)
        
        # Get video information
        title = yt.title

        stream = yt.streams.filter(adaptive=True, file_extension='mp4', type='video').order_by('resolution').desc().first()
        
        if not stream:
            # Second attempt: Try progressive streams (has both video and audio but lower quality)
            stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
            
        if not stream:
            # Last resort: Any video stream available
            stream = yt.streams.filter(file_extension='mp4').order_by('resolution').desc().first()
            
        if not stream:
            raise Exception("No suitable video stream found for this URL")
        
        # Generate a unique filename to avoid conflicts
        unique_id = str(uuid.uuid4())[:8]
        safe_title = "".join([c if c.isalnum() else "_" for c in title])
        filename = f"{safe_title}_{unique_id}.mp4"
        file_path = os.path.join(DOWNLOAD_FOLDER, filename)
        
        # Download the video to the specified folder
        stream.download(output_path=DOWNLOAD_FOLDER, filename=filename)
        
        return file_path, filename
    except Exception as e:
        error_msg = f"Error downloading video: {str(e)}"
        st.error(error_msg)
        raise Exception(error_msg)

def cleanup_video(file_path):
    """Delete the video file after download"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
    except Exception as e:
        st.warning(f"Could not delete temporary file: {str(e)}")
        return False
    return False

st.title('YouTube Video Downloader')
st.write("Version: 1.0")
st.write("Enter a YouTube URL and press Enter or click the Download button")

url = st.text_input('Enter YouTube URL:')

# Add a download button
download_clicked = st.button('Get Video')

# No session state needed for the simplified download process

# Process the URL when entered or button clicked
if url and download_clicked:
    try:
        with st.spinner('Fetching video... This may take a while depending on the video size'):
            file_path, file_name = download_video(url)
            
        if file_path and os.path.exists(file_path):
            # Store download data in session state
            st.session_state.download_ready = True
            st.session_state.file_data = open(file_path, 'rb').read()
            st.session_state.file_name = file_name
            
            # Display success message first
            st.success('Video fetched successfully! Click the download button below.')
            
            # Schedule cleanup for next session
            if not os.path.exists('cleanup_list.txt'):
                with open('cleanup_list.txt', 'w') as f:
                    f.write(file_path + '\n')
            else:
                with open('cleanup_list.txt', 'a') as f:
                    f.write(file_path + '\n')
        else:
            st.error('Failed to download the video. File not found.')
    except Exception as e:
        st.error(f'Error: {str(e)}')

# Display download button if ready
if st.session_state.get('download_ready'):
    st.download_button(
        label='Save Video',
        data=st.session_state.file_data,
        file_name=st.session_state.file_name,
        mime='video/mp4',
        key='persistent_download'
    )

# Check for files that need cleanup from previous sessions
if os.path.exists('cleanup_list.txt'):
    try:
        with open('cleanup_list.txt', 'r') as f:
            files_to_cleanup = f.readlines()
        
        cleaned_files = []
        for file_path in files_to_cleanup:
            file_path = file_path.strip()
            if file_path and os.path.exists(file_path):
                cleanup_video(file_path)
                cleaned_files.append(file_path)
        
        # Update cleanup list
        if cleaned_files:
            with open('cleanup_list.txt', 'w') as f:
                for file_path in files_to_cleanup:
                    if file_path.strip() not in cleaned_files:
                        f.write(file_path)
    except Exception as e:
        st.warning(f"Could not perform cleanup: {str(e)}")
        pass