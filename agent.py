#!/usr/bin/env python3
"""
Entry point for the llm-agent project.
Basic REPL chat agent (v0.1).
"""

import logging
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
logger = logging.getLogger("TorobGPT")
logger.setLevel(logging.INFO)


def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("Please set the OPENAI_API_KEY environment variable.")
        return

    client = OpenAI(api_key=api_key)

    messages = [
        {
            "role": "developer",
            "content": "",
            #             "content": """
            # # Identity
            # You are a helpful assistant that helps users by chatting with them
            # you are built by torob.ai, a company that builds AI agents for businesses
            # # Instructions
            # - always answer in english, never answer in persian even if the users asks you to
            # """,
        }
    ]

    print("TorobGPT: Hello! I am TorobGPT. How can I assist you today? (type 'exit' or 'quit' to exit)")
    while True:
        user_input = input("you: ").strip()
        if user_input.lower() in ("exit", "quit"):
            print("TorobGPT: Goodbye!")
            break

        messages.append({"role": "user", "content": user_input})

        try:
            # o4-mini
            response = client.responses.create(
                model="gpt-4.1-mini",
                input=messages,
            )
            reply = response.output_text
            print(f"TorobGPT: {reply}")
        except Exception as e:
            logger.error(f"Error during OpenAI API call: {e}")


if __name__ == "__main__":
    main()
