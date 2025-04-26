import streamlit as st
from pytubefix import YouTube
import os
from commons import (
    get_available_streams,
    download_selected_stream,
    cleanup_video
)
# Create a dedicated downloads folder
DOWNLOAD_FOLDER = "youtube_downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)


st.title('YouTube Video Downloader')
st.write("Version: 2.0")
url = st.text_input('Enter YouTube URL:')

if 'streams' not in st.session_state:
    st.session_state.streams = None

if st.button('Show Available Formats'):
    if url:
        try:
            with st.spinner('Fetching available formats...'):
                streams, title = get_available_streams(url)
                st.session_state.streams = streams
                st.session_state.video_title = title
                st.success("Found available formats!")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    else:
        st.warning("Please enter a YouTube URL first")

if st.session_state.streams:
    st.subheader("Available Formats")
    
    format_type = st.radio("Select format type:", 
                         ['Progressive (Video+Audio)', 'Video Only', 'Audio Only'],
                         index=0)
    
    stream_list = []
    if format_type == 'Progressive (Video+Audio)':
        stream_list = st.session_state.streams['progressive']
    elif format_type == 'Video Only':
        stream_list = st.session_state.streams['video']
    elif format_type == 'Audio Only':
        stream_list = st.session_state.streams['audio']
    
    if len(stream_list) > 0:
        sorted_streams = sorted(stream_list, 
                              key=lambda s: (
                                  int(s.resolution[:-1]) 
                                  if s.resolution and s.resolution.endswith('p') 
                                  else int(s.abr[:-4]) if s.abr and s.abr.endswith('kbps') 
                                  else 0
                              ), 
                              reverse=True)
        
        selected = st.selectbox(
            "Select quality:",
            options=[f"{s.resolution or s.abr} ({s.mime_type})" for s in sorted_streams],
            index=0
        )
        
        selected_stream = sorted_streams[[f"{s.resolution or s.abr} ({s.mime_type})" for s in sorted_streams].index(selected)]
        
        if st.button('Prepare Selected Format'):
            try:
                with st.spinner('Preparing for download...'):
                    file_path, file_name = download_selected_stream(selected_stream, st.session_state.video_title, DOWNLOAD_FOLDER)
                
                if file_path and os.path.exists(file_path):
                    st.session_state.download_ready = True
                    st.session_state.file_data = open(file_path, 'rb').read()
                    st.session_state.file_name = file_name
                    st.success('Download ready! Click the download button below.')
                    
                    # Schedule cleanup for next session
                    if not os.path.exists('cleanup_list.txt'):
                        with open('cleanup_list.txt', 'w') as f:
                            f.write(file_path + '\n')
                    else:
                        with open('cleanup_list.txt', 'a') as f:
                            f.write(file_path + '\n')
            except Exception as e:
                st.error(f'Error: {str(e)}')
    else:
        st.warning("No streams available in this category")


# Display download button if ready
if st.session_state.get('download_ready'):
    st.download_button(
        label='Click to Download',
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