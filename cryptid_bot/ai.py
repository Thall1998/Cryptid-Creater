from openai import OpenAI

from cryptid_bot.config import Settings
from cryptid_bot.prompts import load_prompt


# This class keeps all AI-related code in one place.
# Discord commands call these methods instead of talking to OpenAI directly.
class CryptidStoryAI:
    def __init__(self, settings: Settings):
        # Save settings so every method can use the selected model/API key.
        self.settings = settings

        # Create the OpenAI client once when the bot starts.
        self.client = OpenAI(api_key=settings.openai_api_key)

    def create_cryptid(self, idea: str, tone: str | None = None) -> str:
        # Generates a full cryptid profile using the cryptid_creator prompt file.
        return self._generate(
            template_name="cryptid_creator",
            user_input={
                "idea": idea,
                # If the user does not provide a tone, use a default genre tone.
                "tone": tone or "eerie regional folklore with grounded horror",
            },
        )

    def create_origin(self, name: str, details: str) -> str:
        # Generates a legend/origin story for an existing cryptid.
        return self._generate(
            template_name="origin_story",
            user_input={
                "name": name,
                "details": details,
            },
        )

    def create_sighting(self, location: str, details: str) -> str:
        # Generates a field-report-style witness account.
        return self._generate(
            template_name="sighting_report",
            user_input={
                "location": location,
                "details": details,
            },
        )

    def _generate(self, template_name: str, user_input: dict[str, str]) -> str:
        # The system prompt controls the AI's role, style, and output format.
        system_prompt = load_prompt(template_name)

        # Convert the command arguments into a clean text block for the AI.
        # Example:
        # idea: deer-like creature
        # tone: swamp horror
        prompt_lines = [f"{key}: {value}" for key, value in user_input.items()]
        user_prompt = "\n".join(prompt_lines)

        # Send the request to the selected AI model.
        response = self.client.responses.create(
            model=self.settings.openai_model,
            instructions=system_prompt,
            input=user_prompt,
        )

        # output_text is the final generated text we send back to Discord.
        return response.output_text.strip()
