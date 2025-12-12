#!/usr/bin/env python3
"""
Local testing example for the Product Management Agent.

This script demonstrates how to test the PM agent locally before deployment.
It simulates the agent workflow without needing to deploy to Agent Engine.

Usage:
    python examples/local_test.py
"""

import sys
import os

# Add parent directory to path to import pm_agent
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pm_agent.agent import root_agent


def test_local_agent():
    """Test the agent locally with a sample product idea."""

    print("Testing PM Agent locally (simulation mode)")
    print("=" * 60)

    # Sample product idea
    product_idea = """
    I want to build a mobile app for fitness tracking that helps users:
    - Track their daily workouts and nutrition
    - Set and monitor fitness goals
    - Connect with fitness coaches
    - Join community challenges
    """

    print(f"\nProduct Idea:\n{product_idea}\n")
    print("=" * 60)

    # In local mode, you would typically use the agent with a local runner
    # For demonstration, we'll just show the agent structure
    print("\nAgent Structure:")
    print(f"Root Agent: {root_agent.name}")
    print(f"Model: {root_agent.model}")
    print(f"\nSub-agents:")

    for sub_agent in root_agent.sub_agents:
        print(f"  - {sub_agent.name}")
        if hasattr(sub_agent, 'sub_agents'):
            print(f"    Sequential workflow with {len(sub_agent.sub_agents)} stages:")
            for stage in sub_agent.sub_agents:
                print(f"      {len(sub_agent.sub_agents.index(stage)) + 1}. {stage.name}")

    print("\n" + "=" * 60)
    print("Note: Full execution requires deployment to Agent Engine")
    print("See ../docs/DEPLOYMENT.md for deployment instructions")
    print("=" * 60)


if __name__ == "__main__":
    test_local_agent()
