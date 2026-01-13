# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] - 2026-01-13

### Added
- **Tracing Support**: Full OpenTelemetry tracing integration with Agent Engine
  - Added `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY` environment variable
  - Added `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT` for prompt/response logging
  - Traces viewable in Cloud Trace console and Vertex AI Reasoning Engines UI
- **deployment.env.example**: Template for Agent Engine deployment configuration
- Updated documentation with latest tracing configuration (January 2026 standard)

### Changed
- **Deployment Process**: Now uses `--env_file` parameter instead of deprecated `--trace_to_cloud` flag
- **MCP Server URL**: Updated to use correct Cloud Run service URL (`https://prd-mcp-server-4bz26qs7xq-uc.a.run.app`)
- **deploy_and_test.py**: Added environment variables configuration for ReasoningEngine deployment
- **README.md**:
  - Added tracing environment variables documentation
  - Updated deployment steps to include `deployment.env` creation
  - Added telemetry and logging APIs to prerequisites
  - Updated monitoring section with both Cloud Trace and Vertex AI console links

### Fixed
- MCP Server connection issue: Environment variable `MCP_SERVER_URL` now properly passed to deployed agent
- Tracing not enabled: Switched from deprecated `enable_tracing=True` to environment variables

### Deprecated
- `--trace_to_cloud` CLI flag (use environment variables instead)
- `enable_tracing=True` parameter in AdkApp initialization

## [1.0.0] - 2025-12-12

### Added
- Initial release of PM Agent Example
- Sequential multi-agent workflow (Market Researcher → User Journey → PRD Scripter)
- MCP Server for PRD storage and retrieval
- Human-in-the-loop pattern with duplicate detection and PRD approval
- Integration with Google Cloud Storage and Vertex AI Search
- Cloud Run deployment for MCP server
- Agent Engine deployment for PM agent
- Gemini Enterprise registration support

### Features
- Market research via Google Search
- User persona and journey generation
- Comprehensive PRD creation with markdown and HTML output
- Semantic search for existing PRDs
- Duplicate PRD detection and prevention
