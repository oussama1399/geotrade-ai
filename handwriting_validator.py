import pytesseract
import json
import requests
import os
from datetime import datetime
from PIL import Image
from typing import List, Dict, Tuple

# You can replace pytesseract with a more advanced model if available, e.g., GPT-OSS or a deep learning OCR API


def extract_handwritten_fields_with_llm(
    image_path: str,
    required_fields: List[str],
    model: str = "gpt-oss:20b",
    base_url: str = "http://localhost:11434"
) -> Tuple[bool, Dict[str, str], List[str]]:
    """
    Reads a document image, extracts handwritten text, and uses a local LLM to check for missing required fields.
    Args:
        image_path (str): Path to the image file.
        required_fields (List[str]): List of required field names to check in the document.
        model (str): LLM model name for Ollama.
        base_url (str): Ollama base URL.
    Returns:
        Tuple[bool, Dict[str, str], List[str]]: (is_valid, extracted_fields, missing_fields)
    """
    # Step 1: OCR extraction
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image, lang='eng')

    # Step 2: Use LLM to extract fields and check for missing ones
    prompt = f"""
    You are an expert document validator. The following is the OCR text from a scanned document. 
    Your task is to extract the values for these required fields: {required_fields}.
    Return a JSON object with exactly two keys:
    1. "extracted_fields": A dictionary where keys are the field names and values are the extracted text.
    2. "missing_fields": A list of field names that could not be found or are empty.

    OCR TEXT:
    {text}
    """

    # Call Ollama LLM
    payload = {
        "model": model,
        "prompt": prompt,
        "format": "json",
        "stream": False
    }
    
    base_url = base_url.rstrip('/')
    result_details = {
        "timestamp": datetime.now().isoformat(),
        "image_path": image_path,
        "required_fields": required_fields,
        "ocr_text": text,
        "method": "LLM"
    }

    try:
        response = requests.post(f"{base_url}/api/generate", json=payload)
        response.raise_for_status()
        result = response.json()
        llm_response = result.get("response", "")
        data = json.loads(llm_response)
        extracted_fields = data.get("extracted_fields", {})
        missing_fields = data.get("missing_fields", [])
        is_valid = len(missing_fields) == 0
        
        result_details.update({
            "is_valid": is_valid,
            "extracted_fields": extracted_fields,
            "missing_fields": missing_fields,
            "llm_raw_response": llm_response
        })
    except Exception as e:
        print(f"LLM extraction failed or Ollama not reachable: {e}")
        # Fallback: basic extraction
        extracted_fields = {}
        for line in text.split('\n'):
            if ':' in line:
                field, value = line.split(':', 1)
                field = field.strip().lower()
                value = value.strip()
                extracted_fields[field] = value
        missing_fields = [f for f in required_fields if f.lower() not in extracted_fields]
        is_valid = len(missing_fields) == 0
        
        result_details.update({
            "method": "FALLBACK_OCR",
            "is_valid": is_valid,
            "extracted_fields": extracted_fields,
            "missing_fields": missing_fields,
            "error": str(e)
        })

    # Save to JSON
    with open("extraction_result.json", "w") as f:
        json.dump(result_details, f, indent=4)
        print(f"Results saved to extraction_result.json")

    return is_valid, extracted_fields, missing_fields


if __name__ == "__main__":
    import os
    required_fields = ["name", "date of birth", "address"]
    image_path = "image.png"
    
    if not os.path.exists(image_path):
        print(f"ERROR: {image_path} not found in the current directory.")
        # Create a dummy image for testing if possible, or just warn
    else:
        try:
            is_valid, extracted_fields, missing_fields = extract_handwritten_fields_with_llm(image_path, required_fields)
            print("Valid document:", is_valid)
            print("Extracted fields:", extracted_fields)
            print("Missing fields:", missing_fields)
        except Exception as e:
            print(f"Exception occurred: {e}")

