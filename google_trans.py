import os
from googleapiclient.discovery import build
from pydub import AudioSegment
import speech_recognition as sr
import yt_dlp as youtube_dl
import openai

# Replace with your own API keys
google_api_key = "my key"
openai_api_key = 'my key'

# Set up OpenAI API key
openai.api_key = openai_api_key

# Create a YouTube resource object
youtube = build('youtube', 'v3', developerKey=google_api_key)

def get_video_info(video_id):
    request = youtube.videos().list(
        part="snippet",
        id=video_id
    )
    response = request.execute()
    
    if not response['items']:
        print("No video found with the given ID.")
        return None
    
    return response['items'][0]['snippet']

def download_audio(video_url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'audio.%(ext)s',
        'noplaylist': True,
    }
    
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        return "audio.mp3"
    except Exception as e:
        print(f"Error downloading video: {e}")
        return None

def convert_audio(audio_file):
    try:
        audio = AudioSegment.from_file(audio_file)
        wav_file = "audio.wav"
        audio.export(wav_file, format="wav")
        os.remove(audio_file)  # Remove the original mp3 file
        return wav_file
    except Exception as e:
        print(f"Error converting audio: {e}")
        return None

def transcribe_audio_google(audio_file):
    recognizer = sr.Recognizer()
    audio = AudioSegment.from_wav(audio_file)
    duration = len(audio) // 1000
    print(duration)
    transcript = []

    for i in range(0, duration, 60):
        segment = audio[i*1000:(i+60)*1000]
        segment.export("temp.wav", format="wav")

        with sr.AudioFile("temp.wav") as source:
            audio_data = recognizer.record(source)
        
        try:
            text = recognizer.recognize_google(audio_data)
            transcript.append(text)
        except sr.UnknownValueError:
            transcript.append("[Unrecognized]")
        except sr.RequestError as e:
            transcript.append(f"[Request Error: {e}]")
    
    os.remove("temp.wav")
    return " ".join(transcript)

def transcribe_audio_openai(audio_file):
    audio_file= open(audio_file, "rb")
    transcription = openai.audio.transcriptions.create(
        model="whisper-1", 
        file=audio_file
        )
    return transcription.text

def get_transcription(video_url, service='google'):
    audio_file = download_audio(video_url)
    if audio_file is None:
        return "Failed to download audio."
    
    wav_file = convert_audio(audio_file)
    if wav_file is None:
        return "Failed to convert audio."
    
    if service == 'google':
        transcription = transcribe_audio_google(wav_file)
    elif service == 'openai':
        transcription = transcribe_audio_openai(wav_file)
    else:
        transcription = "Invalid transcription service specified."
    
    print(transcription)
    os.remove(wav_file)  # Clean up the wav file
    return transcription

# Replace with your YouTube Short URL
video_url = "https://www.youtube.com/shorts/smWNEH22uUU"
video_id = video_url.split('/')[-1]

# Get video info (optional, to verify the video details)
video_info = get_video_info(video_id)
if video_info:
    print("Video Title:", video_info['title'])
    print("Video Description:", video_info['description'])

# Choose the transcription service: 'google' or 'openai'
service = 'openai'

# Get the transcription
transcription = get_transcription(video_url, service=service)
print("Transcription:", transcription)
