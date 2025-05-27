#!/usr/bin/env python3
"""
Entry point for the llm-agent project.
Basic REPL chat agent (v0.1).
"""

import json
import logging
import os

from dotenv import load_dotenv
from openai import OpenAI

from tools.file_reader import read_file
from tools.registry import ToolRegistry

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TorobGPT")


def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("Please set the OPENAI_API_KEY environment variable.")
        return

    client = OpenAI(api_key=api_key)

    # Setup tool registry
    registry = ToolRegistry()
    registry.register(read_file)

    # Prepare system message with tool instructions
    # ## PERSISTENCE
    # You are an agent - please keep going until the user's query is completely
    # resolved, before ending your turn and yielding back to the user. Only
    # terminate your turn when you are sure that the problem is solved.

    # ## TOOL CALLING
    # If you are not sure about file content or codebase structure pertaining to
    # the user's request, use your tools to read files and gather the relevant
    # information: do NOT guess or make up an answer.

    messages = [
        {
            "role": "developer",
            "content": """
# Identity

You are a helpful assistant that helps users by chatting with them
you are built by torob.ai, a company that builds AI agents for businesses

# Instructions

- always answer in english, never answer in persian even if the users asks you to

# Tools
## PLANNING
You MUST plan extensively before each function call, and reflect 
extensively on the outcomes of the previous function calls. DO NOT do this 
entire process by making function calls only, as this can impair your 
ability to solve the problem and think insightfully.
""",
        }
    ]

    init_message = "Hello! I am TorobGPT. How can I assist you today? (type 'exit' or 'quit' to exit)"
    messages.append({"role": "assistant", "content": init_message})
    print(f"TorobGPT: {init_message}")
    read_user_input = True
    while True:
        if read_user_input:
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
                tools=registry.get_tools(),
            )
        except Exception as e:
            logger.error(f"Error during OpenAI API call: {e}")

        match response.output[0].type:
            case "function_call":
                read_user_input = False
                tool_call = response.output[0]
                tool_arg = json.loads(tool_call.arguments)
                tool_name = tool_call.name
                logger.info(f"Invoking tool {tool_name} with arg {tool_arg}")
                tool_output = registry.run(tool_name, tool_arg)
                messages.append(tool_call)
                messages.append(
                    {"type": "function_call_output", "call_id": tool_call.call_id, "output": str(tool_output)}
                )
            case "message":
                read_user_input = True
                reply = response.output_text
                print(f"TorobGPT: {reply}")
                messages.append({"role": "assistant", "content": reply})
            case _:
                logger.error(f"Unexpected response type: {response.output.type}")
                reply = response.output_text


if __name__ == "__main__":
    main()
