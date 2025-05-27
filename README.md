# llm-agent

A simple AI agent framework that incrementally adds functionalities to interact with LLMs and external tools.

## Project Structure

```
llm-agent/
├── agent.py        # entry point
├── tools/          # directory for agent tools
├── README.md
├── requirements.txt
└── .gitignore
```

## Getting Started

1. Install UV:

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

1. Install dependencies:

   ```bash
   uv sync
   ```

2. Run the agent:

   ```bash
   uv run python agent.py
   ``` 