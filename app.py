import streamlit as st
import json
from deep_translator import GoogleTranslator
import spacy
import langid
import subprocess

# Function to download SpaCy model if not already downloaded
def ensure_spacy_model_installed():
    try:
        spacy.cli.download("en_core_web_sm")
    except Exception as e:
        st.error(f"Error downloading SpaCy model: {e}")

# Ensure the SpaCy model is available
ensure_spacy_model_installed()

# Load SpaCy model for English
nlp = spacy.load("en_core_web_sm")

# Load the JSON data
try:
    with open('new.json') as f:
        data = json.load(f)
except FileNotFoundError:
    st.write("Error: 'new.json' file not found. Please make sure it is available.")
    data = {}  # Empty dictionary as fallback

def get_keywords(text):
    """Extract main keywords using NLP from the text."""
    doc = nlp(text)
    keywords = {token.lemma_ for token in doc if token.is_alpha and not token.is_stop}
    return keywords

def get_answer(question):
    """Get the answer to the given question using keyword search and NLP analysis."""
    keywords = get_keywords(question)
    response = "Sorry, I don't have an answer to that."

    # Function to check if keywords match any category in the data
    def check_keywords_in_data(category):
        for item, info in data.get(category, {}).items():
            if any(keyword.lower() in item.lower() for keyword in keywords):
                return info
        return None

    # Check in streams
    stream_info = check_keywords_in_data('streams')
    if stream_info:
        if 'eligibility' in question.lower():
            return stream_info.get('eligibility', 'No eligibility information available.')
        if 'exams' in question.lower() or 'परीक्षा' in question.lower():
            return stream_info.get('exams', 'No exam information available.')
        if 'path' in question.lower() or 'how to become' in question.lower():
            return stream_info.get('career_path', 'No pathway information available.')
        if 'colleges' in question.lower() or 'top colleges' in question.lower():
            top_colleges = stream_info.get('top_colleges', 'No college information available.')
            return format_college_response(top_colleges)
        return stream_info.get('career_options', 'No career options available.')

    # Check in professions
    profession_info = check_keywords_in_data('professions')
    if profession_info:
        if any(keyword in ['skills', 'कौशल्य', 'कौशल्ये'] for keyword in keywords):
            return profession_info.get('skills_required', 'No skills information available.')
        if 'exams' in question.lower() or 'परीक्षा' in question.lower():
            return profession_info.get('exams', 'No exam information available.')
        if 'eligibility' in question.lower():
            return profession_info.get('eligibility', 'No eligibility information available.')
        if 'path' in question.lower() or 'how to become' in question.lower():
            return profession_info.get('career_path', 'No pathway information available.')
        if 'colleges' in question.lower() or 'top colleges' in question.lower():
            top_colleges = profession_info.get('top_colleges', 'No college information available.')
            return format_college_response(top_colleges)
        return profession_info.get('description', 'No detailed info available.')

    # Check for government jobs
    gov_jobs = data.get('government_jobs', {})
    if any(keyword.lower() in job.lower() for job in gov_jobs.get('types', []) for keyword in keywords):
        if any(keyword in ['skills', 'कौशल्य', 'कौशल्ये'] for keyword in keywords):
            return gov_jobs.get('skills_required', 'No skills information available.')
        return f"Government job sectors include: {', '.join(gov_jobs['types'])}"

    # Check for vocational courses
    if 'vocational' in question.lower():
        vocational_info = data.get('Vocational', {})
        courses = vocational_info.get('courses', [])
        return format_vocational_courses(courses)

    # Check for diploma courses
    if 'diploma' in question.lower():
        diploma_info = data.get('Diploma', {})
        return format_diploma_info(diploma_info)

    return response

def format_college_response(colleges):
    """Format the response for college information."""
    if isinstance(colleges, dict):
        return "\n".join([f"{key}: {', '.join(value)}" for key, value in colleges.items()])
    return colleges

def format_vocational_courses(courses):
    """Format the response for vocational courses."""
    return "\n".join([f"{course['course_name']} ({course['duration']}) - Career Options: {', '.join(course['career_options'])}" for course in courses])

def format_diploma_info(diploma_info):
    """Format the response for diploma information."""
    return f"Subjects: {', '.join(diploma_info.get('subjects', []))}\nCareer Options: {', '.join(diploma_info.get('career_options', []))}"

def translate_text(text, dest):
    """Translate the given text to the destination language."""
    try:
        translated = GoogleTranslator(source='auto', target=dest).translate(text)
        return translated
    except Exception as e:
        print(f"Translation error: {e}")
        return text  # Return the original text on error

def detect_language(text):
    """Detect language using langid."""
    lang, _ = langid.classify(text)
    return lang

def main():
    st.title("Multilingual Chatbot")

    user_input = st.text_input("Ask your question (in Hindi, Marathi, or English):")

    if st.button("Submit"):
        if user_input:
            detected_lang = detect_language(user_input)

            if detected_lang == 'en':
                translated_input = user_input
            else:
                translated_input = translate_text(user_input, 'en')

            answer = get_answer(translated_input)

            if detected_lang != 'en':
                translated_answer = translate_text(answer, detected_lang)
            else:
                translated_answer = answer

            st.write(f"Answer: {translated_answer}")

if __name__ == "__main__":
    main()
