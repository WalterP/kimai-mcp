# KIMAI MCP Server

A Model Context Protocol (MCP) server for [KIMAI 2](https://www.kimai.org/) time tracking application. This server enables Large Language Models to interact
with KIMAI for time tracking, project management, and reporting.

## Features

### Time Tracking

- **Start/Stop Time Entries**: Begin and end time tracking in real-time
- **Create Time Entries**: Add historical time entries with custom start/end times
- **Update Time Entries**: Modify existing entries (times, descriptions, tags)
- **Delete Time Entries**: Remove incorrect or duplicate entries
- **Query Time Entries**: Search and filter timesheets by project, activity, customer, user, date range, and status

### Project & Activity Management

- **List Projects & Activities**: Browse available projects and activities
- **Create Projects**: Set up new projects under customers
- **Create Activities**: Define new work types (global or project-specific)
- **Update Projects & Activities**: Modify names, visibility, billable status, and colors

### Customer Management

- **List Customers**: View all customers
- **Create Customers**: Add new clients with currency preferences
- **Update Customers**: Modify customer information and settings

### Reporting & Analytics

- **Timesheet Summaries**: Generate reports with total hours, billable vs non-billable time
- **Project Breakdowns**: See time distribution across projects
- **Activity Analysis**: Analyze time spent on different activity types
- **Flexible Filtering**: Filter reports by user, customer, project, activity, and date range

## Prerequisites

- **KIMAI 2**: A running KIMAI 2 instance (version 2.0 or higher)
- **Python**: Python 3.10 or higher
- **API Token**: Bearer token from your KIMAI user profile

## Installation

### Quick Setup (Recommended)

1. **Clone or download this repository:**
   ```bash
   cd /projects/personal/kimai-mcp
   ```

2. **Run the setup script:**
   ```bash
   ./setup.sh
   ```

3. **Edit `.env` file with your KIMAI credentials:**
   ```bash
   nano .env  # or use your preferred editor
   ```

4. **Test the connection:**
   ```bash
   source .venv/bin/activate
   python3 test_connection.py
   ```

### Manual Setup

1. **Install dependencies using uv:**
   ```bash
   uv venv
   uv pip install -r requirements.txt
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your KIMAI URL and API token
   ```

### Generate KIMAI API Token

- Log into your KIMAI instance
- Navigate to: User Profile > API
- Click "Create New Token"
- Copy the token and add it to your `.env` file

## Configuration

### Environment Variables

The server requires two environment variables:

| Variable          | Description                         | Example                 |
|-------------------|-------------------------------------|-------------------------|
| `KIMAI_BASE_URL`  | Base URL of your KIMAI instance     | `http://localhost:8001` |
| `KIMAI_API_TOKEN` | Bearer token for API authentication | `<token_here>`          |

### Claude Code Configuration

To use this MCP server with Claude Code (CLI), add it to your MCP settings file.

**Location:** `~/.claude/mcp_settings.json` or your project's `.claude/mcp_settings.json`

Add the following configuration:

```json
{
  "mcpServers": {
    "kimai": {
      "command": "/projects/personal/kimai-mcp/.venv/bin/python",
      "args": ["/projects/personal/kimai-mcp/server.py"],
      "env": {
        "KIMAI_BASE_URL": "http://localhost:8001",
        "KIMAI_API_TOKEN": "<your_api_token_here>"
      }
    }
  }
}
```

**Important Notes:**
- Use absolute paths for both `command` and `args`
- Replace `/projects/personal/kimai-mcp` with your actual installation path
- Replace `<your_api_token_here>` with your KIMAI API token
- The Python binary should point to your virtual environment

After adding the configuration, restart Claude Code to load the MCP server. You can verify it's loaded by checking for KIMAI-related tools.

### Claude Desktop Configuration

Add this MCP server to your Claude Desktop configuration:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
	"kimai": {
	  "command": "/projects/personal/kimai-mcp/.venv/bin/python",
	  "args": ["/projects/personal/kimai-mcp/server.py"],
	  "env": {
		"KIMAI_BASE_URL": "http://localhost:8001",
		"KIMAI_API_TOKEN": "your_api_token_here"
	  }
	}
  }
}
```

**Note:** Make sure to use absolute paths and point to the Python binary in your virtual environment.

## Available Tools

### Timesheet Tools

#### `list_timesheets`

List timesheet entries with filtering options.

**Parameters:**

- `user` (optional): Filter by user ID
- `customer` (optional): Filter by customer ID
- `project` (optional): Filter by project ID
- `activity` (optional): Filter by activity ID
- `active` (optional): Filter for running timesheets only
- `exported` (optional): Filter by export status
- `begin` (optional): Start date filter (ISO 8601)
- `end` (optional): End date filter (ISO 8601)
- `page` (default: 1): Page number for pagination
- `size` (default: 50): Results per page (max 100)
- `format` (default: "json"): Response format ("json" or "markdown")

**Example:**

```
List all running timesheets
Show me timesheets for project 1 from last week
```

#### `get_timesheet`

Get detailed information about a specific timesheet.

**Parameters:**

- `id`: Timesheet ID (required)
- `format`: Response format ("json" or "markdown")

**Example:**

```
Get details for timesheet #1245
```

#### `start_timesheet`

Start tracking time for a project and activity.

**Parameters:**

- `project`: Project ID (required)
- `activity`: Activity ID (required)
- `description` (optional): Work description
- `tags` (optional): Comma-separated tags

**Example:**

```
Start tracking time for project 1, activity 355
Start timer for "Code Review" on project 2
```

#### `stop_timesheet`

Stop a running timesheet entry.

**Parameters:**

- `id`: Timesheet ID to stop (required)

**Example:**

```
Stop timesheet #1245
```

#### `create_timesheet`

Create a time entry with specific start/end times.

**Parameters:**

- `project`: Project ID (required)
- `activity`: Activity ID (required)
- `begin`: Start datetime in ISO 8601 format (required)
- `end` (optional): End datetime (omit for running entry)
- `description` (optional): Work description
- `tags` (optional): Comma-separated tags

**Example:**

```
Create a timesheet for yesterday from 9am to 5pm on project 1, activity 355
Log 3 hours of work for project 2, activity 10
```

#### `update_timesheet`

Update an existing timesheet entry.

**Parameters:**

- `id`: Timesheet ID (required)
- `begin` (optional): New start datetime
- `end` (optional): New end datetime
- `description` (optional): Updated description
- `tags` (optional): Updated tags

**Example:**

```
Update timesheet #1245 with description "Fixed bug in authentication"
Change the end time of timesheet #1244 to 6pm
```

#### `delete_timesheet`

Delete a timesheet entry.

**Parameters:**

- `id`: Timesheet ID (required)

**Example:**

```
Delete timesheet #1245
```

### Project Tools

#### `list_projects`

List all projects with filtering.

**Parameters:**

- `customer` (optional): Filter by customer ID
- `visible` (optional): Filter by visibility
- `page` (default: 1): Page number
- `size` (default: 50): Results per page
- `format` (default: "json"): Response format

**Example:**

```
List all projects
Show me projects for customer 1
```

#### `get_project`

Get details about a specific project.

**Parameters:**

- `id`: Project ID (required)
- `format`: Response format

**Example:**

```
Get details for project #1
```

#### `create_project`

Create a new project.

**Parameters:**

- `name`: Project name (required)
- `customer`: Customer ID (required)
- `visible` (default: true): Visibility
- `billable` (default: true): Billable status
- `color` (optional): Hex color code

**Example:**

```
Create a new project "Website Redesign" for customer 1
```

#### `update_project`

Update a project's details.

**Parameters:**

- `id`: Project ID (required)
- `name` (optional): New name
- `visible` (optional): New visibility
- `billable` (optional): New billable status
- `color` (optional): New color

**Example:**

```
Rename project #1 to "Mobile App Development"
Make project #2 non-billable
```

### Activity Tools

#### `list_activities`

List all activities.

**Parameters:**

- `project` (optional): Filter by project ID
- `visible` (optional): Filter by visibility
- `page` (default: 1): Page number
- `size` (default: 50): Results per page
- `format` (default: "json"): Response format

**Example:**

```
List all activities
Show activities for project 1
```

#### `get_activity`

Get details about a specific activity.

**Parameters:**

- `id`: Activity ID (required)
- `format`: Response format

**Example:**

```
Get details for activity #355
```

#### `create_activity`

Create a new activity.

**Parameters:**

- `name`: Activity name (required)
- `project` (optional): Project ID (omit for global)
- `visible` (default: true): Visibility
- `billable` (default: true): Billable status
- `color` (optional): Hex color code

**Example:**

```
Create a new activity called "Code Review"
Create a global activity "Meeting"
```

#### `update_activity`

Update an activity's details.

**Parameters:**

- `id`: Activity ID (required)
- `name` (optional): New name
- `visible` (optional): New visibility
- `billable` (optional): New billable status
- `color` (optional): New color

**Example:**

```
Rename activity #355 to "Senior Code Review"
```

### Customer Tools

#### `list_customers`

List all customers.

**Parameters:**

- `visible` (optional): Filter by visibility
- `page` (default: 1): Page number
- `size` (default: 50): Results per page
- `format` (default: "json"): Response format

**Example:**

```
List all customers
```

#### `get_customer`

Get details about a specific customer.

**Parameters:**

- `id`: Customer ID (required)
- `format`: Response format

**Example:**

```
Get details for customer #1
```

#### `create_customer`

Create a new customer.

**Parameters:**

- `name`: Customer name (required)
- `currency` (default: "USD"): 3-letter currency code
- `visible` (default: true): Visibility
- `billable` (default: true): Billable status
- `color` (optional): Hex color code

**Example:**

```
Create a new customer "Acme Corporation" with EUR currency
```

#### `update_customer`

Update a customer's details.

**Parameters:**

- `id`: Customer ID (required)
- `name` (optional): New name
- `currency` (optional): New currency
- `visible` (optional): New visibility
- `billable` (optional): New billable status
- `color` (optional): New color

**Example:**

```
Change customer #1 currency to CAD
```

### Reporting Tools

#### `get_timesheet_summary`

Generate summary reports of timesheet data.

**Parameters:**

- `user` (optional): Filter by user ID
- `customer` (optional): Filter by customer ID
- `project` (optional): Filter by project ID
- `activity` (optional): Filter by activity ID
- `begin` (optional): Start date (ISO 8601)
- `end` (optional): End date (ISO 8601)
- `format` (default: "markdown"): Response format

**Example:**

```
Generate a timesheet report for this week
Show me total hours for project 1 this month
Summary of all billable hours for customer 1
```

## Usage Examples

### Time Tracking Workflow

```
User: Start tracking time for the FNLR project
Claude: [Uses list_projects to find "First Nations Land Register"]
        [Uses list_activities to find appropriate activity]
        [Uses start_timesheet with project=1, activity=355]

