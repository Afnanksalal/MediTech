import logging
import json
import os
import tempfile
from io import BytesIO
from sanic import Sanic
from sanic import response
from sanic.request import Request
from sanic.response import JSONResponse
from transformers import pipeline
from langdetect import detect
import requests
import anthropic
import librosa  # Only librosa is needed for audio loading
from dotenv import load_dotenv  # Import dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging for better error tracking
logging.basicConfig(level=logging.ERROR)

app = Sanic(__name__)

# Load machine learning models (outside the route handler for performance)
try:
    pipe_en = pipeline(
        "automatic-speech-recognition", model="openai/whisper-small"
    )
    pipe_ml = pipeline(
        "automatic-speech-recognition",
        model="kavyamanohar/whisper-small-malayalam",
    )
    pipe_translate = pipeline(
        "translation", model="Helsinki-NLP/opus-mt-ml-en"
    )

except Exception as e:
    logging.error(f"Error loading models: {e}")
    raise

# --- Anthropic API Setup ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")  # Load API key from .env file
if not ANTHROPIC_API_KEY:
    raise ValueError(
        "Please set the ANTHROPIC_API_KEY environment variable."
    )

# Instantiate the Anthropic client
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
# ------------------------


# Function to clean and extract EMR data using Anthropic API
def extract_emr(text):
    prompt = (
        f"\n\nHuman: You are a helpful medical assistant.\n"
        f"Please extract and structure relevant Electronic Medical Record (EMR) information from the following text.\n"
        f"If the text seems like gibberish, try to guess what it means in the context of medical information.\n"
        f"Focus on:\n"
        f"- Disease: Any mentioned illnesses or health conditions.\n"
        f"- Allergy: Any mentioned allergies.\n"
        f"- Timeline: Any dates, durations, or time-related information about the medical context.\n"
        f"- Medical History: Any past medical conditions or treatments.\n"
        f"\nText: {text}\n\n"
        f"Output:\n"
        f"```json\n"
        f'{{"disease": "...", "allergy": "...", "timeline": "...", "medical_history": "..."}}\n'
        f"```\n\nAssistant:"
    )

    try:
        response = anthropic_client.completions.create(
            model="claude-2.1",
            max_tokens_to_sample=256,
            prompt=prompt,
        )

        # Extract and clean the JSON response
        emr_data_str = (
            response.completion.split("```json")[1]
            .split("```")[0]
            .strip()
        )
        emr_data = json.loads(emr_data_str)

        # Additional cleaning and formatting:
        for key, value in emr_data.items():
            emr_data[key] = (
                value.strip()
                .replace("\n", " ")
                .replace("  ", " ")
            )
            if emr_data[key] == "":
                emr_data[key] = "N/A"

        return emr_data

    except Exception as e:
        logging.error(f"Error extracting EMR data: {e}")
        return {
            "disease": f"N/A (Error: {str(e)})",
            "allergy": f"N/A (Error: {str(e)})",
            "timeline": f"N/A (Error: {str(e)})",
            "medical_history": f"N/A (Error: {str(e)})",
        }


# Function to generate suggestions using Anthropic API
def generate_suggestions(emr_data):
    emr_data_str = json.dumps(emr_data)
    prompt = (
        f"\n\nHuman: You are a helpful medical assistant. \n"
        f"Based on the following EMR data, suggest potential treatments and medications. \n"
        f'If you cannot make a suggestion, respond with "N/A" for both treatment and medication suggestions.\n'
        f"\nEMR Data: \n{emr_data_str}\n"
        f"\nOutput:\n"
        f"```json\n"
        f'{{"treatment_suggestion": "...", "medicine_suggestion": "..."}}\n'
        f"```\n\nAssistant:"
    )

    try:
        response = anthropic_client.completions.create(
            model="claude-2.1",
            max_tokens_to_sample=256,
            prompt=prompt,
        )

        # Extract and clean the JSON response
        suggestions_str = (
            response.completion.split("```json")[1]
            .split("```")[0]
            .strip()
        )
        suggestions = json.loads(suggestions_str)

        # Additional cleaning and formatting:
        for key, value in suggestions.items():
            suggestions[key] = (
                value.strip()
                .replace("\n", " ")
                .replace("  ", " ")
            )
            if suggestions[key] == "":
                suggestions[key] = "N/A"

        return suggestions

    except Exception as e:
        logging.error(f"Error generating suggestions: {e}")
        return {
            "treatment_suggestion": f"N/A (Error: {str(e)})",
            "medicine_suggestion": f"N/A (Error: {str(e)})",
        }


@app.route("/")
async def test(request):
    return response.json({"test": True})


@app.route("/asr", methods=["POST"])
async def transcribe(request: Request) -> JSONResponse:
    audio_file = request.files.get("audio")
    if not audio_file:
        return JSONResponse({"error": "No audio file provided."}, status=400)

    try:
        # 1. Language Detection and Audio Loading
        try:
            with tempfile.NamedTemporaryFile(
                suffix=".wav", delete=False
            ) as temp_audio:
                temp_audio.write(audio_file.body)
                print(f"Debug - Audio saved to: {temp_audio.name}")

                # Load audio using librosa
                audio_array, sr = librosa.load(temp_audio.name, sr=None)

            # Resample audio to 16000 Hz
            target_sr = 16000
            audio_array = librosa.resample(
                audio_array, orig_sr=sr, target_sr=target_sr
            )

            text_snippet = pipe_en(audio_array)["text"][:200]
            detected_lang = detect(text_snippet)

            print(f"Detected Language: {detected_lang}")

        except Exception as e:
            print(
                f"Language detection failed: {str(e)} - Defaulting to Malayalam"
            )
            detected_lang = "ml"  # Default to Malayalam if detection fails

        # 2. Choose Speech Recognition Pipeline
        pipe = pipe_en if detected_lang == "en" else pipe_ml

        # 3. Perform Speech Recognition (no sampling_rate argument)
        transcription = pipe(audio_array)["text"]

        # 4. Translate to English if necessary
        if detected_lang != "en":
            translation_output = pipe_translate(transcription)
            english_text = translation_output[0]["translation_text"]
            print(f"Text: {transcription}")
            print(f"Text: {english_text}")
        else:
            english_text = transcription
            print(f"Text: {english_text}")

        # 5. Extract EMR data using Anthropic API
        emr_data = extract_emr(english_text)
        print(f"Extracted EMR Data: {emr_data}")

        # 6. Generate suggestions from EMR data
        suggestions = generate_suggestions(emr_data)
        print(f"Generated Suggestions: {suggestions}")

        # 7. Prepare and send the response
        response_data = {
            "transcription": transcription,
            "translation": english_text,
            "emr_data": emr_data,
            "suggestions": suggestions,
        }
        return JSONResponse(response_data)

    except Exception as e:
        return JSONResponse({"error": f"Error: {str(e)}"}, status=500)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
