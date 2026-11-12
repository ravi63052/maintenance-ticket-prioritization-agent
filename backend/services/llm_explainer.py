
import os
import json

from dotenv import load_dotenv
from google import genai

load_dotenv()


class LLMExplainer:

    def __init__(self):

        self.api_key = os.getenv("GEMINI_API_KEY")

        self.model = os.getenv(
            "GEMINI_MODEL",
            "gemini-3.8-flash"
        )

        self.client = (
            genai.Client(api_key=self.api_key)
            if self.api_key
            else None
        )

    def explain(self, ticket_analysis):

        if not self.client:
            return {
                "provider": "gemini",
                "status": "disabled",
                "explanation": "Gemini API key is missing."
            }

        instructions = """
        You are an AI assistant supporting
        renewable energy maintenance operations.

        Explain the ticket analysis clearly.

        Rules:
        1. Use only the provided ticket information.
        2. Do not modify the calculated severity.
        3. Do not modify the assigned team.
        4. Explain the assigned priority.
        5. Describe root causes as hypotheses.
        6. Never invent operational measurements.
        7. Highlight safety concerns.
        8. Keep the explanation concise.
        """

        prompt = (
            instructions
            + "\nTicket analysis:\n"
            + json.dumps(ticket_analysis, indent=2)
        )

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )

            return {
                "provider": "gemini",
                "status": "success",
                "model": self.model,
                "explanation": response.text
            }

        except Exception as error:

            print("Gemini API error:", str(error))

            return {
                "provider": "gemini",
                "status": "error",
                "explanation": "Gemini explanation unavailable."
            }
