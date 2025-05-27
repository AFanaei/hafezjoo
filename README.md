# llm-agent

A simple AI agent framework that incrementally adds functionalities to interact with LLMs and external tools.

## Project Structure

```
llm-agent/
├── agent.py        # entry point
├── tools/          # directory for agent tools
├── README.md
└── .gitignore
```

## Getting Started
0. (if you have macOS)
   ```bash
   brew install python3.12
   ```

1. Install UV:

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

1. Install dependencies:

   ```bash
   uv sync
   ```

   on macos

   ```bash
   uv sync --python /opt/homebrew/bin/python3.12
   ```

2. Run the agent:

   ```bash
   uv run python agent.py
   ``` 