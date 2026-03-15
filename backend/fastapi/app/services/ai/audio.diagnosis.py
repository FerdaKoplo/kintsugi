import json
import numpy as np
import librosa
from google import genai
from google.genai import types
from io import BytesIO

client = genai.Client()


class AudioDiagnosisService:
    def diagnose(self, audio_bytes: bytes) -> dict:
        y, sr = librosa.load(BytesIO(audio_bytes), sr=None)
        features = {
            "spectral_centroid": float(
                librosa.feature.spectral_centroid(y=y, sr=sr).mean()
            ),
            "zero_crossing_rate": float(librosa.feature.zero_crossing_rate(y).mean()),
            "mfcc": librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13).mean(axis=1).tolist(),
            "spectral_rolloff": float(
                librosa.feature.spectral_rolloff(y=y, sr=sr).mean()
            ),
        }

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav"),
                f"""Analyze this audio and the extracted features:
                {json.dumps(features, indent=2)}

                Return ONLY a JSON object with:
                - detected_issue: what's likely wrong
                - confidence: 0.0 to 1.0
                - suggested_skill: repair skill needed
                - frequency_analysis: brief description of what the frequencies indicate""",
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
