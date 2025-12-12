from google.adk.agents import Agent, SequentialAgent
from google.adk.tools import google_search
from .mcp_tool import search_existing_prds, get_prd, store_prd

# Market Researcher Agent - with google_search tool
market_researcher_agent = Agent(
    name="market_researcher_agent",
    model="gemini-2.5-flash",
    instruction="""Your task is to understand the problem space based on the product idea provided.

Define the core problem, identify the target audience, and analyze potential competitors.

Use the Google Search tool to gather external context and validate your findings.""",
    tools=[google_search],
)

# User Journey Agent
user_journey_agent = Agent(
    name="user_journey_agent",
    model="gemini-2.5-pro",
    instruction="""Based on the market research and problem definition, synthesize the information to create

detailed customer user journeys and high-level user personas.

Focus on user needs, motivations, and pain points uncovered during market research.""",
)

# Helper tool to write PRD to temporary file
def write_prd_to_temp(content: str) -> str:
    """
    Write PRD content to a temporary file for handoff to root agent.

    Args:
        content: The complete PRD in markdown format

    Returns:
        Confirmation message with file path
    """
    import os
    temp_file = "/tmp/temp_prd_draft.md"
    try:
        with open(temp_file, 'w') as f:
            f.write(content)
        return f"PRD draft successfully saved to {temp_file}"
    except Exception as e:
        return f"Error saving PRD draft: {str(e)}"

# PRD Scripter Agent - Creates PRD and saves to temp file
prd_scripter_agent = Agent(
    name="prd_scripter_agent",
    model="gemini-2.5-pro",
    instruction="""Your task is to compile all the preceding context (market research, user journeys, and personas)

into a concise Product Requirements Document (PRD).

The PRD should include:

1. Problem Statement: A clear definition of the problem being solved.

2. User Stories: A list of user stories with acceptance criteria.

3. Key Functional Requirements: Essential features and functionalities.

After creating the PRD in markdown format:
1. Use the write_prd_to_temp tool to save it to a temporary file
2. Present the complete PRD to the user in a clear, formatted manner
3. End your response by explicitly asking: "Would you like me to save this PRD to storage? You can also ask me to refine any section if needed."

This ensures the user sees the PRD and knows they need to provide confirmation to proceed.""",
    tools=[write_prd_to_temp],
)

# Helper tool to read PRD from temporary file
def read_prd_from_temp() -> str:
    """
    Read PRD content from temporary file.

    Returns:
        PRD content or error message
    """
    temp_file = "/tmp/temp_prd_draft.md"
    try:
        with open(temp_file, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return "Error: PRD draft file not found at /tmp/temp_prd_draft.md"
    except Exception as e:
        return f"Error reading PRD draft: {str(e)}"

# Sequential Agent for PRD Generation Workflow
virtual_product_manager_agent = SequentialAgent(
    name="virtual_product_manager_agent",
    description="Orchestrates a series of specialized sub-agents to manage a product definition workflow, where the output of one agent becomes the input for the next.",
    sub_agents=[
        market_researcher_agent,
        user_journey_agent,
        prd_scripter_agent,
    ],
)

# Root Agent - Handles duplicate check, delegates to SequentialAgent, then handles save confirmation
root_agent = Agent(
    name="root_agent",
    model="gemini-2.5-flash",
    instruction="""You are the main orchestrator for the Product Management workflow.

CRITICAL WORKFLOW - Follow this sequence exactly:

**STEP 1: Check for Duplicates**
When user provides a product idea, ALWAYS use search_existing_prds to check if similar PRDs already exist.
- Extract key product concept from user's request
- Search for related/similar products

**STEP 2: Handle Duplicates (HITL #1 - conversational)**
IF DUPLICATES FOUND (search returns results):
- Present the search results to the user clearly
- Explain that similar PRDs already exist in the system
- Ask the user explicitly what they want to do:
  a) View one of the existing PRDs (use get_prd tool with specific prd_id)
  b) Create a new PRD anyway (proceed to Step 3)
  c) Refine their idea and search again
- WAIT for the user's response before taking any action
- DO NOT automatically proceed to create a new PRD

IF NO DUPLICATES FOUND:
- Inform the user that no similar PRDs were found
- Proceed to Step 3

**STEP 3: Delegate to PRD Generation Workflow**
Delegate to virtual_product_manager_agent (SequentialAgent) which will automatically:
1. Run market research (with Google Search)
2. Create user journeys and personas
3. Generate the complete PRD and save it to /tmp/temp_prd_draft.md
4. The prd_scripter_agent will automatically present the PRD to the user and ask for confirmation

**STEP 4: Handle User Response to PRD (HITL #2)**
After the SequentialAgent presents the PRD:
1. WAIT for the user's response
2. If user confirms (e.g., "yes", "save it", "please save"), proceed to Step 5
3. If user asks for refinements, provide guidance or delegate back to appropriate agent
4. DO NOT call store_prd until user explicitly confirms

**STEP 5: Save PRD and Display Result**
If user confirms saving:
- Extract the product name from the user's original request
- Read the PRD content from /tmp/temp_prd_draft.md using read_prd_from_temp
- Call store_prd with:
  - product_name: The product name from user's request
  - content: The PRD content from the temp file
  - author: "PM Agent"
  - version: "1.0"
- Parse the result and display to user:
  - Confirm successful save
  - Show the PRD ID
  - IMPORTANT: Display the html_url prominently so user can view the formatted PRD

This approach ensures:
- Duplicate prevention (HITL #1 via conversation)
- User approval before saving (HITL #2 via conversation)
- PRD content is preserved via file system (artifact handoff pattern)
- User receives a shareable link to the formatted PRD""",
    tools=[search_existing_prds, get_prd, read_prd_from_temp, store_prd],
    sub_agents=[virtual_product_manager_agent],
)
