# Contributing

## Setup

```bash
git clone https://github.com/brianpelow/ai-regulation-tracker
cd ai-regulation-tracker
uv sync
uv run pytest
```

## Run locally

```bash
export OPENROUTER_API_KEY=your_key
uv run python scripts/agent.py
```