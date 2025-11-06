# KIMAI MCP Server - Quick Start Guide

## 🚀 Get Started in 3 Steps

### 1. Install & Setup

```bash
cd /projects/personal/kimai-mcp
./setup.sh
```

### 2. Configure

Edit `.env` file:
```bash
KIMAI_BASE_URL=http://localhost:8001
KIMAI_API_TOKEN=your_token_here
```

### 3. Test

```bash
source .venv/bin/activate
python3 test_connection.py
```

## 📝 Add to Claude Desktop

Edit your Claude Desktop config:

**Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "kimai": {
      "command": "/projects/personal/kimai-mcp/.venv/bin/python",
      "args": ["/projects/personal/kimai-mcp/server.py"],
      "env": {
        "KIMAI_BASE_URL": "http://localhost:8001",
        "KIMAI_API_TOKEN": "your_token_here"
      }
    }
  }
}
```

## 💡 Example Conversations with Claude

### Time Tracking
```
You: Start tracking time for the FNLR project
You: What am I currently tracking?
You: Stop the timer and add description "Fixed authentication bug"
```

### Reporting
```
You: How much time did I spend this week?
You: Show me all time entries for project 1 from last month
You: Generate a summary of billable vs non-billable hours
```

### Project Management
```
You: List all my projects
You: Create a new project "Mobile App" for customer Acme Corp
You: What activities are available for project 1?
```

## 🛠️ Available Tools (21 total)

**Timesheets (7)**
- `list_timesheets` - Query time entries
- `get_timesheet` - Get specific entry
- `start_timesheet` - Begin tracking
- `stop_timesheet` - End tracking
- `create_timesheet` - Add historical entry
- `update_timesheet` - Modify entry
- `delete_timesheet` - Remove entry

**Projects (4)**
- `list_projects`, `get_project`, `create_project`, `update_project`

**Activities (4)**
- `list_activities`, `get_activity`, `create_activity`, `update_activity`

**Customers (4)**
- `list_customers`, `get_customer`, `create_customer`, `update_customer`

**Reporting (1)**
- `get_timesheet_summary` - Analytics & summaries

## 📊 Response Formats

Most tools support both formats:

**JSON** - Structured data:
```json
{"id": 1245, "duration": 9240, "project": 1}
```

**Markdown** - Human-readable:
```markdown
## Timesheet #1245
**Duration:** 2.57 hours
**Project ID:** 1
```

## 🔧 Troubleshooting

### Connection Issues
```bash
# Test connection
source .venv/bin/activate
python3 test_connection.py

# Check KIMAI is running
curl http://localhost:8001/api/version
```

### Claude Desktop Issues
1. Restart Claude Desktop after config changes
2. Check paths are absolute in config
3. Verify virtual environment Python path
4. Check logs in Claude Desktop

## 📚 Full Documentation

See [README.md](README.md) for complete documentation.

## 🎯 Quick Commands Reference

```bash
# Setup
./setup.sh

# Test
source .venv/bin/activate && python3 test_connection.py

# Update dependencies
uv pip install -r requirements.txt

# Git operations
git status
git log --oneline
```

## 🆘 Getting Help

- KIMAI API: http://localhost:8001/api/doc
- KIMAI Docs: https://www.kimai.org/documentation/
- MCP Protocol: https://modelcontextprotocol.io/

---

**Version:** 1.0.0
**Last Updated:** 2025-11-06
**KIMAI Version:** 2.18.0+
