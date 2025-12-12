# Architecture

## Overview

The Product Management Agent implements a hierarchical multi-agent system using Google's Agent Development Kit (ADK). The system processes product ideas through three specialized stages in a sequential workflow.

## Agent Hierarchy

```
┌─────────────────────────────────────────────────────┐
│              root_agent                              │
│         (Main Orchestrator)                          │
│         gemini-2.5-flash                            │
└────────────────┬────────────────────────────────────┘
                 │
                 ├─► Initiates workflow
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│      virtual_product_manager_agent                   │
│         (SequentialAgent)                            │
└────────────────┬────────────────────────────────────┘
                 │
                 ├─► Sequential Execution
                 │
    ┌────────────┼────────────┐
    │            │            │
    ▼            ▼            ▼
┌─────────┐  ┌─────────┐  ┌──────────┐
│ Market  │  │  User   │  │   PRD    │
│Research │─►│ Journey │─►│ Scripter │
│  Agent  │  │  Agent  │  │  Agent   │
└─────────┘  └─────────┘  └──────────┘
```

## Agents

### Root Agent
- **Model**: gemini-2.5-flash
- **Type**: Agent
- **Purpose**: Main orchestrator that initiates the workflow
- **Transfers to**: virtual_product_manager_agent

### Virtual Product Manager Agent
- **Type**: SequentialAgent
- **Purpose**: Coordinates three sub-agents in sequence
- **Flow**: Output of each agent becomes input for the next
- **Sub-agents**: market_researcher → user_journey → prd_scripter

### Market Researcher Agent
- **Model**: gemini-2.5-flash
- **Tools**: google_search
- **Purpose**:
  - Analyze problem space
  - Identify target audience
  - Research competitors
  - Gather external context

### User Journey Agent
- **Model**: gemini-2.5-pro
- **Purpose**:
  - Create detailed personas
  - Map customer journeys
  - Identify pain points
  - Define user needs

### PRD Scripter Agent
- **Model**: gemini-2.5-pro
- **Purpose**:
  - Compile Product Requirements Document
  - Write problem statement
  - Create user stories
  - Define functional requirements

## Data Flow

```
User Input (Product Idea)
    │
    ▼
Root Agent (validates and routes)
    │
    ▼
Virtual PM Agent (orchestrates)
    │
    ├──► Market Researcher
    │    ├─ Google Search
    │    └─ Output: Market Analysis
    │
    ▼
    User Journey Agent
    ├─ Input: Market Analysis
    └─ Output: Personas + Journeys
    │
    ▼
    PRD Scripter
    ├─ Input: All previous context
    └─ Output: Complete PRD
```

## Key Components

### Sequential Execution

Agents execute in order using `SequentialAgent`:

```python
SequentialAgent(
    name="virtual_product_manager_agent",
    sub_agents=[
        market_researcher_agent,
        user_journey_agent,
        prd_scripter_agent,
    ],
)
```

### Shared Memory

All agents share session state through VertexAiMemoryBankService:
- Persistent across conversations
- Enables context awareness
- Improves response quality

### Tool Integration

Market researcher uses Google Search:
```python
Agent(
    name="market_researcher_agent",
    tools=[google_search],
    ...
)
```

### Model Selection

- **gemini-2.5-flash**: Fast, cost-effective for orchestration and research
- **gemini-2.5-pro**: Higher quality for synthesis and writing

## Tracing & Observability

### OpenTelemetry Integration

```python
AdkApp(
    agent=root_agent,
    enable_tracing=True,
    memory_service_builder=memory_bank_service_builder
)
```

### Cloud Trace

- Automatic span creation for each agent execution
- Performance monitoring
- Error tracking
- Request flow visualization

## Design Decisions

### Why Sequential vs Parallel?

Sequential execution ensures:
- Proper workflow order
- Each agent builds on previous outputs
- Consistent context flow
- Quality over speed

### Why Hierarchical Structure?

Benefits:
- Clear separation of concerns
- Reusable components
- Easy to test individual agents
- Scalable architecture

### Why Shared Memory?

Enables:
- Multi-turn conversations
- Context retention
- Improved user experience
- Learning from past interactions

## Extension Points

### Adding New Agents

```python
new_agent = Agent(
    name="new_agent",
    model="gemini-2.5-pro",
    instruction="...",
    tools=[custom_tool],
)

# Add to sequence
SequentialAgent(
    sub_agents=[
        market_researcher_agent,
        user_journey_agent,
        new_agent,  # Insert here
        prd_scripter_agent,
    ],
)
```

### Custom Tools

```python
from google.adk.tools import Tool

def custom_api(query: str) -> str:
    # Your implementation
    return result

agent = Agent(
    tools=[google_search, Tool(custom_api)],
    ...
)
```

## Performance Characteristics

- **Latency**: ~15-20 seconds per stage
- **Token Usage**: ~2,500-3,000 tokens per product idea
- **Accuracy**: High-quality outputs with grounding
- **Scalability**: Scales with Vertex AI infrastructure

## Security Considerations

1. **API Keys**: Managed through Google Cloud IAM
2. **Data Privacy**: All data stays in your GCP project
3. **Access Control**: Configure IAM roles
4. **Audit Logging**: Automatic via Cloud Logging

## References

- [ADK Agents](https://google.github.io/adk-docs/agents/)
- [Sequential Agents](https://google.github.io/adk-docs/agents/sequential/)
- [Tools](https://google.github.io/adk-docs/tools/)
- [Memory](https://google.github.io/adk-docs/sessions/memory/)
