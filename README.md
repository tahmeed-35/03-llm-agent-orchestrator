# Modular LLM Agent Orchestration & Tool-Calling

A modular, config-driven agent execution engine implementing an autonomous tool-calling loop, exponential backoff retries, configurable timeouts, and structured JSON telemetry.

## Key Features

- **Extensible Tool Registry**: `@registry.register` decorator pattern that automatically extracts tool descriptions and parameter types into standard function-calling schemas.
- **YAML Config Driven**: Control iterations, backoff parameters, model selection, timeouts, and tool permissions without changing code.
- **Async API Wrapper with Exponential Backoff**: Resilient execution handling network timeouts and HTTP 429/5xx status codes with configurable backoff factors.
- **Structured JSON Logging**: Every step, tool request, tool output, retry, and completion event is logged in machine-readable JSON lines format.
- **Mock Mode**: Out-of-the-box local testing and unit tests run with deterministic mock execution without needing third-party API credits.
- **CI / CD Ready**: Preconfigured GitHub Actions test workflow.

## Directory Structure

```
03-llm-agent-orchestrator/
├── ci/
│   └── ci.yml               # Automated CI test pipeline configuration
├── configs/
│   └── agent_config.yaml    # Agent, model, execution & logging settings
├── logs/                    # Execution logs (JSON lines)
├── src/
│   ├── __init__.py
│   ├── client.py            # Async LLM API client with backoff retries
│   ├── config.py            # YAML configuration loader & Pydantic validator
│   ├── logger.py            # Structured JSON logger
│   ├── orchestrator.py      # Core agent execution & tool loop
│   └── tools.py             # Tool registry and default tool implementations
├── tests/
│   ├── test_config.py       # Configuration parser tests
│   ├── test_orchestrator.py # Tool loop & reasoning tests
│   └── test_tools.py        # Tool registry and schema generation tests
├── .env.example             # Environment variable template
├── .gitignore
├── requirements.txt         # Project dependencies
├── run_agent.py             # CLI runner
└── README.md
```

## Quick Start

### 1. Installation

```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and set your API key (or omit for mock mode):

```bash
cp .env.example .env
```

### 3. Run the Orchestrator CLI

```bash
python run_agent.py "Please calculate 45 * 12 + 100"
```

### 4. Run Pytest Suite

```bash
pytest -v
```
