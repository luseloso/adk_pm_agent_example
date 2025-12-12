# Architecture

## Overview

The Product Management Agent is a hierarchical multi-agent system that creates comprehensive Product Requirements Documents (PRDs) through a sequential workflow with two human-in-the-loop (HITL) confirmation points. The system integrates with a custom MCP server for PRD storage and retrieval.

## System Architecture

```
┌──────────────────────────────────────────────────────────┐
│                     User Request                          │
│              "Create PRD for [product idea]"             │
└───────────────────────┬──────────────────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────────────────┐
│                   root_agent                              │
│              (Main Orchestrator)                          │
│               gemini-2.5-flash                            │
│                                                           │
│  Tools:                                                   │
│  - search_existing_prds (MCP)                            │
│  - get_prd (MCP)                                         │
│  - read_prd_from_temp                                    │
│  - store_prd (MCP)                                       │
└───────────────────────┬───────────────────────────────────┘
                        │
            ┌───────────┴──────────────┐
            │                          │
       HITL #1                    HITL #2
   Duplicate Check             PRD Approval
            │                          │
            ▼                          ▼
┌─────────────────────────┐  ┌──────────────────────┐
│  MCP Server Query       │  │  Save to Storage     │
│  (Search existing PRDs) │  │  (Dual-format)       │
└─────────────────────────┘  └──────────────────────┘
            │
            ▼
┌───────────────────────────────────────────────────────────┐
│         virtual_product_manager_agent                     │
│              (SequentialAgent)                            │
│                                                           │
│  Sequential Workflow:                                     │
│    market_researcher → user_journey → prd_scripter       │
└───────────────────────┬───────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
   ┌─────────┐    ┌──────────┐    ┌──────────┐
   │ Market  │    │   User   │    │   PRD    │
   │Research │───►│  Journey │───►│ Scripter │
   │ Agent   │    │  Agent   │    │  Agent   │
   └─────────┘    └──────────┘    └──────────┘
   gemini-flash   gemini-pro      gemini-pro
   google_search
```

## Agents

