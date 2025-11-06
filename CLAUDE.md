# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Model Context Protocol (MCP) server for KIMAI 2, a time tracking application. It exposes 20+ tools that enable LLMs to interact with KIMAI for time tracking, project management, and reporting through the KIMAI REST API.

**Technology Stack:**
- Python 3.10+ with asyncio
- MCP SDK (mcp>=1.0.0) for protocol implementation
- httpx for async HTTP requests
- Pydantic v2 for input validation and schema generation

## Development Commands

### Setup and Installation
```bash
# Initial setup (creates venv, installs dependencies, creates .env)
./setup.sh

# Manual setup
uv venv
uv pip install -r requirements.txt
cp .env.example .env
# Edit .env with your KIMAI_BASE_URL and KIMAI_API_TOKEN
```

### Testing
```bash
# Test KIMAI API connection
source .venv/bin/activate
python test_connection.py

# Run the MCP server directly (waits for stdio input)
python server.py
```

### Environment Configuration
Required environment variables (set in `.env` or MCP client config):
- `KIMAI_BASE_URL`: Base URL of KIMAI instance (e.g., http://localhost:8001)
- `KIMAI_API_TOKEN`: Bearer token from KIMAI User Profile > API

## Architecture

### Core Components

**server.py** (1566 lines) - Single-file MCP server with clear sections:

1. **Pydantic Models (lines ~35-550)**: Input validation models for all 20+ tools
   - Each tool has a dedicated model with strict validation
   - All models use `ConfigDict(extra='forbid')` to reject unknown fields
   - Field-level validation with descriptions for LLM schema generation

2. **KimaiClient (lines ~570-660)**: HTTP client wrapper
   - Async request method handles all HTTP operations
   - Bearer token authentication via headers
   - Comprehensive error handling with actionable messages
   - Base URL joining for API endpoints

3. **Response Formatters (lines ~665-845)**: Markdown and JSON output
   - Functions like `format_timesheet_markdown()`, `format_project_markdown()`
   - `truncate_if_needed()` caps output at 25000 characters
   - Supports both human-readable markdown and structured JSON

4. **Tool Registration (lines ~859-1133)**: MCP tool definitions
   - `@app.list_tools()` decorator registers all tools
   - Each Tool includes name, detailed description, and Pydantic schema

5. **Tool Handlers (lines ~1136-1546)**: Implementation logic
   - `@app.call_tool()` decorator handles all tool invocations
   - Pattern: validate input → build request → call API → format response
   - All exceptions caught and returned as error messages

6. **Main Entry Point (lines ~1553-1566)**: stdio server setup

### Request Flow

1. LLM calls tool with parameters
2. Pydantic model validates input (raises exception if invalid)
3. Handler builds KIMAI API request (GET/POST/PATCH/DELETE)
4. `KimaiClient.request()` executes HTTP call with auth
5. Response formatted as markdown or JSON based on `format` parameter
6. Result returned as `TextContent` to LLM

### Tool Categories

- **Timesheets (7 tools)**: list, get, start, stop, create, update, delete
- **Projects (4 tools)**: list, get, create, update
- **Activities (4 tools)**: list, get, create, update
- **Customers (4 tools)**: list, get, create, update
- **Reporting (1 tool)**: get_timesheet_summary (aggregates data client-side)

### Key Design Patterns

**Input Validation**: Every tool has a Pydantic model ensuring type safety and providing automatic schema generation for LLM tool calling.

**Format Flexibility**: Most tools support `format` parameter ("json" or "markdown") to choose between structured data and human-readable output.

**Error Handling**: HTTP errors are caught and transformed into user-friendly messages with troubleshooting hints (e.g., "check your API token", "verify IDs exist").

**Pagination**: List endpoints support `page` and `size` parameters with defaults (page=1, size=50, max=100).

**Datetime Handling**: Uses ISO 8601 format strings and `datetime.now(timezone.utc)` for timestamps.

## Common Modification Patterns

### Adding a New Tool

1. Create Pydantic input model with validation rules
2. Add tool definition in `@app.list_tools()` with clear description
3. Add handler case in `@app.call_tool()` following this pattern:
   ```python
   elif name == "new_tool":
       params = NewToolInput(**arguments)
       # Build API request
       result = await client.request(method, endpoint, params=query_params, json_data=data)
       # Format response
       if params.format == "markdown":
           return [TextContent(type="text", text=format_new_thing_markdown(result))]
       return [TextContent(type="text", text=str(result))]
   ```
4. Add formatter function if markdown output is supported

### Modifying API Calls

- KIMAI API endpoints follow pattern: `/api/{resource}` or `/api/{resource}/{id}`
- Query parameters for filtering use keys like "project", "customer", "begin", "end"
- Boolean filters sent as "1" or "0" strings (see line ~1158)
- POST/PATCH requests use `json_data` parameter

### Testing Changes

1. Modify code
2. Test with `python test_connection.py` to verify basic connectivity
3. Test MCP integration by configuring in Claude Code/Desktop and invoking tools
4. Check that Pydantic validation catches invalid inputs appropriately

## KIMAI API Specifics

- API base path is `/api/` (appended in `KimaiClient.request()`)
- Authentication via `Authorization: Bearer {token}` header
- Timesheet durations are in seconds (convert to hours with `/ 3600`)
- Running timesheets have `end: null`
- Colors use hex format: `#RRGGBB`
- Date filters use ISO 8601 format
- Empty DELETE responses return `{"success": True}`

## Important Notes

- This is a single-file MCP server - keep all code in server.py unless complexity requires refactoring
- Pydantic schemas auto-generate tool descriptions for LLMs - keep field descriptions clear and include examples
- The server runs via stdio (stdin/stdout) - no REST endpoints or UI
- Character limit of 25000 prevents token overload when returning large datasets
- test_connection.py imports from server.py (requires `KimaiConfig` and `KimaiClient` to be importable)
- The setup.sh script handles initial environment setup for new users