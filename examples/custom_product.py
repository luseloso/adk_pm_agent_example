#!/usr/bin/env python3
"""
Custom product testing example for the deployed PM Agent.

This script demonstrates how to test the deployed agent with various
product ideas to generate different PRDs.

Usage:
    python examples/custom_product.py
"""

import os
import vertexai
from vertexai import agent_engines


# Configuration - update these with your deployment details
PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "your-project-id")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
REASONING_ENGINE_ID = os.getenv("REASONING_ENGINE_ID", "your-reasoning-engine-id")


def test_product_idea(agent, product_idea):
    """Test the agent with a specific product idea."""

    print(f"\n{'=' * 60}")
    print(f"Testing Product Idea:\n{product_idea}")
    print(f"{'=' * 60}\n")

    # Create agent context
    agent_context = f'{{"message":{{"role":"user","parts":[{{"text":"{product_idea}"}}]}}}}'

    try:
        # Stream the response
        for response in agent.streaming_agent_run_with_events(request_json=agent_context):
            print(response)
    except Exception as e:
        print(f"Error during streaming: {e}")
        print("\nFalling back to query method...")

        # Fallback to query method
        result = agent.query(input=product_idea)
        print(f"\nResult: {result}")


def main():
    """Run tests with different product ideas."""

    # Initialize Vertex AI
    vertexai.init(project=PROJECT, location=LOCATION)

    print(f"Connecting to deployed PM Agent...")
    print(f"Project: {PROJECT}")
    print(f"Location: {LOCATION}")
    print(f"Reasoning Engine ID: {REASONING_ENGINE_ID}\n")

    # Get the deployed agent
    deployed_agent = agent_engines.get(
        f"projects/{PROJECT}/locations/{LOCATION}/reasoningEngines/{REASONING_ENGINE_ID}"
    )

    print(f"Connected to: {deployed_agent.resource_name}\n")

    # Test cases - different product ideas
    product_ideas = [
        "A mobile app for fitness tracking that helps users track workouts and nutrition",
        "A B2B SaaS platform for managing remote team collaboration and project tracking",
        "An AI-powered personal finance assistant that helps users save money and invest wisely",
        "A marketplace connecting freelance designers with small businesses needing branding",
    ]

    # Run tests
    for i, idea in enumerate(product_ideas, 1):
        print(f"\n{'#' * 60}")
        print(f"Test Case {i}/{len(product_ideas)}")
        print(f"{'#' * 60}")

        test_product_idea(deployed_agent, idea)

        # Optional: Ask to continue
        if i < len(product_ideas):
            response = input("\n\nContinue to next test? (y/n): ")
            if response.lower() != 'y':
                print("Stopping tests.")
                break

    print(f"\n{'=' * 60}")
    print("All tests complete!")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
