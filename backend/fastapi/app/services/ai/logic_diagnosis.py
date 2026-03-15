import json
from typing import Optional
from google import genai
from google.genai import types

client = genai.Client()

SYSTEM_PROMPT = """You are a repair diagnostic assistant.
Your goal is to identify what's wrong with an item through questions.
Always respond ONLY with a JSON object — never plain text."""


class LogicDiagnosisService:
    def __init__(self):
        self._sessions: dict[str, list] = {}

    def start_diagnosis(self, session_id: str, item_description: str) -> dict:
        self._sessions[session_id] = []

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"The user has a problem with: {item_description}. Ask ONE diagnostic question.",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                max_output_tokens=300,
            ),
        )

        raw_text = response.text

        if not raw_text:
            raise ValueError("Gemini returned empty response")

        result = json.loads(raw_text)

        self._sessions[session_id].append(
            types.Content(role="model", parts=[types.Part(text=response.text)])
        )
        return result

    def continue_diagnosis(self, session_id: str, user_answer: str) -> dict:
        if session_id not in self._sessions:
            raise ValueError("Session not found. Call start_diagnosis first.")

        history = self._sessions[session_id]
        history.append(types.Content(role="user", parts=[types.Part(text=user_answer)]))

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=history,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                max_output_tokens=500,
            ),
        )

        raw_text = response.text

        if not raw_text:
            raise ValueError("Gemini returned empty response")

        result = json.loads(raw_text)
        history.append(
            types.Content(role="model", parts=[types.Part(text=response.text)])
        )

        if result.get("is_complete"):
            del self._sessions[session_id]

        return result

    def clear_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
