# PM Agent HITL Testing Guide

## Overview
This guide walks you through testing the Human-in-the-Loop (HITL) workflow for the PM Agent, now refactored to use the **blog-writer pattern** (manual workflow orchestration).

## Prerequisites
- ADK web server running at: http://127.0.0.1:8080
- MCP server deployed at: https://prd-mcp-server-your-project-number.us-central1.run.app
- MCP_SERVER_URL configured in `.env`

## Architecture Changes (Blog-Writer Pattern)

### Before (SequentialAgent - BROKEN)
```
root_agent
└─ virtual_product_manager_agent (SequentialAgent)
   ├─ market_researcher_agent
   ├─ user_journey_agent
   ├─ prd_scripter_agent
   └─ prd_saver_agent (had store_prd tool)
```
**Problem**: When prd_saver requested confirmation, the SequentialAgent couldn't resume → "app is not resumable" error

### After (Artifact Handoff Pattern - FIXED)
```
root_agent (Agent with HITL at root level)
├─ Tools: search_existing_prds, get_prd, read_prd_from_temp, store_prd
└─ virtual_product_manager_agent (SequentialAgent)
   ├─ market_researcher_agent (google_search)
   ├─ user_journey_agent
   └─ prd_scripter_agent (write_prd_to_temp) ← saves to /tmp/temp_prd_draft.md
```
**Solution**:
- SequentialAgent runs deterministically (no HITL inside)
- PRD Scripter saves PRD to `/tmp/temp_prd_draft.md` (artifact handoff)
- Root agent reads PRD from temp file after SequentialAgent completes
- Root agent handles both HITL checkpoints conversationally
- File system acts as "shared memory" between SequentialAgent and root
- **Key Benefits**:
  - No tool mixing (MCP tools not active during SequentialAgent execution)
  - No double execution (SequentialAgent runs once, saves to file, completes)
  - Clean HITL (root agent handles all user interaction)
  - PRD preserved reliably (no truncation, no loss)

## Test Workflow

### Test Case 1: New PRD with No Duplicates

**Input**: "Create a PRD for a mobile fitness tracking app"

**Expected Behavior**:
1. ✓ Root agent calls `search_existing_prds("mobile fitness tracking app")`
2. ✓ Search returns no results (or empty results)
3. ✓ Root agent informs you: "No similar PRDs found, proceeding with workflow"
4. ✓ Root agent delegates to `market_researcher_agent`
   - Sub-agent uses google_search to research fitness apps
   - Returns market research findings
5. ✓ Root agent delegates to `user_journey_agent`
   - Sub-agent creates user personas and journeys
   - Returns user journey documentation
6. ✓ Root agent delegates to `prd_scripter_agent`
   - Sub-agent compiles PRD from all context
   - Returns complete PRD markdown
7. **HITL #2 - CRITICAL TEST**: Root agent calls `store_prd()`
   - ✓ Tool shows PRD preview (first 500 chars)
   - ✓ Tool requests confirmation: "Please review the PRD and approve saving..."
   - ✓ **YOU APPROVE** the confirmation
   - ✓ Agent successfully **resumes** (no "app is not resumable" error)
   - ✓ PRD saved to MCP server → GCS bucket
   - ✓ Returns success message with prd_id

**Success Criteria**: No resumability errors, PRD successfully saved

### Test Case 2: Duplicate Detection (HITL #1)

**Setup**: First, create a PRD using Test Case 1, then run this test.

**Input**: "Create a PRD for a fitness tracking mobile application"

**Expected Behavior**:
1. ✓ Root agent calls `search_existing_prds("fitness tracking mobile application")`
2. ✓ Search returns results (the PRD from Test Case 1)
3. **HITL #1 - CRITICAL TEST**: Root agent presents results and asks:
   ```
   I found the following similar PRDs:
   - Product: Mobile Fitness Tracking App (prd_id: mobile_fitness_tracking_app_1234567890)
     Summary: ...
     Created: 2025-12-09

   What would you like to do?
   a) View one of the existing PRDs (provide prd_id)
   b) Create a new PRD anyway
   c) Refine your idea and search again
   ```
4. ✓ **YOU RESPOND**: Choose one of the options
5. ✓ Agent waits for your response before proceeding

**Option A: View Existing PRD**
- Input: "View the existing PRD: mobile_fitness_tracking_app_1234567890"
- ✓ Root agent calls `get_prd("mobile_fitness_tracking_app_1234567890")`
- ✓ Returns full PRD content and metadata
- ✓ Workflow ends

