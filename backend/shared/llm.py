"""One place for the Anthropic client and model name used by every project."""
import os
import anthropic

# Change the model for all projects here.
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
