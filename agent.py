"""
Nova's brain. Sends your message to Gemini together with the list of tools.
Gemini decides which tools to call, the SDK runs them, and Gemini turns the
results into a normal answer.

This file knows nothing about how things are displayed, so the same Agent
works in the terminal now and in a graphical interface later.
"""

import os
from datetime import datetime

from dotenv import load_dotenv
from google import genai
from google.genai import types

import tools

load_dotenv()

AGENT_NAME = os.getenv("AGENT_NAME", "Nova")
USER_NAME = os.getenv("USER_NAME", "Kevin")
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

SYSTEM_PROMPT = f"""You are {AGENT_NAME}, a personal assistant that runs on {USER_NAME}'s computer.

- Use your tools whenever they help answer the request. Don't guess system info, check it.
- Keep answers short and clear. Use simple formatting.
- Reply in the same language the user writes in (Slovenian or English).
- When reporting system status, highlight anything that looks wrong and suggest a fix.
- If a tool says the user cancelled, accept it and don't try again.
- Today is {datetime.now().strftime('%A, %d %B %Y')}.
"""


class MissingApiKey(Exception):
    pass


class Agent:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise MissingApiKey(
                "No GEMINI_API_KEY found. Copy .env.example to .env and paste your key in it.\n"
                "Get a free key at https://aistudio.google.com/apikey"
            )
        self.client = genai.Client(api_key=api_key)
        self.new_conversation()

    def new_conversation(self):
        """Start a fresh chat. Nova forgets everything said so far (notes stay saved)."""
        self.chat = self.client.chats.create(
            model=MODEL,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=tools.ALL_TOOLS,  # the SDK calls these Python functions for us
            ),
        )

    def ask(self, message: str) -> str:
        """Send one message and return Nova's answer."""
        response = self.chat.send_message(message)
        return response.text or "(no answer)"
