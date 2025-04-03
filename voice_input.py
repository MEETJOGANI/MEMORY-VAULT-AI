import streamlit as st
import speech_recognition as sr
import tempfile
import os

def transcribe_voice():
    """
    Capture audio from a file upload and transcribe it using speech recognition.
    
    Returns:
        str: Transcribed text, or empty string if transcription fails
    """
    # Create a recognizer instance
    recognizer = sr.Recognizer()
    
    # Display instructions for voice input
    st.info("📢 **Voice Input Instructions**:  \n"
            "1. Record an audio file using any recorder app on your device  \n"
            "2. Save it as a WAV or MP3 file  \n"
            "3. Upload the file below  \n"
            "4. The system will transcribe your recording")
    
    # For web use, we'll use a file uploader instead of microphone
    # This is a temporary solution as st.microphone() is not available
    audio_file = st.file_uploader("Upload audio file for transcription", type=["wav", "mp3"], key="voice_input")
    
    if audio_file:
        temp_audio_path = None
        try:
            # Save the audio bytes to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio_file:
                temp_audio_file.write(audio_file.read())
                temp_audio_path = temp_audio_file.name
            
            # Open the temporary audio file with speech_recognition
            with sr.AudioFile(temp_audio_path) as source:
                audio_data = recognizer.record(source)
                
                # Transcribe using Google Web API
                text = recognizer.recognize_google(audio_data)
                
                return text
                
        except sr.UnknownValueError:
            st.error("Sorry, I could not understand the audio. Please ensure your recording is clear and try again.")
        except sr.RequestError as e:
            st.error(f"Could not request results from Google Speech Recognition service; {e}")
        except Exception as e:
            st.error(f"An error occurred during transcription: {e}")
        finally:
            # Ensure the temporary file is deleted
            if temp_audio_path and os.path.exists(temp_audio_path):
                try:
                    os.unlink(temp_audio_path)
                except Exception:
                    pass
    
    return ""


def transcribe_uploaded_audio(audio_file):
    """
    Transcribe an uploaded audio file.
    
    Args:
        audio_file: Streamlit UploadedFile object
        
    Returns:
        str: Transcribed text, or empty string if transcription fails
    """
    # Create a recognizer instance
    recognizer = sr.Recognizer()
    
    temp_audio_path = None
    try:
        # Save the uploaded file to a temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio_file:
            temp_audio_file.write(audio_file.read())
            temp_audio_path = temp_audio_file.name
        
        # Open the audio file with speech_recognition
        with sr.AudioFile(temp_audio_path) as source:
            audio_data = recognizer.record(source)
            
            # Transcribe using Google Web API
            text = recognizer.recognize_google(audio_data)
            
            return text
            
    except sr.UnknownValueError:
        st.error("Sorry, I could not understand the audio. Please ensure your recording is clear and try again.")
    except sr.RequestError as e:
        st.error(f"Could not request results from Google Speech Recognition service; {e}")
    except Exception as e:
        st.error(f"An error occurred during transcription: {e}")
    finally:
        # Ensure the temporary file is deleted
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.unlink(temp_audio_path)
            except Exception:
                pass
    
    return ""
