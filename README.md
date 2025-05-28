# llm-agent

A simple AI agent framework that incrementally adds functionalities to interact with LLMs and external tools.

## Getting Started
0. (if you have macOS)
   ```bash
   brew install python3.12
   ```

1. Install UV:

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Install dependencies:

   ```bash
   uv sync
   ```

   on macos

   ```bash
   uv sync --python /opt/homebrew/bin/python3.12
   ```

3. Add openAi api key and optionaly logfire api key to Environment variables.

```
OPENAI_API_KEY
LOGFIRE_API_KEY (optional)
```

4. Run the agent:

   ```bash
   uv run python agent.py
   ``` 

## TODO:
- add more poetry.
- use pydanticAi.
- add user option to change model.
- add html interface
