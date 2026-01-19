
import os
from google.cloud import vision
from google.oauth2 import service_account

# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "ans.json"

import re
import string

def clean_answer(a):
    # Remove question numbers like 1., 1), Q1, Question 1:
    a = re.sub(r'^(question\s*)?\(?q?\d+[\).:\s-]*', '', a, flags=re.IGNORECASE)

    # Convert to lowercase
    a = a.lower()

    # Remove punctuation
    a = a.translate(str.maketrans('', '', string.punctuation))

    # Remove extra spaces
    a = ' '.join(a.split())

    return a


def get_text_from_image(image_path:str):
    creds_json = os.getenv("GOOGLE_CLOUD_CREDENTIALS_JSON")
    if not creds_json:
        raise RuntimeError("Missing GOOGLE_CLOUD_CREDENTIALS_JSON")

    credentials_info = json.loads(creds_json)
    credentials = service_account.Credentials.from_service_account_info(
        credentials_info
    )

    client = vision.ImageAnnotatorClient(credentials=credentials)

    with open(image_path, "rb") as f:
        content = f.read()

    image = vision.Image(content=content)

    response = client.document_text_detection(image=image)

    return response.full_text_annotation.text


import json
import os
from google import genai
from google.genai import types


def generate(question:str, correct_answer:str, student_answer:str):
    client = genai.Client(
        api_key=os.getenv("GENAI_API_KEY")
    )

    prompt = f"""
You are a strict exam evaluator.

Question:
{question}

Correct Answer:
{correct_answer}

Student Answer:
{student_answer}


Evaluation rules:
- Compare the student answer ONLY with the correct answer.
- Check correctness, completeness, and clarity.
- Score out of 10.
- Do not give full marks unless all key points are present.

Return ONLY valid JSON in this format:
{{
  "score": number,
  "feedback": "short explanation",
  "missing_points": ["point1", "point2"]
}}
"""
    model = "gemini-2.5-flash"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=prompt),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=genai.types.Schema(
            type = genai.types.Type.OBJECT,
            required = ["score", "feedback", "missing_points"],
            properties = {
                "score": genai.types.Schema(
                    type = genai.types.Type.NUMBER,
                ),
                "feedback": genai.types.Schema(
                    type = genai.types.Type.STRING,
                ),
                "missing_points": genai.types.Schema(
                    type = genai.types.Type.ARRAY,
                    items = genai.types.Schema(
                        type = genai.types.Type.STRING,
                    ),
                ),
            },
        ),
    )

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config,
    )
    final_res = response.candidates[0].content.parts[0].text

    resp = json.loads(final_res)
    return resp

def check_and_generate(quertion_image_path:str, correct_answer_image_path:str, student_answer_image_path:str):
    qs = get_text_from_image(quertion_image_path)
    a = get_text_from_image(correct_answer_image_path)
    sa = get_text_from_image(student_answer_image_path)

    a = clean_answer(a)
    sa = clean_answer(sa)

    return generate(question=qs, correct_answer=a, student_answer=sa)

    

