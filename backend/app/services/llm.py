from google import genai
from app.config import settings


SUMMARY_PROMPT = """
You are a professional summarization assistant.

Analyze the transcript below and produce a concise, useful summary.

IMPORTANT:
- Do NOT copy the transcript.
- Do NOT repeat long sentences from the transcript.
- Synthesize the main ideas in your own words.
- Ignore greetings, introductions, YouTube promotions, calls to subscribe,
  repeated phrases, and filler speech unless they are essential to the meaning.
- Do not invent facts that are not supported by the transcript.
- Keep the summary concise.

Return exactly these sections:

### Executive Summary
Write 2-3 sentences describing the central purpose and content.

### Key Takeaways
- 3-5 concise points containing the most important ideas.

### Action Items & Next Steps
- List concrete actions mentioned or clearly implied by the transcript.
- If there are no meaningful action items, write:
  - None explicitly mentioned.

Transcript:
{transcript}
"""


class LLMService:
    def __init__(self, api_key: str = settings.GEMINI_API_KEY):
        self.api_key = api_key

        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    def generate_summary(self, transcript: str) -> str:
        """
        Generate a structured summary using Gemini.

        Gemini failures are surfaced instead of silently returning
        the transcript as a fake summary.
        """
        if not transcript or not transcript.strip():
            raise ValueError("Cannot summarize an empty transcript.")

        if not self.client:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured in the backend environment."
            )

        return self._call_gemini(transcript)

    def _call_gemini(self, transcript: str) -> str:
        prompt = SUMMARY_PROMPT.format(transcript=transcript)

        try:
            response = self.client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=prompt,
            )
        except Exception as e:
            raise RuntimeError(f"Gemini API request failed: {e}") from e

        if not response.text or not response.text.strip():
            raise RuntimeError("Gemini returned an empty summary.")

        return response.text.strip()


llm_service = LLMService()