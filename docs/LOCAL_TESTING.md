# Local Testing with ADK Web

This guide explains how to test the PM Agent locally using the ADK web interface.

## Prerequisites

- ADK CLI installed (`pip install google-cloud-aiplatform[adk]`)
- Python 3.10-3.13
- All dependencies from `requirements.txt` installed in your environment

## Current Setup Status

✅ **Fixed**: Updated `pm_agent/__init__.py` to use relative imports (`.agent` instead of `agent`)
✅ **Server Running**: ADK web server is running on port 8080
⚠️ **Note**: The ADK CLI uses its own Python environment, which may differ from your current environment

## Starting the ADK Web Interface

### Method 1: Using ADK CLI (Current Approach)

From the project root directory:

```bash
cd /Users/your-project-id/Documents/agents/product-management-agent

# Start the web server (pointing to current directory which contains pm_agent/)
adk web . --port 8080
```

The server will start at: **http://127.0.0.1:8080**

### Method 2: With Virtual Environment

If you have a virtual environment with ADK installed:

```bash
# Activate your virtual environment
source venv/bin/activate  # or your venv path

# Install dependencies if not already installed
pip install -r requirements.txt

# Start ADK web
adk web . --port 8080
```

## Using the Web Interface

1. **Open your browser** to http://127.0.0.1:8080
2. **Select the pm_agent** from the available agents
3. **Start a conversation** with a product idea, for example:
   ```
   I want to build a mobile app for fitness tracking that helps users:
   - Track their daily workouts and nutrition
   - Set and monitor fitness goals
   - Connect with fitness coaches
   - Join community challenges
   ```

4. **Watch the agent work** through three stages:
   - **Market Research**: Uses Google Search to analyze the problem space
   - **User Journey Mapping**: Creates personas and user journeys
   - **PRD Generation**: Compiles everything into a structured PRD

## Troubleshooting

### "No agents found" Warning

**Cause**: The agent module can't be imported, usually due to:
- Wrong Python environment
- Missing dependencies
- Import errors in the code

**Solution**:
1. Ensure ADK packages are installed in the Python environment being used
2. Check that `pm_agent/__init__.py` uses relative imports (`.agent`)
3. Verify `agent.py` can be imported:
   ```bash
   python3 -c "from pm_agent import root_agent; print(root_agent.name)"
   ```

### Port Already in Use

**Error**: `[errno 48] address already in use`

**Solution**: Use a different port
```bash
adk web . --port 8081  # or any other available port
```

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'google'`

**Cause**: ADK packages not installed in the current Python environment

**Solution**:
```bash
pip install google-cloud-aiplatform[adk,agent_engines]>=1.112
```

## ADK Web CLI Options

Useful options for local testing:

```bash
# Enable verbose logging
adk web . --port 8080 --verbose

# Enable auto-reload on code changes
adk web . --port 8080 --reload --reload_agents

# Enable cloud tracing (requires GCP auth)
adk web . --port 8080 --trace_to_cloud
```

## Alternative: Python-Based Local Testing

If `adk web` doesn't work, you can test with a simple Python script:

```python
#!/usr/bin/env python3
import vertexai
from pm_agent import root_agent

# For local testing without deployment
print(f"Testing {root_agent.name}")
print(f"Model: {root_agent.model}")
print(f"Sub-agents: {len(root_agent.sub_agents)}")

# Note: Full execution requires deployment to Agent Engine
# This just validates the agent structure
```

Save as `local_structure_test.py` and run:
```bash
python local_structure_test.py
```

## Best Practices for Local Testing

1. **Use `--reload_agents`** during development to see changes without restarting
2. **Test with realistic product ideas** to validate the full workflow
3. **Check logs** for errors or warnings during execution
4. **Verify Google Search** is working (requires internet connection)
5. **Compare outputs** with the deployed version to ensure consistency

## Environment Variables

For local testing with cloud features:

```bash
export GOOGLE_CLOUD_PROJECT=your-project-id
export GOOGLE_CLOUD_LOCATION=us-central1
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

Then start with cloud features:

```bash
adk web . --port 8080 --trace_to_cloud
```

## Current Server Status

A server is currently running at http://127.0.0.1:8080

To stop it:
- Press `Ctrl+C` in the terminal where it's running
- Or find and kill the process:
  ```bash
  lsof -ti:8080 | xargs kill -9
  ```

## Comparing Local vs Deployed

| Feature | Local (adk web) | Deployed (Agent Engine) |
|---------|----------------|------------------------|
| Speed | Faster (local execution) | Network latency |
| Memory | In-memory only | Persistent with VertexAiMemoryBankService |
| Tracing | Optional (--trace_to_cloud) | Always enabled |
| Cost | Free (local compute) | GCP charges |
| Collaboration | Single user | Multi-user sessions |

## Next Steps

- Test the agent thoroughly with various product ideas
- Compare results with deployed version
- Iterate on agent instructions and logic
- Deploy updates when satisfied with local testing

## References

- [ADK CLI Documentation](https://google.github.io/adk-docs/cli/)
- [ADK Web Interface Guide](https://google.github.io/adk-docs/deploy/local/)
- [Architecture Documentation](ARCHITECTURE.md)
