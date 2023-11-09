import streamlit as st
import os
import tempfile
import time
import requests
from pytube import YouTube
from supabase import create_client, Client

# Set up the API endpoint and headers
base_url = "https://api.assemblyai.com/v2"
headers = {
    "authorization": os.environ.get("ASSEMBLYAI_API_KEY"),
    "content-type": "application/json"
}

# Your Supabase credentials
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Create a Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def convert_ms_to_time(milliseconds):
    seconds = milliseconds // 1000
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    time_str = f"{hours:02}:{minutes:02}:{seconds:02}"
    return time_str

def fetch_transcribed_videos():
    data = supabase.table("transcripts").select("*").execute()
    videos = {d['content_name']: d['transcript_id'] for d in data.data}
    return videos

def save_transcript(video_name, transcript_id):
    supabase.table("transcripts").insert({"content_name": video_name, "transcript_id": transcript_id}).execute()

def ask_question(transcript_id, question_text):
    lemur_params = {
        "transcript_ids": [transcript_id],
        "prompt": question_text
    }
    lemur_url = "https://api.assemblyai.com/lemur/v3/generate/task"
    lemur_response = requests.post(lemur_url, json=lemur_params, headers=headers)
    lemur_result = lemur_response.json()

    if "error" in lemur_result:
        raise RuntimeError(f"Error: {lemur_result['error']}")
    return lemur_result['response']

# Function to handle audio file upload and transcription
def transcribe_uploaded_audio(uploaded_file, episode_name):
    if uploaded_file is not None:
        # To read file as bytes:
        bytes_data = uploaded_file.getvalue()
        # You can now process this file and transcribe it
        temp_dir = tempfile.mkdtemp()
        audio_path = os.path.join(temp_dir, uploaded_file.name)
        with open(audio_path, "wb") as f:
            f.write(bytes_data)
        
        # Now you can transcribe using the same function you use for YouTube
        transcript_text, transcript_id = transcribe_audio(audio_path)
        os.remove(audio_path)  # Clean up the audio file

        # Save the episode name and transcript ID to your database
        save_transcript(episode_name, transcript_id)
        
        return transcript_text, transcript_id
    return "", ""

def download_youtube_audio(url):
    yt = YouTube(url)
    video_name = yt.title
    audio_stream = yt.streams.filter(only_audio=True).first()
    temp_dir = tempfile.mkdtemp()
    audio_path = os.path.join(temp_dir, "video123.mp4")
    audio_stream.download(filename=audio_path)
    return audio_path, video_name

def transcribe_audio(file_path):
    # Upload the audio file
    with open(file_path, "rb") as f:
        upload_response = requests.post(base_url + "/upload", headers=headers, data=f)
    upload_url = upload_response.json()["upload_url"]

    # Request transcription
    transcription_request_data = {
        "audio_url": upload_url,
        "auto_chapters": True  # To match your original configuration
    }
    transcription_response = requests.post(base_url + "/transcript", json=transcription_request_data, headers=headers)
    transcript_id = transcription_response.json()['id']

    # Poll for transcription result
    polling_endpoint = base_url + "/transcript/" + transcript_id
    while True:
        transcription_result = requests.get(polling_endpoint, headers=headers).json()
        if transcription_result['status'] == 'completed':
            return transcription_result['text'], transcript_id
        elif transcription_result['status'] == 'error':
            raise RuntimeError(f"Transcription failed: {transcription_result['error']}")
        time.sleep(5)  # Adjusted to 5 seconds to match your original code

    raise TimeoutError("Transcription took too long to complete.")


# Streamlit app layout
st.title("Audio + Video Transcriber and Q&A")

# Create tabs for Transcription and Q&A
tab1, tab2, tab3 = st.tabs(["Transcribe New Youtube Video", "Transcribe New File", "Q&A on Existing Transcripts"])

with tab1:
    st.header("Transcribe New YouTube Video")
    youtube_url = st.text_input("Enter the YouTube video URL")
    if st.button("Transcribe"):
        try:
            with st.spinner("Downloading and processing audio..."):
                audio_file_path, video_name = download_youtube_audio(youtube_url)
                transcript_text, transcript_id = transcribe_audio(audio_file_path)
                save_transcript(video_name, transcript_id)
                os.remove(audio_file_path)
            st.text_area("Transcription", value=transcript_text, height=300)
        except Exception as e:
            st.error(f"An error occurred: {e}")

# Create an additional tab for Transcribing New Podcast
with tab2:
    episode_name = st.text_input("Enter the podcast episode name")
    uploaded_file = st.file_uploader("Upload a podcast audio file", type=['mp3', 'wav', 'aac', 'm4a'])
    if st.button("Transcribe Podcast"):
        if episode_name and uploaded_file:
            try:
                with st.spinner("Transcribing audio..."):
                    transcript_text, transcript_id = transcribe_uploaded_audio(uploaded_file, episode_name)
                    if transcript_text and transcript_id:
                        st.text_area("Transcription", value=transcript_text, height=300)
                        save_transcript(episode_name, transcript_id)
            except Exception as e:
                st.error(f"An error occurred: {e}")
        else:
            st.error("Please enter an episode name and upload a file to transcribe.")

with tab3:
    st.header("Q&A on Existing Transcripts")
    transcribed_videos = fetch_transcribed_videos()
    selected_video_name = st.selectbox("Select a video to question", options=[""] + list(transcribed_videos.keys()))
    if selected_video_name:
        selected_transcript_id = transcribed_videos[selected_video_name]
        question = st.text_area("Ask a question about the selected transcript")
        if st.button("Get Answer"):
            try:
                with st.spinner("Fetching answer for the existing transcript..."):
                    answer = ask_question(selected_transcript_id, question)
                    st.write(answer)
            except Exception as e:
                st.error(f"An error occurred: {e}")
        if st.button("Get Chapters"):
            try:
                with st.spinner("Fetching chapters for the existing transcript..."):
                    t = aai.Transcript.get_by_id(selected_transcript_id)
                    for chapter in t.chapters:
                        st.write(f"{convert_ms_to_time(chapter.start)} - {chapter.summary}")
            except Exception as e:
                st.error(f"An error occurred: {e}")

# Sidebar for additional information or actions if necessary
with st.sidebar:
    st.write("Navigate between the tabs to transcribe a new video or to conduct Q&A on existing transcripts.")
