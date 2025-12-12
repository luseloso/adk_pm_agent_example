# Development Notes

This document captures the development journey and key learnings from building and deploying the Product Management Agent.

## Project Overview

The PM Agent is a hierarchical multi-agent system built with Google's Agent Development Kit (ADK) that transforms product ideas into comprehensive Product Requirements Documents (PRDs) through a three-stage workflow.

**Deployment Date**: December 2025
**Reasoning Engine ID**: 5890211333344854016
**Project**: your-project-id
**Region**: us-central1

## Development Journey

### Phase 1: Architecture Design

Started with YAML agent configurations that defined the agent hierarchy:
- `root_agent.yaml` - Main orchestrator
- `virtual_product_manager_agent.yaml` - Sequential coordinator
- `market_researcher_agent.yaml` - Research with Google Search
- `user_journey_agent.yaml` - Persona and journey mapping
- `prd_scripter_agent.yaml` - PRD generation

**Key Decision**: Converted to Python-only implementation for better flexibility and maintainability.

### Phase 2: Python Implementation

Created `pm_agent/agent.py` with ADK Python SDK:

```python
from google.adk.agents import Agent, SequentialAgent
from google.adk.tools import google_search
```

**Architecture Pattern**: SequentialAgent for workflow orchestration
- Market Research → User Journey → PRD Scripter
- Each stage builds on previous outputs
- Shared session state for memory persistence

### Phase 3: Memory Integration

Implemented `VertexAiMemoryBankService` for persistent memory:
- All agents share context across sessions
- Enables multi-turn conversations
- Improves response quality through learning

```python
def memory_bank_service_builder():
    return VertexAiMemoryBankService(
        project=PROJECT,
        location=LOCATION
    )
```

### Phase 4: Tracing & Observability

Enabled OpenTelemetry tracing for monitoring:
- Set `enable_tracing=True` in AdkApp
- Required Telemetry API to be enabled
- Integrated with Cloud Trace for visualization

**Critical Learning**: The Telemetry API (`telemetry.googleapis.com`) must be enabled before tracing will work, even with `enable_tracing=True` configured.

### Phase 5: Deployment Challenges

#### Challenge 1: Python Version Compatibility
**Issue**: Initial deployment failed with Python 3.14
**Error**: "Unsupported python version: 3.14. AgentEngine only supports ('3.9', '3.10', '3.11', '3.12', '3.13')"
**Solution**: Used pyenv to install Python 3.13.2
```bash
pyenv install 3.13.2
~/.pyenv/versions/3.13.2/bin/python3 -m venv venv313
```

#### Challenge 2: Missing Location Parameter
**Issue**: 404 error during deployment
**Error**: "Received http2 header with status: 404"
**Root Cause**: Missing `location` parameter in `vertexai.init()`
**Solution**: Added location parameter
```python
vertexai.init(
    project=project,
    location=location,  # This was missing!
    staging_bucket=staging_bucket
)
```

#### Challenge 3: Tracing Not Working
**Issue**: Agent deployed successfully but no traces appeared
**Error**: "Telemetry API has not been used in project before or it is disabled"
**Solution**: Enabled Telemetry API
```bash
gcloud services enable telemetry.googleapis.com --project=your-project-id
```
**Wait Time**: 2-3 minutes after enabling for changes to propagate

