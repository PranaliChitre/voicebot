import streamlit as st
import speech_recognition as sr
import pyttsx3
import json
from deep_translator import GoogleTranslator
import spacy  # For NLP keyword extraction

# Load SpaCy model for keyword extraction
nlp = spacy.load("en_core_web_sm")

# Initialize the recognizer and TTS engine
recognizer = sr.Recognizer()
engine = pyttsx3.init()

# Load the JSON data
with open('new.json') as f:
    data = json.load(f)

def speak(text, lang):
    """Speak the given text in the specified language."""
    engine.setProperty('voice', lang)
    engine.say(text)
    try:
        engine.runAndWait()
    except RuntimeError:
        pass

def get_keywords(text):
    """Extract main keywords using NLP from the text."""
    doc = nlp(text)
    keywords = {token.lemma_ for token in doc if token.is_alpha and not token.is_stop}
    return keywords

def get_answer(question, original_lang):
    """Get the answer to the given question using keyword search and NLP analysis."""
    keywords = get_keywords(question)

    # Initialize a flag to track if a match is found
    match_found = False
    response = "Sorry, I don't have an answer to that."

    # Check for matches in educational streams
    for stream, info in data['streams'].items():
        if any(keyword.lower() in stream.lower() for keyword in keywords):
            match_found = True
            if 'eligibility' in question.lower():
                response = info.get('eligibility', 'No eligibility information available.')
            elif 'exams' in question.lower() or 'परीक्षा' in question.lower():
                response = info.get('exams', 'No exam information available.')
            elif 'path' in question.lower() or 'how to become' in question.lower():
                response = info.get('career_path', 'No pathway information available.')
            elif 'colleges' in question.lower() or 'top colleges' in question.lower():
                top_colleges = info.get('top_colleges', 'No college information available.')
                if isinstance(top_colleges, dict):
                    response = "Here are the top colleges:\n"
                    for category, colleges in top_colleges.items():
                        response += f"- **{category}**: {', '.join(colleges)}\n"
                else:
                    response = 'No college information available.'
            else:
                response = info.get('career_options', 'No career options available.')
            break  # Exit loop after finding a match

    # Check for matches in professions
    if not match_found:
        for profession, details in data['professions'].items():
            if any(keyword.lower() in profession.lower() for keyword in keywords):
                match_found = True
                if 'exams' in question.lower() or 'परीक्षा' in question.lower():
                    response = details.get('exams', 'No exam information available.')
                elif 'eligibility' in question.lower():
                    response = details.get('eligibility', 'No eligibility information available.')
                elif 'path' in question.lower() or 'how to become' in question.lower():
                    response = details.get('career_path', 'No pathway information available.')
                elif 'colleges' in question.lower() or 'top colleges' in question.lower():
                    top_colleges = details.get('top_colleges', 'No college information available.')
                    if isinstance(top_colleges, dict):
                        response = "Here are the top colleges:\n"
                        for category, colleges in top_colleges.items():
                            response += f"- **{category}**: {', '.join(colleges)}\n"
                    else:
                        response = 'No college information available.'
                else:
                    response = details.get('description', 'No detailed info available.')
                break  # Exit loop after finding a match

    # Check for matches in government jobs
    if not match_found:
        gov_jobs = data['government_jobs']
        if any(keyword.lower() in job.lower() for job in gov_jobs['types'] for keyword in keywords):
            match_found = True
            response = f"Government job sectors include: {', '.join(gov_jobs['types'])}"

    # Check for matches in vocational courses
    if not match_found:
        if 'vocational' in question.lower():
            match_found = True
            vocational_info = data['Vocational']
            courses = vocational_info.get('courses', [])
            response = "Vocational Courses:\n"
            for course in courses:
                response += f"- **{course['course_name']}**: Duration: {course['duration']}, Career Options: {', '.join(course['career_options'])}\n"
            response += "For more details on specific courses, please ask!"

    # Check for matches in diploma courses
    if not match_found:
        if 'diploma' in question.lower():
            match_found = True
            diploma_info = data['Diploma']
            if 'colleges' in question.lower() or 'top colleges' in question.lower():
                top_colleges = diploma_info.get('top_colleges', 'No college information available.')
                if isinstance(top_colleges, dict):
                    response = "Here are the top diploma colleges:\n"
                    for category, colleges in top_colleges.items():
                        response += f"- **{category}**: {', '.join(colleges)}\n"
                else:
                    response = 'No college information available.'
            else:
                response = f"Diploma Description: {diploma_info.get('description', 'No description available.')}\n"
                response += f"Subjects: {', '.join(diploma_info.get('subjects', []))}\n"
                response += f"Career Options: {', '.join(diploma_info.get('career_options', []))}\n"

    return response




def translate_text(text, dest):
    """Translate the given text to the destination language."""
    try:
        translated = GoogleTranslator(source='auto', target=dest).translate(text)
        return translated
    except Exception as e:
        st.write(f"Translation error: {e}")
        return text  # Return the original text on error

def speak(text, lang, filename="output.mp3"):
    """Speak the given text in the specified language and save to a file."""
    
    # Get available voices
    voices = engine.getProperty('voices')
    
    # Set voice based on the selected language
    if lang == 'hi-IN':  # Hindi
        for voice in voices:
            if 'hi' in voice.languages:
                engine.setProperty('voice', voice.id)
                break
    elif lang == 'mr-IN':  # Marathi
        for voice in voices:
            if 'mr' in voice.languages:
                engine.setProperty('voice', voice.id)
                break
    else:  # Default to English
        for voice in voices:
            if 'en' in voice.languages:
                engine.setProperty('voice', voice.id)
                break

    # Save the text to an audio file
    engine.save_to_file(text, filename)
    try:
        engine.runAndWait()
    except RuntimeError:
        pass

    # Play the generated audio file in Streamlit
    st.audio(filename)


def main():
    st.title("Multilingual Voicebot")
    st.write("Select a language:")
    lang = st.selectbox("Language", ["English", "Hindi", "Marathi"])

    lang_code = {
        "English": "en-US",
        "Hindi": "hi-IN",
        "Marathi": "mr-IN"
    }[lang]

    if st.button("Start Listening"):
        with sr.Microphone() as source:
            audio = recognizer.listen(source)

            try:
                # Recognize the speech and convert to text
                question = recognizer.recognize_google(audio, language=lang_code)
                st.write(f"You asked: {question}")

                # Translate the question to English if not already in English
                if lang != "English":
                    translated_question = translate_text(question, 'en')
                else:
                    translated_question = question

                # Get answer from JSON data using NLP analysis
                answer = get_answer(translated_question, lang)

                # Translate the answer back to the original language
                if lang != "English":
                    translated_answer = translate_text(answer, lang_code.split('-')[0])
                else:
                    translated_answer = answer

                # Display only the question and answer in the same language
                st.write(f"Question: {question}")
                st.write(f"Answer: {translated_answer}")

                speak(translated_answer, lang_code)
                
            except sr.UnknownValueError:
                st.write("Sorry, I could not understand the audio.")
            except sr.RequestError as e:
                st.write(f"Could not request results from Google Speech Recognition service; {e}")
            except Exception as e:
                st.write(f"An error occurred: {e}")


if __name__ == "__main__":
    main()