### Root Agent
- **Model**: gemini-2.5-flash
- **Type**: Agent
- **Purpose**: Main orchestrator implementing HITL workflow
- **Workflow**:
  1. **Duplicate Detection** (HITL #1)
     - Searches for existing similar PRDs using `search_existing_prds`
     - If found, asks user to view existing or create new
     - Waits for user confirmation

  2. **PRD Generation**
     - Delegates to `virtual_product_manager_agent` (SequentialAgent)
     - Sequential execution of market research, user journeys, PRD writing

  3. **User Approval** (HITL #2)
     - Receives completed PRD from PRD Scripter
     - Presents PRD to user
     - Waits for user confirmation before saving

  4. **Storage**
     - Reads PRD from temporary file (`/tmp/temp_prd_draft.md`)
     - Calls `store_prd` to save to MCP server
     - Returns shareable HTML URL to user

### Virtual Product Manager Agent
- **Type**: SequentialAgent
- **Purpose**: Orchestrates three specialized agents in sequence
- **Flow**: Output of each agent becomes input for the next
- **Sub-agents**:
  1. market_researcher_agent
  2. user_journey_agent
  3. prd_scripter_agent

### Market Researcher Agent
- **Model**: gemini-2.5-flash
- **Tools**: `google_search`
- **Purpose**:
  - Analyze the problem space
  - Identify target audience
  - Research competitors
  - Gather external market context

### User Journey Agent
- **Model**: gemini-2.5-pro
- **Purpose**:
  - Synthesize market research findings
  - Create detailed user personas
  - Map customer journeys
  - Identify pain points and user needs

### PRD Scripter Agent
- **Model**: gemini-2.5-pro
- **Tools**: `write_prd_to_temp`
- **Purpose**:
  - Compile comprehensive PRD from all previous context
  - Write problem statement
  - Create user stories with acceptance criteria
  - Define functional requirements
  - Save to `/tmp/temp_prd_draft.md` for root agent
  - Present PRD and ask for confirmation

## MCP Server Integration

### Architecture
```
┌──────────────────┐         ┌──────────────────┐
│   PM Agent       │  HTTP   │   MCP Server     │
│  (Agent Engine)  │◄──────►│  (Cloud Run)     │
└──────────────────┘  SSE    └─────────┬────────┘
                                       │
                        ┌──────────────┼──────────────┐
                        │              │              │
                        ▼              ▼              ▼
                   ┌─────────┐  ┌──────────┐  ┌─────────────┐
                   │   GCS   │  │  Vertex  │  │   Search    │
                   │ Storage │  │ AI Search│  │  Indexing   │
                   └─────────┘  └──────────┘  └─────────────┘
                   prds/*.md    prds/*.html
                   prds/*.html
```

### MCP Tools

**1. search_existing_prds**
- Searches Vertex AI Search data store
- Returns matching PRDs with summaries
- Used in HITL #1 for duplicate detection

**2. get_prd**
- Retrieves full PRD content by ID
- Returns markdown format
- Used when user wants to view existing PRD

**3. store_prd**
- Stores PRD in dual format (markdown + HTML)
- Uploads to Google Cloud Storage
- Indexes HTML in Vertex AI Search
- Returns both markdown path and HTML URL

### Dual-Format Storage

PRDs are stored in two formats:

**Markdown (`.md`)**
- Original PRD content
- Editable by users
- Used for retrieval by `get_prd`

**HTML (`.html`)**
- Converted from markdown using Python markdown library
- Styled for web viewing
- Indexed by Vertex AI Search (compatible MIME type)
- Shareable URL for presentation

**Storage Pattern**:
```
gs://bucket-name/prds/
├── product_name_timestamp.md    # Markdown source
└── product_name_timestamp.html  # HTML presentation
```

## Human-in-the-Loop (HITL) Patterns

### HITL #1: Duplicate Prevention
- **When**: Before starting PRD generation
- **Purpose**: Prevent duplicate work
- **Implementation**: Conversational confirmation
- **Flow**:
  1. User provides product idea
  2. Agent searches for similar PRDs
  3. If found, agent presents options:
     - View existing PRD
     - Create new PRD anyway
     - Refine idea and search again
  4. Agent waits for user response

### HITL #2: PRD Approval
- **When**: After PRD generation completes
- **Purpose**: Review and approval before storage
- **Implementation**: Conversational confirmation
- **Flow**:
  1. PRD Scripter presents complete PRD
  2. PRD Scripter explicitly asks: "Would you like me to save this PRD to storage?"
  3. Root agent waits for user confirmation
  4. On confirmation, saves to MCP server

### Artifact Handoff Pattern

PRDs are passed between agents using the filesystem:
- PRD Scripter writes to `/tmp/temp_prd_draft.md`
- Root agent reads from `/tmp/temp_prd_draft.md`
- This preserves PRD content across agent handoffs

## Data Flow

```
User Input (Product Idea)
    │
    ▼
Root Agent: search_existing_prds(idea)
    │
    ├── Found duplicates?
    │   ├── Yes → Present to user → Wait for decision (HITL #1)
    │   └── No → Proceed
    │
    ▼
Delegate to virtual_product_manager_agent
    │
    ├──► Market Researcher
    │    ├─ google_search(market research)
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
    ├─ write_prd_to_temp(prd_content)
    ├─ Present PRD to user
    └─ Ask for confirmation (HITL #2)
    │
    ▼
Root Agent: Wait for user confirmation
    │
    ├── Approved?
    │   ├── Yes → read_prd_from_temp()
    │   │         store_prd(name, content, metadata)
    │   │         Return HTML URL
    │   └── No → Offer refinements
```

## Key Design Decisions

### Why Sequential Agents?
- Ensures proper context flow
- Each agent builds on previous outputs
- Consistent information across PRD sections
- Quality over speed

### Why Two HITL Checkpoints?
1. **Duplicate Check**: Prevents wasted work, improves efficiency
2. **PRD Approval**: Gives user control before committing to storage

### Why MCP Server?
- Centralized PRD storage and retrieval
- Separation of concerns (agent logic vs. storage)
- Dual-format conversion (markdown → HTML)
- Semantic search capabilities via Vertex AI Search

### Why Dual-Format Storage?
- **Markdown**: Easy editing, version control, agent retrieval
- **HTML**: Presentation, sharing, search indexing (Vertex AI compatible)

### Why Temporary File Handoff?
- Preserves PRD content between agent executions
- Simple, reliable artifact sharing
- No dependency on external state management

## Extension Points

### Adding New Agents

Insert into the sequential workflow:

```python
competitor_analysis_agent = Agent(
    name="competitor_analysis_agent",
    model="gemini-2.5-pro",
    instruction="Analyze competitors...",
)

virtual_product_manager_agent = SequentialAgent(
    sub_agents=[
        market_researcher_agent,
        competitor_analysis_agent,  # New agent
        user_journey_agent,
        prd_scripter_agent,
    ],
)
```

### Adding Custom Tools

```python
def analyze_market_trends(industry: str) -> str:
    # Your implementation
    return result

market_researcher_agent = Agent(
    tools=[google_search, analyze_market_trends],
    ...
)
```

### Adding More MCP Tools

Update `mcp_tool.py` to add new MCP tools:

```python
def list_all_prds() -> str:
    """List all PRDs in the system"""
    response = requests.post(
        f"{MCP_SERVER_URL}/sse",
        json={"method": "tools/call", "params": {"name": "list_all_prds"}}
    )
    return parse_sse_response(response)
```

## Performance Characteristics

- **Latency**: ~30-60 seconds per PRD (three sequential agents)
- **Token Usage**: ~5,000-8,000 tokens per product idea
- **Accuracy**: High-quality PRDs with grounded market research
- **Scalability**: Scales with Vertex AI Agent Engine infrastructure

## Security & Privacy

1. **Authentication**: Service account authentication for MCP server
2. **Authorization**: IAM roles control access to GCS and Vertex AI
3. **Data Privacy**: All data stays within your GCP project
4. **Audit Logging**: Automatic via Cloud Logging and Cloud Trace
5. **No Public Access**: MCP server requires authentication (Cloud Run IAM)

## References

- [ADK Agents](https://google.github.io/adk-docs/agents/)
- [Sequential Agents](https://google.github.io/adk-docs/agents/multi-agents/)
- [Tools & Functions](https://google.github.io/adk-docs/tools/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Vertex AI Search](https://cloud.google.com/generative-ai-app-builder/docs/introduction)
