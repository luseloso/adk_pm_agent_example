# Local Testing Guide

Test the PM Agent locally using the ADK web interface before deploying.

## Prerequisites

- ADK CLI: `pip install google-cloud-aiplatform[adk,agent_engines]`
- Python 3.11+
- Dependencies installed: `pip install -r requirements.txt`

## Quick Start

From the repository root:

```bash
cd pm_agent
adk web . --port 8080
```

Open browser to `http://127.0.0.1:8080`

## Testing Workflow

### 1. Start ADK Web Server

```bash
# From repository root
adk web pm_agent --port 8080 --reload_agents
```

The `--reload_agents` flag enables hot-reloading when you modify agent code.

### 2. Test Product Ideas

Try these example prompts:

**Basic PRD Creation**:
```
Create a PRD for a mobile fitness tracking app
```

**With Specifics**:
```
I want to build a productivity app that helps remote workers:
- Track deep work sessions
- Block distracting websites
- Integrate with calendar
- Provide daily insights
```

### 3. Test HITL Workflows

**Duplicate Detection**:
1. Create a PRD for "fitness tracking app"
2. Try creating another similar PRD
3. Agent should detect duplicate and ask what to do

**PRD Approval**:
1. Complete a PRD generation
2. Agent presents PRD and asks for confirmation
3. Respond with "yes" to save or ask for refinements

## Environment Configuration

### For Local Testing Only

```bash
# In pm_agent directory
cp .env.example .env

# Minimal config for local testing:
GOOGLE_GENAI_USE_VERTEXAI=1
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
```

### For Testing with MCP Server

To test with actual PRD storage:

```bash
# Ensure MCP server is deployed first
# Then add to .env:
MCP_SERVER_URL=https://your-mcp-server.run.app

# For authentication:
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

## ADK Web CLI Options

```bash
# Auto-reload on code changes
adk web pm_agent --port 8080 --reload_agents

# Enable cloud tracing (requires GCP auth)
adk web pm_agent --port 8080 --trace_to_cloud

# Verbose logging
adk web pm_agent --port 8080 --verbose
```

## Troubleshooting

### "No agents found"

**Cause**: Module import error

**Solution**:
```bash
# Verify agent can be imported
python3 -c "from pm_agent import root_agent; print(root_agent.name)"

# Should output: root_agent
```

### Port Already in Use

**Error**: `address already in use`

**Solution**:
```bash
# Use different port
adk web pm_agent --port 8081

# Or kill existing process
lsof -ti:8080 | xargs kill -9
```

### MCP Server Connection Errors

**Error**: Connection refused when calling MCP tools

**Solutions**:
1. Verify MCP_SERVER_URL in `.env`
2. Check MCP server is running:
   ```bash
   curl https://your-mcp-server.run.app/health
   ```
3. Verify authentication (service account permissions)

## Comparing Local vs. Deployed

| Feature | Local (adk web) | Deployed (Agent Engine) |
|---------|----------------|-------------------------|
| Speed | Faster | Network latency |
| Storage | Temporary (no persistence) | Persists to GCS |
| Tracing | Optional | Always enabled |
| Cost | Free (local compute) | GCP charges |
| Collaboration | Single user | Multi-user |

## Validating Changes

Before deploying updates:

1. **Test the full workflow** - Create PRD end-to-end
2. **Test error cases** - Try invalid inputs
3. **Test HITL points** - Verify both confirmation points work
4. **Check logs** - Look for errors or warnings
5. **Compare outputs** - Ensure PRD quality is maintained

## Next Steps

- Deploy changes: See [Deployment Guide](DEPLOYMENT.md)
- Understand architecture: See [Architecture Documentation](ARCHITECTURE.md)
- Try examples: See [Examples](../examples/)

## References

- [ADK CLI Documentation](https://google.github.io/adk-docs/cli/)
- [ADK Web Interface](https://google.github.io/adk-docs/deploy/local/)
