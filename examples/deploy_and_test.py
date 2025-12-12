#!/usr/bin/env python3
"""
Automated deployment and testing script for the PM Agent.

This script combines deployment and testing into a single workflow.
It deploys the agent to Agent Engine and immediately tests it.

Usage:
    python examples/deploy_and_test.py
"""

import os
import sys
import vertexai
from vertexai.preview import reasoning_engines
from vertexai import agent_engines

# Add parent directory to path to import pm_agent
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pm_agent.agent import root_agent
from google.adk.memory import VertexAiMemoryBankService


# Configuration from environment or defaults
PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "your-project-id")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
STAGING_BUCKET = os.getenv("GOOGLE_CLOUD_STAGING_BUCKET", "gs://your-staging-bucket")
AGENT_DISPLAY_NAME = "pm-agent-example"
AGENT_DESCRIPTION = "Product Management multi-agent system - Example deployment"


def deploy_agent():
    """Deploy the PM agent to Vertex AI Agent Engine."""

    print("=" * 60)
    print("Deploying PM Agent to Vertex AI Agent Engine")
    print("=" * 60)
    print(f"Project: {PROJECT}")
    print(f"Location: {LOCATION}")
    print(f"Staging Bucket: {STAGING_BUCKET}\n")

    # Initialize Vertex AI
    vertexai.init(
        project=PROJECT,
        location=LOCATION,
        staging_bucket=STAGING_BUCKET
    )

    # Memory service builder
    def memory_bank_service_builder():
        return VertexAiMemoryBankService(
            project=PROJECT,
            location=LOCATION
        )

    # Create ADK app with memory and tracing
    print("Creating ADK app with memory and tracing enabled...")
    app = reasoning_engines.AdkApp(
        agent=root_agent,
        enable_tracing=True,
        memory_service_builder=memory_bank_service_builder
    )

    # Deploy to Agent Engine
    print("Deploying to Agent Engine...")
    print("This may take several minutes...\n")

    remote_app = reasoning_engines.ReasoningEngine.create(
        reasoning_engine=app,
        requirements=[
            "google-cloud-aiplatform[adk,agent_engines]>=1.112",
        ],
        extra_packages=[os.path.join(os.path.dirname(__file__), "..", "pm_agent", "agent.py")],
        sys_version="3.13"
    )

    print("\n" + "=" * 60)
    print("Deployment successful!")
    print("=" * 60)
    print(f"Resource name: {remote_app.resource_name}")

    reasoning_engine_id = remote_app.resource_name.split("/")[-1]
    print(f"Reasoning Engine ID: {reasoning_engine_id}")
    print("=" * 60 + "\n")

    return remote_app, reasoning_engine_id


def test_agent(reasoning_engine_id):
    """Test the deployed agent with a sample product idea."""

    print("\n" + "=" * 60)
    print("Testing Deployed Agent")
    print("=" * 60)

    # Get the deployed agent
    deployed_agent = agent_engines.get(
        f"projects/{PROJECT}/locations/{LOCATION}/reasoningEngines/{reasoning_engine_id}"
    )

    # Test product idea
    product_idea = "I want to build a mobile app for fitness tracking that helps users track their workouts and nutrition"

    print(f"\nProduct Idea:\n{product_idea}\n")
    print("=" * 60 + "\n")

    # Create agent context
    agent_context = f'{{"message":{{"role":"user","parts":[{{"text":"{product_idea}"}}]}}}}'

    print("Agent response:\n")

    try:
        # Stream the response
        for response in deployed_agent.streaming_agent_run_with_events(request_json=agent_context):
            print(response)
    except Exception as e:
        print(f"Error during streaming: {e}")
        print("\nFalling back to query method...")

        # Fallback to query method
        result = deployed_agent.query(input=product_idea)
        print(f"\nResult: {result}")

    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)


def main():
    """Deploy and test the PM agent."""

    print("\n" + "#" * 60)
    print("PM Agent - Automated Deployment & Testing")
    print("#" * 60 + "\n")

    # Validate configuration
    if PROJECT == "your-project-id":
        print("ERROR: Please set GOOGLE_CLOUD_PROJECT environment variable")
        print("Example: export GOOGLE_CLOUD_PROJECT=your-project-id")
        sys.exit(1)

    if STAGING_BUCKET == "gs://your-staging-bucket":
        print("ERROR: Please set GOOGLE_CLOUD_STAGING_BUCKET environment variable")
        print("Example: export GOOGLE_CLOUD_STAGING_BUCKET=gs://your-bucket")
        sys.exit(1)

    # Deploy the agent
    remote_app, reasoning_engine_id = deploy_agent()

    # Ask user if they want to test immediately
    response = input("\nTest the deployed agent now? (y/n): ")
    if response.lower() == 'y':
        test_agent(reasoning_engine_id)
    else:
        print("\nSkipping test. You can test later with:")
        print(f"  REASONING_ENGINE_ID={reasoning_engine_id} python test_agent.py")

    print("\n" + "#" * 60)
    print("Complete!")
    print("#" * 60)
    print(f"\nReasoning Engine ID: {reasoning_engine_id}")
    print(f"View traces: https://console.cloud.google.com/traces/list?project={PROJECT}")
    print("#" * 60 + "\n")


if __name__ == "__main__":
    main()
