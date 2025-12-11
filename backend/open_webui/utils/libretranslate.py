import logging
import os
from typing import List, Dict, Optional
import requests

log = logging.getLogger(__name__)

# LibreTranslate base URL from environment or default
LIBRETRANSLATE_BASE_URL = os.environ.get("LIBRETRANSLATE_BASE_URL", "http://localhost:9000")
LIBRETRANSLATE_API_KEY = os.environ.get("LIBRETRANSLATE_API_KEY", "")

# Maximum text length for single translation request (LibreTranslate limit)
MAX_TEXT_LENGTH = 5000


class LibreTranslateError(Exception):
    """Custom exception for LibreTranslate errors"""
    pass


def get_languages() -> List[Dict]:
    """
    Fetch available languages from LibreTranslate.

    Returns:
        List of language dictionaries with 'code' and 'name' keys
        Example: [{"code": "en", "name": "English"}, {"code": "de", "name": "German"}]

    Raises:
        LibreTranslateError: If unable to connect or fetch languages
    """
    try:
        params = {}
        if LIBRETRANSLATE_API_KEY:
            params["api_key"] = LIBRETRANSLATE_API_KEY

        response = requests.get(
            f"{LIBRETRANSLATE_BASE_URL}/languages",
            params=params,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        log.error(f"Cannot connect to LibreTranslate at {LIBRETRANSLATE_BASE_URL}")
        raise LibreTranslateError(
            "Translation service unavailable. Please ensure LibreTranslate is running."
        )
    except requests.exceptions.Timeout:
        log.error("LibreTranslate request timed out")
        raise LibreTranslateError("Translation service is not responding.")
    except requests.exceptions.RequestException as e:
        log.error(f"Error fetching languages from LibreTranslate: {e}")
        raise LibreTranslateError("Failed to fetch available languages.")


def detect_language(text: str) -> Dict:
    """
    Auto-detect the language of the provided text.

    Args:
        text: Text to detect language from

    Returns:
        Dictionary with 'language' (code) and 'confidence' (0-1)
        Example: {"language": "en", "confidence": 0.95}

    Raises:
        LibreTranslateError: If detection fails
    """
    if not text or not text.strip():
        return {"language": "en", "confidence": 0.0}

    try:
        payload = {"q": text[:1000]}  # Limit to first 1000 chars for detection
        if LIBRETRANSLATE_API_KEY:
            payload["api_key"] = LIBRETRANSLATE_API_KEY

        response = requests.post(
            f"{LIBRETRANSLATE_BASE_URL}/detect",
            json=payload,
            timeout=10
        )
        response.raise_for_status()

        # LibreTranslate returns array of detections, take the first one
        detections = response.json()
        if detections and len(detections) > 0:
            return {
                "language": detections[0]["language"],
                "confidence": detections[0]["confidence"]
            }
        return {"language": "en", "confidence": 0.0}

    except requests.exceptions.ConnectionError:
        log.error(f"Cannot connect to LibreTranslate at {LIBRETRANSLATE_BASE_URL}")
        raise LibreTranslateError(
            "Translation service unavailable. Please ensure LibreTranslate is running."
        )
    except requests.exceptions.RequestException as e:
        log.error(f"Error detecting language: {e}")
        raise LibreTranslateError("Failed to detect language.")


def translate_text(text: str, source: str, target: str) -> Dict:
    """
    Translate text from source language to target language.
    Handles long texts by chunking if necessary.

    Args:
        text: Text to translate
        source: Source language code (use 'auto' for auto-detection)
        target: Target language code

    Returns:
        Dictionary with 'translatedText' and optionally 'detectedLanguage'
        Example: {"translatedText": "Hallo Welt", "detectedLanguage": "en"}

    Raises:
        LibreTranslateError: If translation fails
    """
    if not text or not text.strip():
        return {"translatedText": "", "detectedLanguage": source if source != "auto" else None}

    if not target:
        raise LibreTranslateError("Target language is required.")

    try:
        # If text is short enough, translate in one request
        if len(text) <= MAX_TEXT_LENGTH:
            return _translate_single(text, source, target)

        # For longer texts, split into chunks
        chunks = _split_text_into_chunks(text, MAX_TEXT_LENGTH)
        translated_chunks = []
        detected_language = None

        for chunk in chunks:
            result = _translate_single(chunk, source, target)
            translated_chunks.append(result["translatedText"])
            if not detected_language and "detectedLanguage" in result:
                detected_language = result["detectedLanguage"]

        response = {"translatedText": " ".join(translated_chunks)}
        if detected_language:
            response["detectedLanguage"] = detected_language

        return response

    except LibreTranslateError:
        raise
    except Exception as e:
        log.error(f"Unexpected error during translation: {e}")
        raise LibreTranslateError("Translation failed due to unexpected error.")


def _translate_single(text: str, source: str, target: str) -> Dict:
    """
    Internal function to translate a single chunk of text.
    """
    try:
        payload = {
            "q": text,
            "source": source,
            "target": target,
            "format": "text"
        }
        if LIBRETRANSLATE_API_KEY:
            payload["api_key"] = LIBRETRANSLATE_API_KEY

        response = requests.post(
            f"{LIBRETRANSLATE_BASE_URL}/translate",
            json=payload,
            timeout=30
        )
        response.raise_for_status()

        result = response.json()
        translated = result.get("translatedText", "")

        response_data = {"translatedText": translated}

        # If source was 'auto', include detected language
        if source == "auto" and "detectedLanguage" in result:
            detected = result["detectedLanguage"]
            if detected and "language" in detected:
                response_data["detectedLanguage"] = detected["language"]

        return response_data

    except requests.exceptions.ConnectionError:
        log.error(f"Cannot connect to LibreTranslate at {LIBRETRANSLATE_BASE_URL}")
        raise LibreTranslateError(
            "Translation service unavailable. Please ensure LibreTranslate is running."
        )
    except requests.exceptions.Timeout:
        log.error("Translation request timed out")
        raise LibreTranslateError("Translation request timed out.")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            raise LibreTranslateError("Invalid translation request. Check language codes.")
        elif e.response.status_code == 403:
            raise LibreTranslateError("Translation request forbidden. Check API key.")
        elif e.response.status_code == 429:
            raise LibreTranslateError("Rate limit exceeded. Please try again later.")
        else:
            raise LibreTranslateError(f"Translation failed: {str(e)}")
    except requests.exceptions.RequestException as e:
        log.error(f"Error during translation: {e}")
        raise LibreTranslateError("Translation failed.")


def translate_file(file_path: str, source: str, target: str) -> bytes:
    """
    Translate a file using LibreTranslate's file translation endpoint.

    Args:
        file_path: Path to the file to translate
        source: Source language code (use 'auto' for auto-detection)
        target: Target language code

    Returns:
        Translated file content as bytes

    Raises:
        LibreTranslateError: If file translation fails
    """
    if not os.path.exists(file_path):
        raise LibreTranslateError("File not found.")

    if not target:
        raise LibreTranslateError("Target language is required.")

    try:
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {
                'source': source,
                'target': target
            }
            if LIBRETRANSLATE_API_KEY:
                data['api_key'] = LIBRETRANSLATE_API_KEY

            response = requests.post(
                f"{LIBRETRANSLATE_BASE_URL}/translate_file",
                files=files,
                data=data,
                timeout=60
            )
            response.raise_for_status()

            return response.content

    except requests.exceptions.ConnectionError:
        log.error(f"Cannot connect to LibreTranslate at {LIBRETRANSLATE_BASE_URL}")
        raise LibreTranslateError(
            "Translation service unavailable. Please ensure LibreTranslate is running."
        )
    except requests.exceptions.Timeout:
        log.error("File translation request timed out")
        raise LibreTranslateError("File translation timed out. Try a smaller file.")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            raise LibreTranslateError("Invalid file or unsupported file type.")
        elif e.response.status_code == 403:
            raise LibreTranslateError("File translation forbidden. Check API key.")
        elif e.response.status_code == 413:
            raise LibreTranslateError("File too large for translation.")
        elif e.response.status_code == 429:
            raise LibreTranslateError("Rate limit exceeded. Please try again later.")
        else:
            raise LibreTranslateError(f"File translation failed: {str(e)}")
    except requests.exceptions.RequestException as e:
        log.error(f"Error during file translation: {e}")
        raise LibreTranslateError("File translation failed.")
    except Exception as e:
        log.error(f"Unexpected error during file translation: {e}")
        raise LibreTranslateError("File translation failed due to unexpected error.")


def _split_text_into_chunks(text: str, max_length: int) -> List[str]:
    """
    Split text into chunks at sentence boundaries to avoid breaking mid-sentence.

    Args:
        text: Text to split
        max_length: Maximum length per chunk

    Returns:
        List of text chunks
    """
    if len(text) <= max_length:
        return [text]

    chunks = []
    current_chunk = ""

    # Split by sentences (simple approach using common sentence endings)
    sentences = text.replace("! ", "!|").replace("? ", "?|").replace(". ", ".|").split("|")

    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_length:
            current_chunk += sentence
        else:
            if current_chunk:
                chunks.append(current_chunk)
            # If a single sentence is longer than max_length, split it anyway
            if len(sentence) > max_length:
                words = sentence.split()
                temp_chunk = ""
                for word in words:
                    if len(temp_chunk) + len(word) + 1 <= max_length:
                        temp_chunk += (word + " ")
                    else:
                        if temp_chunk:
                            chunks.append(temp_chunk.strip())
                        temp_chunk = word + " "
                current_chunk = temp_chunk
            else:
                current_chunk = sentence

    if current_chunk:
        chunks.append(current_chunk)

    return chunks