**Option B: Create New PRD Anyway**
- Input: "Create a new PRD anyway"
- ✓ Root agent proceeds to Step 3 (market research)
- ✓ Continues through entire workflow (same as Test Case 1)
- ✓ HITL #2 triggers for confirmation before saving

**Option C: Refine and Search Again**
- Input: "Let me refine: create a PRD for a senior citizen fitness tracker"
- ✓ Root agent calls `search_existing_prds("senior citizen fitness tracker")`
- ✓ Returns new search results
- ✓ Repeats HITL #1 decision point

**Success Criteria**: Agent waits for user decision, doesn't auto-proceed to create PRD

### Test Case 3: Rejection of PRD Save

**Input**: "Create a PRD for a weather forecasting app"

**Expected Behavior**:
1-6. Same as Test Case 1 (search, market research, user journey, PRD generation)
7. **HITL #2**: Root agent calls `store_prd()`
   - ✓ Tool shows PRD preview
   - ✓ Tool requests confirmation
   - ✓ **YOU REJECT** the confirmation
   - ✓ Workflow stops
   - ✓ PRD NOT saved to storage
   - ✓ Agent acknowledges rejection

**Success Criteria**: Agent respects rejection, doesn't save PRD

## Key Testing Points

### HITL #1: Duplicate Detection
- **Implementation**: Via agent instructions (conversational HITL)
- **Test**: Agent presents options and waits for user response
- **Success**: No automatic progression to workflow when duplicates found

### HITL #2: PRD Save Confirmation
- **Implementation**: Via `tool_context.request_confirmation()`
- **Test**: Agent pauses, shows preview, requests approval
- **Success**: Agent resumes correctly after approval (no "app is not resumable" error)

## Debugging Tips

### Check Server Logs
```bash
# Monitor ADK web server logs
tail -f /path/to/adk/logs
```

### Check MCP Server Health
```bash
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  "https://prd-mcp-server-your-project-number.us-central1.run.app/sse" \
  -d '{"method": "tools/list"}'
```

### Check GCS Bucket for Saved PRDs
```bash
gcloud storage ls gs://your-prd-storage/prds/
```

### Search Existing PRDs via MCP
```bash
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  "https://prd-mcp-server-your-project-number.us-central1.run.app/sse" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "search_existing_prds",
      "arguments": {"query": "fitness"}
    }
  }'
```

## Expected Files After Testing

After successful Test Case 1, you should see:
- **GCS**: `gs://your-prd-storage/prds/mobile_fitness_tracking_app_{timestamp}.md`
- **Metadata**: Product name, author, version, created_at, summary
- **Searchable**: PRD indexed in Vertex AI Search (prd-search-datastore_1765378075006)

## Troubleshooting

### Error: "app is not resumable"
**Root Cause**: SequentialAgent is not resumable - cannot pause/resume for HITL
**Fix**: Use blog-writer pattern instead - single Agent as root with manual workflow orchestration via detailed instructions

### Error: "MCP_SERVER_URL not configured"
**Root Cause**: .env not loaded
**Fix**: Ensure `.env` file exists with `MCP_SERVER_URL=https://prd-mcp-server-your-project-number.us-central1.run.app`

### Error: "Failed to parse parameter metadata: Dict"
**Root Cause**: ADK can't handle generic Dict parameters
**Fix**: Verify store_prd signature uses `author: str, version: str` instead of `metadata: Dict`

### Search Returns No Results (But PRD Exists)
**Root Cause**: Vertex AI Search indexing delay
**Fix**: Wait 5-10 minutes for indexing, or check fallback GCS search is working

## Success Indicators

✅ **HITL #1 Works**: Agent pauses when duplicates found, waits for user decision
✅ **HITL #2 Works**: Agent pauses before save, requests confirmation, resumes successfully
✅ **No Resumability Errors**: No "app is not resumable" errors during HITL #2
✅ **PRDs Saved**: Files appear in GCS bucket after approval
✅ **PRDs Searchable**: Subsequent searches find saved PRDs

## Next Steps After Testing

Once testing confirms HITL works correctly:

1. **Deploy to Agent Engine**:
   ```bash
   cd /Users/your-project-id/Documents/agents
   source pm_agent/venv313/bin/activate
   adk deploy agent_engine --project=your-project-id --region=us-central1 \
     --staging_bucket=gs://your-staging-bucket \
     --display_name="pm-agent-v3-hitl" \
     --description="PM agent with iterative refinement pattern for HITL" \
     --trace_to_cloud pm_agent
   ```

2. **Test in Production**: Run the same test cases via deployed agent

3. **Monitor Traces**: Check Cloud Trace for agent execution flow
