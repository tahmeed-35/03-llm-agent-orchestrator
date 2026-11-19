#!/usr/bin/env python3
"""CLI script to run agent orchestration with sample task and view trace."""

import asyncio
import sys
from pathlib import Path
from src.orchestrator import AgentOrchestrator


async def main():
    config_path = Path(__file__).resolve().parent / "configs" / "agent_config.yaml"
    orchestrator = AgentOrchestrator(config_path=str(config_path))

    query = sys.argv[1] if len(sys.argv) > 1 else "Please calculate 45 * 12 + 100"
    print(f"🚀 Running Orchestrator with query: '{query}'\n")

    result = await orchestrator.run(query)

    print("\n" + "=" * 55)
    print("🎯 Orchestration Summary:")
    print(f"   Success: {result.success}")
    print(f"   Iterations Used: {result.iterations_used}")
    print(f"   Final Response: {result.final_response}")
    print("=" * 55)


if __name__ == "__main__":
    asyncio.run(main())