User: Stop the timer
Claude: [Uses list_timesheets with active=true to find running entry]
        [Uses stop_timesheet with the ID]

User: Add a description "Implemented authentication feature"
Claude: [Uses update_timesheet to add description]
```

### Reporting Workflow

```
User: How much time did I spend on project 1 this week?
Claude: [Uses get_timesheet_summary with project=1, date filters]
        [Returns markdown report with breakdown]

User: Show me all my timesheets from yesterday
Claude: [Uses list_timesheets with date filters, format=markdown]
        [Returns formatted list of entries]
```

### Project Setup Workflow

```
User: Create a new customer "Acme Corp" and project "Website Redesign"
Claude: [Uses create_customer with name="Acme Corp"]
        [Uses create_project with the new customer ID]
        [Uses create_activity for common tasks]

User: What activities are available for this project?
Claude: [Uses list_activities with the new project ID]
```

## Response Formats

The server supports two response formats:

### JSON Format

Structured data ideal for programmatic processing:

```json
{
  "id": 1245,
  "project": 1,
  "activity": 355,
  "begin": "2025-11-05T15:36:00+0100",
  "end": "2025-11-05T18:10:00+0100",
  "duration": 9240
}
```

### Markdown Format

Human-readable format ideal for reports and summaries:

```markdown
## Timesheet #1245