#### Challenge 4: ADK CLI Payload Size Limit
**Issue**: CLI deployment failed with payload size exceeding 8MB
**Cause**: Virtual environment directories included in package
**Attempted Fix**: Created `.adkignore` file (didn't work with ADK CLI)
**Final Solution**: Used Python SDK deployment method instead
```python
reasoning_engines.ReasoningEngine.create(...)
```

#### Challenge 5: YAML File Confusion
**Issue**: ADK CLI detected YAML files and auto-generated code
**Clarification**: YAML files are NOT required for Python deployments
**Solution**: Moved YAML files to `archive/yaml_configs/` for reference only

### Phase 6: Production Deployment

Final successful deployment using Python SDK:

```python
remote_app = reasoning_engines.ReasoningEngine.create(
    reasoning_engine=app,
    requirements=["google-cloud-aiplatform[adk,agent_engines]>=1.112"],
    extra_packages=["agent.py"],
    sys_version="3.13"
)
```

**Result**:
- Successfully deployed with ID: 5890211333344854016
- Tracing enabled and working
- Memory persistence functional
- Registered in Gemini Enterprise

## Key Technical Decisions

### 1. Sequential vs Parallel Execution
**Choice**: Sequential
**Rationale**:
- Ensures proper workflow order
- Each agent builds on previous outputs
- Quality over speed for PRD generation

### 2. Model Selection
**Choice**:
- gemini-2.5-flash for orchestration and research
- gemini-2.5-pro for synthesis and writing

**Rationale**:
- Flash: Fast and cost-effective for search and routing
- Pro: Higher quality for creative tasks like persona creation and PRD writing

### 3. Shared Memory Architecture
**Choice**: All agents share same session state
**Rationale**:
- Enables context retention across stages
- Improves coherence in final PRD
- Supports multi-turn refinement conversations

### 4. Tool Integration
**Choice**: Built-in `google_search` from ADK
**Rationale**:
- No additional dependencies
- Optimized for agent use cases
- Grounding in real-world data

## Performance Characteristics

Based on production deployment:

- **Latency**: ~15-20 seconds per stage (45-60 seconds total)
- **Token Usage**: ~2,500-3,000 tokens per product idea
- **Success Rate**: High-quality outputs with factual grounding
- **Scalability**: Leverages Vertex AI infrastructure

## Lessons Learned

### 1. Environment Configuration is Critical
Always specify all required parameters explicitly:
```python
vertexai.init(
    project=PROJECT,      # Required
    location=LOCATION,    # Required for Agent Engine
    staging_bucket=BUCKET # Required for deployment
)
```

### 2. API Dependencies Matter
Enable all required APIs before deployment:
- `aiplatform.googleapis.com` - Core AI Platform
- `cloudtrace.googleapis.com` - Tracing
- `telemetry.googleapis.com` - Tracing telemetry (often forgotten!)

### 3. Python Version Compatibility
Agent Engine is strict about Python versions. Always check:
```bash
python --version  # Must be 3.9-3.13
```

### 4. Deployment Method Selection
- **ADK CLI**: Great for simple agents, but has payload size limits
- **Python SDK**: More flexible, handles larger codebases, better for production

### 5. YAML vs Python
- YAML configs are optional, not required
- Python-only approach provides better IDE support and type checking
- Keep YAMLs as reference documentation only

### 6. Testing Strategy
Test at multiple levels:
1. **Local structure validation**: Verify agent hierarchy
2. **Deployed functionality**: Test with real queries
3. **Tracing verification**: Confirm observability works
4. **Memory persistence**: Test multi-turn conversations

## Production Checklist

Before deploying to production:

- [ ] All required APIs enabled
- [ ] Python version 3.9-3.13
- [ ] Environment variables configured
- [ ] Staging bucket accessible
- [ ] IAM permissions granted
- [ ] Telemetry API enabled and propagated (wait 2-3 minutes)
- [ ] Test tracing works
- [ ] Memory service configured correctly
- [ ] Cost budgets set
- [ ] Monitoring alerts configured

## Future Enhancements

Potential areas for improvement:

1. **Parallel Research**: Run market research and competitive analysis in parallel
2. **Custom Tools**: Add domain-specific tools (e.g., patent search, market data APIs)
3. **Quality Gates**: Add validation steps between stages
4. **Feedback Loop**: Incorporate user feedback to refine PRDs
5. **Templates**: Support different PRD templates for different industries
6. **Export Formats**: Generate PRDs in multiple formats (Markdown, PDF, Google Docs)

## References

- [ADK Documentation](https://google.github.io/adk-docs/)
- [Agent Engine Deployment](https://docs.cloud.google.com/agent-builder/agent-engine/deploy)
- [Cloud Trace](https://cloud.google.com/trace/docs)
- [OpenTelemetry Instrumentation](https://docs.cloud.google.com/stackdriver/docs/instrumentation/ai-agent-adk)

## Support

For issues or questions:
1. Check [DEPLOYMENT.md](DEPLOYMENT.md) troubleshooting section
2. Review [ARCHITECTURE.md](ARCHITECTURE.md) for design details
3. Consult [ADK samples](https://github.com/google/adk-samples) for patterns
4. Search [ADK issues](https://github.com/google/adk-python/issues) for known problems
