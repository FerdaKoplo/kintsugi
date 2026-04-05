from google.genai import types
from google import genai
import json

from sqlalchemy import null

client = genai.Client()


class VisualDiagnosisService:
    def diagnose(self, image_bytes: bytes, mime_type: str = "image/jpeg") -> dict:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                """Analyze this image and return ONLY a JSON object with:
                - object_type: what the item is
                - damage_type: type of damage detected
                - severity: low/medium/high
                - suggested_skill: skill needed to fix it
                - confidence: 0.0 to 1.0""",
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                max_output_tokens=500,
            ),
        )

        raw_text = response.text

        if not raw_text:
            raise ValueError("Gemini returned empty response")
        return json.loads(raw_text)