**Status:** ✓ Completed
**Project ID:** 1
**Activity ID:** 355
**Duration:** 2.57 hours (9240 seconds)
```

## Error Handling

The server provides clear, actionable error messages:

- **Authentication errors**: Check your API token
- **Not found errors**: Verify IDs exist
- **Validation errors**: Review parameter formats
- **Network errors**: Verify KIMAI URL is accessible

All errors include suggestions for resolution.

## Development

### Testing the Server

```bash
# Set environment variables
export KIMAI_BASE_URL=http://localhost:8001
export KIMAI_API_TOKEN=your_token

# Run the server directly (will wait for stdio input)
python server.py
```

### Project Structure

```
kimai-mcp/
├── server.py           # Main MCP server implementation
├── requirements.txt    # Python dependencies
├── .env.example       # Environment variable template
└── README.md          # This file
```

## Troubleshooting

### Server won't start

- Check Python version (3.10+ required)
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Ensure environment variables are set

### API errors

- Verify KIMAI instance is running and accessible
- Check API token is valid (not expired)
- Ensure token has appropriate permissions

### Empty results

- Check filters are not too restrictive
- Verify data exists in KIMAI
- Try without filters first

## Contributing

Contributions are welcome! Please ensure:

- Code follows Python best practices
- Pydantic models validate all inputs
- Error messages are clear and actionable
- Documentation is updated

## License

This project is open source and available under the MIT License.

## Support

For issues or questions:

- KIMAI documentation: https://www.kimai.org/documentation/
- MCP documentation: https://modelcontextprotocol.io/

## Changelog

### v1.0.0 (2025-11-06)

- Initial release
- Full timesheet management (CRUD operations)
- Project, activity, and customer management
- Summary reporting and analytics
- Support for JSON and Markdown response formats
- Comprehensive error handling
