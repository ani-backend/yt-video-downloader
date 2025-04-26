from pytubefix import YouTube
import os
import ssl
import uuid

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

def get_available_streams(url):
    """Get all available streams categorized by type"""
    ssl._create_default_https_context = ssl._create_unverified_context
    yt = YouTube(url)
    
    streams = {
        'video': [],
        'audio': [],
        'progressive': []
    }
    
    for stream in yt.streams:
        if stream.type == 'video' and stream.audio_codec is None:
            streams['video'].append(stream)
        elif stream.type == 'audio':
            streams['audio'].append(stream)
        elif stream.type == 'video' and stream.audio_codec:
            streams['progressive'].append(stream)
    
    return streams, yt.title

def download_selected_stream(stream, title, download_dir):
    """Download the selected stream"""
    unique_id = str(uuid.uuid4())[:8]
    safe_title = "".join([c if c.isalnum() else "_" for c in title])
    filename = f"{safe_title}_{unique_id}.{stream.subtype}"
    file_path = os.path.join(download_dir, filename)
    
    stream.download(output_path=download_dir, filename=filename)
    return file_path, filename
