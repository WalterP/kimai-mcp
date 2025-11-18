#!/usr/bin/env python3
"""
KIMAI MCP Server

A Model Context Protocol (MCP) server for KIMAI 2 time tracking application.
Provides tools for managing timesheets, projects, activities, customers, and reporting.

This server enables LLMs to:
- Track time entries (start/stop/create/update/delete)
- Manage projects, activities, and customers
- Generate reports and analytics
- Query historical time tracking data
"""

import asyncio
import os
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import urljoin

import httpx
from mcp.server import Server
from mcp.types import TextContent, Tool
from pydantic import BaseModel, Field, ConfigDict

# Constants
CHARACTER_LIMIT = 25000
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100


# ============================================================================
# Pydantic Models for Input Validation
# ============================================================================

class KimaiConfig(BaseModel):
    """KIMAI instance configuration."""
    model_config = ConfigDict(extra='forbid')

    base_url: str = Field(
        ...,
        description="Base URL of KIMAI instance (e.g., http://localhost:8001)"
    )
    api_token: str = Field(
        ...,
        description="Bearer token for API authentication"
    )


class ListTimesheetsInput(BaseModel):
    """Input for listing timesheets."""
    model_config = ConfigDict(extra='forbid')

    user: Optional[int] = Field(
        None,
        description="Filter by user ID. Example: 1"
    )
    customer: Optional[int] = Field(
        None,
        description="Filter by customer ID. Example: 1"
    )
    project: Optional[int] = Field(
        None,
        description="Filter by project ID. Example: 5"
    )
    activity: Optional[int] = Field(
        None,
        description="Filter by activity ID. Example: 10"
    )
    page: int = Field(
        1,
        ge=1,
        description="Page number for pagination (1-based). Example: 1"
    )
    size: int = Field(
        DEFAULT_PAGE_SIZE,
        ge=1,
        le=MAX_PAGE_SIZE,
        description=f"Number of results per page (max {MAX_PAGE_SIZE}). Example: 50"
    )
    active: Optional[bool] = Field(
        None,
        description="Filter for active (running) timesheets only. Example: true"
    )
    exported: Optional[bool] = Field(
        None,
        description="Filter by export status. Example: false"
    )
    begin: Optional[str] = Field(
        None,
        description="Filter entries starting from this datetime (ISO 8601 format). Example: 2025-11-01T00:00:00"
    )
    end: Optional[str] = Field(
        None,
        description="Filter entries until this datetime (ISO 8601 format). Example: 2025-11-30T23:59:59"
    )
    format: str = Field(
        "json",
        pattern="^(json|markdown)$",
        description="Response format: 'json' for structured data or 'markdown' for human-readable text"
    )


class GetTimesheetInput(BaseModel):
    """Input for getting a specific timesheet."""
    model_config = ConfigDict(extra='forbid')

    id: int = Field(
        ...,
        gt=0,
        description="Timesheet ID. Example: 1245"
    )
    format: str = Field(
        "json",
        pattern="^(json|markdown)$",
        description="Response format: 'json' or 'markdown'"
    )


class StartTimesheetInput(BaseModel):
    """Input for starting a new timesheet entry."""
    model_config = ConfigDict(extra='forbid')

    project: int = Field(
        ...,
        gt=0,
        description="Project ID to track time for. Example: 1"
    )
    activity: int = Field(
        ...,
        gt=0,
        description="Activity ID to track. Example: 355"
    )
    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Optional description of the work. Example: 'Implementing new feature'"
    )
    tags: Optional[str] = Field(
        None,
        description="Comma-separated tags. Example: 'development,urgent'"
    )


class StopTimesheetInput(BaseModel):
    """Input for stopping a running timesheet."""
    model_config = ConfigDict(extra='forbid')

    id: int = Field(
        ...,
        gt=0,
        description="Timesheet ID to stop. Example: 1245"
    )


class CreateTimesheetInput(BaseModel):
    """Input for creating a complete timesheet entry."""
    model_config = ConfigDict(extra='forbid')

    project: int = Field(
        ...,
        gt=0,
        description="Project ID. Example: 1"
    )
    activity: int = Field(
        ...,
        gt=0,
        description="Activity ID. Example: 355"
    )
    begin: str = Field(
        ...,
        description="Start datetime in ISO 8601 format (YYYY-MM-DDTHH:MM:SS). Example: 2025-11-06T09:00:00"
    )
    end: Optional[str] = Field(
        None,
        description="End datetime in ISO 8601 format. Omit for running entry. Example: 2025-11-06T17:00:00"
    )
    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Work description. Example: 'Code review and testing'"
    )
    tags: Optional[str] = Field(
        None,
        description="Comma-separated tags. Example: 'review,testing'"
    )


class UpdateTimesheetInput(BaseModel):
    """Input for updating an existing timesheet."""
    model_config = ConfigDict(extra='forbid')

    id: int = Field(
        ...,
        gt=0,
        description="Timesheet ID to update. Example: 1245"
    )
    begin: Optional[str] = Field(
        None,
        description="New start datetime (ISO 8601). Example: 2025-11-06T09:30:00"
    )
    end: Optional[str] = Field(
        None,
        description="New end datetime (ISO 8601). Example: 2025-11-06T17:30:00"
    )
    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Updated description"
    )
    tags: Optional[str] = Field(
        None,
        description="Updated tags (comma-separated)"
    )


class DeleteTimesheetInput(BaseModel):
    """Input for deleting a timesheet."""
    model_config = ConfigDict(extra='forbid')

    id: int = Field(
        ...,
        gt=0,
        description="Timesheet ID to delete. Example: 1245"
    )


class ListProjectsInput(BaseModel):
    """Input for listing projects."""
    model_config = ConfigDict(extra='forbid')

    customer: Optional[int] = Field(
        None,
        description="Filter by customer ID. Example: 1"
    )
    visible: Optional[bool] = Field(
        None,
        description="Filter by visibility status. Example: true"
    )
    page: int = Field(
        1,
        ge=1,
        description="Page number (1-based). Example: 1"
    )
    size: int = Field(
        DEFAULT_PAGE_SIZE,
        ge=1,
        le=MAX_PAGE_SIZE,
        description=f"Results per page (max {MAX_PAGE_SIZE}). Example: 50"
    )
    format: str = Field(
        "json",
        pattern="^(json|markdown)$",
        description="Response format: 'json' or 'markdown'"
    )


class GetProjectInput(BaseModel):
    """Input for getting a specific project."""
    model_config = ConfigDict(extra='forbid')

    id: int = Field(
        ...,
        gt=0,
        description="Project ID. Example: 1"
    )
    format: str = Field(
        "json",
        pattern="^(json|markdown)$",
        description="Response format: 'json' or 'markdown'"
    )


class CreateProjectInput(BaseModel):
    """Input for creating a new project."""
    model_config = ConfigDict(extra='forbid')

    name: str = Field(
        ...,
        min_length=1,
        max_length=150,
        description="Project name. Example: 'New Website Development'"
    )
    customer: int = Field(
        ...,
        gt=0,
        description="Customer ID. Example: 1"
    )
    visible: bool = Field(
        True,
        description="Whether project is visible. Default: true"
    )
    billable: bool = Field(
        True,
        description="Whether project is billable. Default: true"
    )
    color: Optional[str] = Field(
        None,
        pattern="^#[0-9a-fA-F]{6}$",
        description="Hex color code. Example: '#008000'"
    )


class UpdateProjectInput(BaseModel):
    """Input for updating a project."""
    model_config = ConfigDict(extra='forbid')

    id: int = Field(
        ...,
        gt=0,
        description="Project ID to update. Example: 1"
    )
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=150,
        description="Updated project name"
    )
    visible: Optional[bool] = Field(
        None,
        description="Updated visibility status"
    )
    billable: Optional[bool] = Field(
        None,
        description="Updated billable status"
    )
    color: Optional[str] = Field(
        None,
        pattern="^#[0-9a-fA-F]{6}$",
        description="Updated hex color code"
    )


class ListActivitiesInput(BaseModel):
    """Input for listing activities."""
    model_config = ConfigDict(extra='forbid')

    project: Optional[int] = Field(
        None,
        description="Filter by project ID. Example: 1"
    )
    visible: Optional[bool] = Field(
        None,
        description="Filter by visibility. Example: true"
    )
    term: Optional[str] = Field(
        None,
        max_length=200,
        description="Search term to filter activities by name. Example: 'Code Review' or 'FNNLR' or '7313'"
    )
    page: int = Field(
        1,
        ge=1,
        description="Page number (1-based). Example: 1"
    )
    size: int = Field(
        DEFAULT_PAGE_SIZE,
        ge=1,
        le=MAX_PAGE_SIZE,
        description=f"Results per page (max {MAX_PAGE_SIZE}). Example: 50"
    )
    format: str = Field(
        "json",
        pattern="^(json|markdown)$",
        description="Response format: 'json' or 'markdown'"
    )


class GetActivityInput(BaseModel):
    """Input for getting a specific activity."""
    model_config = ConfigDict(extra='forbid')

    id: int = Field(
        ...,
        gt=0,
        description="Activity ID. Example: 355"
    )
    format: str = Field(
        "json",
        pattern="^(json|markdown)$",
        description="Response format: 'json' or 'markdown'"
    )


class CreateActivityInput(BaseModel):
    """Input for creating a new activity."""
    model_config = ConfigDict(extra='forbid')

    name: str = Field(
        ...,
        min_length=1,
        max_length=150,
        description="Activity name. Example: 'Code Review'"
    )
    project: Optional[int] = Field(
        None,
        gt=0,
        description="Project ID (omit for global activity). Example: 1"
    )
    visible: bool = Field(
        True,
        description="Whether activity is visible. Default: true"
    )
    billable: bool = Field(
        True,
        description="Whether activity is billable. Default: true"
    )
    color: Optional[str] = Field(
        None,
        pattern="^#[0-9a-fA-F]{6}$",
        description="Hex color code. Example: '#FF5733'"
    )


class UpdateActivityInput(BaseModel):
    """Input for updating an activity."""
    model_config = ConfigDict(extra='forbid')

    id: int = Field(
        ...,
        gt=0,
        description="Activity ID to update. Example: 355"
    )
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=150,
        description="Updated activity name"
    )
    visible: Optional[bool] = Field(
        None,
        description="Updated visibility status"
    )
    billable: Optional[bool] = Field(
        None,
        description="Updated billable status"
    )
    color: Optional[str] = Field(
        None,
        pattern="^#[0-9a-fA-F]{6}$",
        description="Updated hex color code"
    )


class ListCustomersInput(BaseModel):
    """Input for listing customers."""
    model_config = ConfigDict(extra='forbid')

    visible: Optional[bool] = Field(
        None,
        description="Filter by visibility. Example: true"
    )
    page: int = Field(
        1,
        ge=1,
        description="Page number (1-based). Example: 1"
    )
    size: int = Field(
        DEFAULT_PAGE_SIZE,
        ge=1,
        le=MAX_PAGE_SIZE,
        description=f"Results per page (max {MAX_PAGE_SIZE}). Example: 50"
    )
    format: str = Field(
        "json",
        pattern="^(json|markdown)$",
        description="Response format: 'json' or 'markdown'"
    )


class GetCustomerInput(BaseModel):
    """Input for getting a specific customer."""
    model_config = ConfigDict(extra='forbid')

    id: int = Field(
        ...,
        gt=0,
        description="Customer ID. Example: 1"
    )
    format: str = Field(
        "json",
        pattern="^(json|markdown)$",
        description="Response format: 'json' or 'markdown'"
    )


class CreateCustomerInput(BaseModel):
    """Input for creating a new customer."""
    model_config = ConfigDict(extra='forbid')

    name: str = Field(
        ...,
        min_length=1,
        max_length=150,
        description="Customer name. Example: 'Acme Corporation'"
    )
    currency: str = Field(
        "USD",
        min_length=3,
        max_length=3,
        description="3-letter currency code. Example: 'USD', 'EUR', 'CAD'"
    )
    visible: bool = Field(
        True,
        description="Whether customer is visible. Default: true"
    )
    billable: bool = Field(
        True,
        description="Whether customer is billable. Default: true"
    )
    color: Optional[str] = Field(
        None,
        pattern="^#[0-9a-fA-F]{6}$",
        description="Hex color code. Example: '#008000'"
    )


class UpdateCustomerInput(BaseModel):
    """Input for updating a customer."""
    model_config = ConfigDict(extra='forbid')

    id: int = Field(
        ...,
        gt=0,
        description="Customer ID to update. Example: 1"
    )
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=150,
        description="Updated customer name"
    )
    currency: Optional[str] = Field(
        None,
        min_length=3,
        max_length=3,
        description="Updated currency code"
    )
    visible: Optional[bool] = Field(
        None,
        description="Updated visibility status"
    )
    billable: Optional[bool] = Field(
        None,
        description="Updated billable status"
    )
    color: Optional[str] = Field(
        None,
        pattern="^#[0-9a-fA-F]{6}$",
        description="Updated hex color code"
    )


class GetTimesheetSummaryInput(BaseModel):
    """Input for getting timesheet summary/report."""
    model_config = ConfigDict(extra='forbid')

    user: Optional[int] = Field(
        None,
        description="Filter by user ID. Example: 1"
    )
    customer: Optional[int] = Field(
        None,
        description="Filter by customer ID. Example: 1"
    )
    project: Optional[int] = Field(
        None,
        description="Filter by project ID. Example: 1"
    )
    activity: Optional[int] = Field(
        None,
        description="Filter by activity ID. Example: 355"
    )
    begin: Optional[str] = Field(
        None,
        description="Start date for report (ISO 8601). Example: 2025-11-01T00:00:00"
    )
    end: Optional[str] = Field(
        None,
        description="End date for report (ISO 8601). Example: 2025-11-30T23:59:59"
    )
    format: str = Field(
        "markdown",
        pattern="^(json|markdown)$",
        description="Response format: 'json' or 'markdown'"
    )


# ============================================================================
# API Client
# ============================================================================

class KimaiClient:
    """HTTP client for KIMAI API."""

    def __init__(self, config: KimaiConfig):
        self.base_url = config.base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {config.api_token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        json_data: Optional[dict] = None
    ) -> Any:
        """
        Make an HTTP request to the KIMAI API.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            endpoint: API endpoint path
            params: Query parameters
            json_data: JSON body for POST/PATCH

        Returns:
            Response data (dict or list)

        Raises:
            Exception: On API errors with descriptive message
        """
        url = urljoin(self.base_url, f"/api/{endpoint}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    params=params,
                    json=json_data
                )

                response.raise_for_status()

                # Handle empty responses (e.g., DELETE)
                if response.status_code == 204 or not response.content:
                    return {"success": True}

                return response.json()

            except httpx.HTTPStatusError as e:
                error_detail = ""
                try:
                    error_data = e.response.json()
                    error_detail = error_data.get("message", str(error_data))
                except Exception:
                    error_detail = e.response.text

                raise Exception(
                    f"KIMAI API error ({e.response.status_code}): {error_detail}. "
                    f"Please check your request parameters and try again."
                ) from e

            except httpx.RequestError as e:
                raise Exception(
                    f"Network error connecting to KIMAI: {str(e)}. "
                    f"Please verify the KIMAI instance URL ({self.base_url}) is correct and accessible."
                ) from e


# ============================================================================
# Response Formatting Utilities
# ============================================================================

def truncate_if_needed(text: str, limit: int = CHARACTER_LIMIT) -> str:
    """Truncate text if it exceeds character limit."""
    if len(text) <= limit:
        return text

    truncated = text[:limit - 50]
    return f"{truncated}\n\n... [Output truncated at {limit} characters]"


def format_timesheet_markdown(timesheet: dict) -> str:
    """Format a single timesheet as markdown."""
    duration_hours = timesheet.get("duration", 0) / 3600
    status = "⏱️ RUNNING" if timesheet.get("end") is None else "✓ Completed"

    lines = [
        f"## Timesheet #{timesheet.get('id')}",
        f"**Status:** {status}",
        f"**Project ID:** {timesheet.get('project')}",
        f"**Activity ID:** {timesheet.get('activity')}",
        f"**Start:** {timesheet.get('begin')}",
        f"**End:** {timesheet.get('end', 'Still running...')}",
        f"**Duration:** {duration_hours:.2f} hours ({timesheet.get('duration', 0)} seconds)",
        f"**Billable:** {'Yes' if timesheet.get('billable') else 'No'}",
        f"**Exported:** {'Yes' if timesheet.get('exported') else 'No'}",
    ]

    if timesheet.get("description"):
        lines.append(f"**Description:** {timesheet.get('description')}")

    if timesheet.get("tags"):
        lines.append(f"**Tags:** {', '.join(timesheet.get('tags', []))}")

    if timesheet.get("rate"):
        lines.append(f"**Rate:** {timesheet.get('rate')}")

    return "\n".join(lines)


def format_timesheets_markdown(timesheets: list) -> str:
    """Format multiple timesheets as markdown."""
    if not timesheets:
        return "No timesheets found."

    total_duration = sum(t.get("duration", 0) for t in timesheets)
    total_hours = total_duration / 3600

    lines = [
        f"# Timesheets ({len(timesheets)} entries)",
        f"**Total Duration:** {total_hours:.2f} hours",
        "",
    ]

    for ts in timesheets:
        lines.append(format_timesheet_markdown(ts))
        lines.append("")

    return truncate_if_needed("\n".join(lines))


def format_project_markdown(project: dict) -> str:
    """Format a single project as markdown."""
    lines = [
        f"## {project.get('name')} (#{project.get('id')})",
        f"**Number:** {project.get('number')}",
        f"**Customer ID:** {project.get('customer')}",
        f"**Visible:** {'Yes' if project.get('visible') else 'No'}",
        f"**Billable:** {'Yes' if project.get('billable') else 'No'}",
    ]

    if project.get("color"):
        lines.append(f"**Color:** {project.get('color')}")

    if project.get("comment"):
        lines.append(f"**Comment:** {project.get('comment')}")

    return "\n".join(lines)


def format_projects_markdown(projects: list) -> str:
    """Format multiple projects as markdown."""
    if not projects:
        return "No projects found."

    lines = [
        f"# Projects ({len(projects)} total)",
        "",
    ]

    for proj in projects:
        lines.append(format_project_markdown(proj))
        lines.append("")

    return truncate_if_needed("\n".join(lines))


def format_activity_markdown(activity: dict) -> str:
    """Format a single activity as markdown."""
    lines = [
        f"## {activity.get('name')} (#{activity.get('id')})",
        f"**Number:** {activity.get('number')}",
        f"**Project ID:** {activity.get('project', 'Global')}",
        f"**Visible:** {'Yes' if activity.get('visible') else 'No'}",
        f"**Billable:** {'Yes' if activity.get('billable') else 'No'}",
    ]

    if activity.get("color"):
        lines.append(f"**Color:** {activity.get('color')}")

    if activity.get("comment"):
        lines.append(f"**Comment:** {activity.get('comment')}")

    return "\n".join(lines)


def format_activities_markdown(activities: list) -> str:
    """Format multiple activities as markdown."""
    if not activities:
        return "No activities found."

    lines = [
        f"# Activities ({len(activities)} total)",
        "",
    ]

    for act in activities:
        lines.append(format_activity_markdown(act))
        lines.append("")

    return truncate_if_needed("\n".join(lines))


def format_customer_markdown(customer: dict) -> str:
    """Format a single customer as markdown."""
    lines = [
        f"## {customer.get('name')} (#{customer.get('id')})",
        f"**Number:** {customer.get('number')}",
        f"**Currency:** {customer.get('currency')}",
        f"**Visible:** {'Yes' if customer.get('visible') else 'No'}",
        f"**Billable:** {'Yes' if customer.get('billable') else 'No'}",
    ]

    if customer.get("color"):
        lines.append(f"**Color:** {customer.get('color')}")

    if customer.get("comment"):
        lines.append(f"**Comment:** {customer.get('comment')}")

    return "\n".join(lines)


def format_customers_markdown(customers: list) -> str:
    """Format multiple customers as markdown."""
    if not customers:
        return "No customers found."

    lines = [
        f"# Customers ({len(customers)} total)",
        "",
    ]

    for cust in customers:
        lines.append(format_customer_markdown(cust))
        lines.append("")

    return truncate_if_needed("\n".join(lines))


# ============================================================================
# MCP Server Setup
# ============================================================================

# Initialize MCP server
app = Server("kimai-mcp")

# Global client instance (will be initialized from environment)
kimai_client: Optional[KimaiClient] = None


def get_client() -> KimaiClient:
    """Get the KIMAI client instance."""
    global kimai_client
    if kimai_client is None:
        config = KimaiConfig(
            base_url=os.environ.get("KIMAI_BASE_URL", "http://localhost:8001"),
            api_token=os.environ.get("KIMAI_API_TOKEN", "")
        )
        kimai_client = KimaiClient(config)
    return kimai_client


# ============================================================================
# Tool Implementations
# ============================================================================

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools."""
    return [
        Tool(
            name="list_timesheets",
            description="""
List timesheet entries with optional filtering.

Use this tool to:
- View recent time tracking entries
- Find timesheets by project, activity, customer, or user
- Check currently running timesheets (active=true)
- Filter by date range
- Find exported/unexported entries

Returns a list of timesheet records with duration, project/activity info, and metadata.
Supports pagination for large result sets.
""",
            inputSchema=ListTimesheetsInput.model_json_schema()
        ),
        Tool(
            name="get_timesheet",
            description="""
Get detailed information about a specific timesheet entry.

Use this tool when you know the timesheet ID and need complete details
about a specific time entry including all metadata, rates, and tags.
""",
            inputSchema=GetTimesheetInput.model_json_schema()
        ),
        Tool(
            name="start_timesheet",
            description="""
Start tracking time for a project and activity.

Use this tool to begin a new time entry. This creates a running timesheet
with the current timestamp as the start time. The entry remains active
until stopped with stop_timesheet.

Returns the created timesheet with ID for later reference.
""",
            inputSchema=StartTimesheetInput.model_json_schema()
        ),
        Tool(
            name="stop_timesheet",
            description="""
Stop a currently running timesheet entry.

Use this tool to end time tracking for an active entry. Sets the end time
to the current timestamp and calculates the total duration.

The timesheet must be currently running (no end time) to use this tool.
""",
            inputSchema=StopTimesheetInput.model_json_schema()
        ),
        Tool(
            name="create_timesheet",
            description="""
Create a complete timesheet entry with specific start and end times.

Use this tool to:
- Record past work that wasn't tracked in real-time
- Create time entries with custom start/end times
- Batch import historical time data

Unlike start_timesheet, this creates a completed entry with both begin
and end timestamps, or you can omit end to create a running entry.
""",
            inputSchema=CreateTimesheetInput.model_json_schema()
        ),
        Tool(
            name="update_timesheet",
            description="""
Update an existing timesheet entry.

Use this tool to:
- Correct time entry errors (wrong start/end time)
- Add or modify descriptions
- Update tags
- Adjust billable status

Only provide the fields you want to change; others remain unchanged.
""",
            inputSchema=UpdateTimesheetInput.model_json_schema()
        ),
        Tool(
            name="delete_timesheet",
            description="""
Delete a timesheet entry permanently.

Use this tool to remove incorrect or duplicate time entries.
This action cannot be undone.

Ensure you have the correct timesheet ID before deletion.
""",
            inputSchema=DeleteTimesheetInput.model_json_schema()
        ),
        Tool(
            name="list_projects",
            description="""
List all projects with optional filtering.

Use this tool to:
- Browse available projects for time tracking
- Find projects by customer
- Discover project IDs needed for timesheet operations
- Check project visibility and billable status

Returns project details including name, customer, color, and metadata.
""",
            inputSchema=ListProjectsInput.model_json_schema()
        ),
        Tool(
            name="get_project",
            description="""
Get detailed information about a specific project.

Use this tool when you need complete details about a project including
all metadata, configuration, and relationships.
""",
            inputSchema=GetProjectInput.model_json_schema()
        ),
        Tool(
            name="create_project",
            description="""
Create a new project under a customer.

Use this tool to:
- Set up new projects for time tracking
- Organize work by customer and project
- Configure billable/non-billable projects

Requires a valid customer ID. The project becomes available immediately
for timesheet entries.
""",
            inputSchema=CreateProjectInput.model_json_schema()
        ),
        Tool(
            name="update_project",
            description="""
Update an existing project's details.

Use this tool to:
- Rename projects
- Change visibility or billable status
- Update project color coding

Only provide fields you want to change.
""",
            inputSchema=UpdateProjectInput.model_json_schema()
        ),
        Tool(
            name="list_activities",
            description="""
List all activities with optional filtering.

Use this tool to:
- Browse available activities for time tracking
- Find activities by project
- Discover activity IDs needed for timesheet operations
- Check global vs project-specific activities

Returns activity details including name, project association, and metadata.
""",
            inputSchema=ListActivitiesInput.model_json_schema()
        ),
        Tool(
            name="get_activity",
            description="""
Get detailed information about a specific activity.

Use this tool when you need complete details about an activity including
all metadata and configuration.
""",
            inputSchema=GetActivityInput.model_json_schema()
        ),
        Tool(
            name="create_activity",
            description="""
Create a new activity.

Use this tool to:
- Define new types of work for time tracking
- Create project-specific or global activities
- Set up activity categories

Activities can be associated with a specific project or made global
(available for all projects) by omitting the project ID.
""",
            inputSchema=CreateActivityInput.model_json_schema()
        ),
        Tool(
            name="update_activity",
            description="""
Update an existing activity's details.

Use this tool to:
- Rename activities
- Change visibility or billable status
- Update activity color coding

Only provide fields you want to change.
""",
            inputSchema=UpdateActivityInput.model_json_schema()
        ),
        Tool(
            name="list_customers",
            description="""
List all customers with optional filtering.

Use this tool to:
- Browse available customers
- Find customer IDs for project creation
- Check customer configuration and billing info

Returns customer details including name, currency, and metadata.
""",
            inputSchema=ListCustomersInput.model_json_schema()
        ),
        Tool(
            name="get_customer",
            description="""
Get detailed information about a specific customer.

Use this tool when you need complete details about a customer including
all metadata and configuration.
""",
            inputSchema=GetCustomerInput.model_json_schema()
        ),
        Tool(
            name="create_customer",
            description="""
Create a new customer.

Use this tool to:
- Add new clients to the system
- Set up customer billing configuration
- Define currency preferences

The customer becomes immediately available for project creation.
""",
            inputSchema=CreateCustomerInput.model_json_schema()
        ),
        Tool(
            name="update_customer",
            description="""
Update an existing customer's details.

Use this tool to:
- Update customer information
- Change billing currency
- Modify visibility or billable status

Only provide fields you want to change.
""",
            inputSchema=UpdateCustomerInput.model_json_schema()
        ),
        Tool(
            name="get_timesheet_summary",
            description="""
Generate a summary report of timesheet data.

Use this tool to:
- Analyze time spent across projects and activities
- Calculate total hours for billing
- Review time tracking by customer or user
- Generate period reports (daily, weekly, monthly)

Aggregates timesheet data and provides statistics on duration,
billable vs non-billable time, and distribution across projects/activities.
""",
            inputSchema=GetTimesheetSummaryInput.model_json_schema()
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    client = get_client()

    try:
        # Timesheet Tools
        if name == "list_timesheets":
            params = ListTimesheetsInput(**arguments)
            query_params = {
                "page": params.page,
                "size": params.size,
            }
            if params.user is not None:
                query_params["user"] = params.user
            if params.customer is not None:
                query_params["customer"] = params.customer
            if params.project is not None:
                query_params["project"] = params.project
            if params.activity is not None:
                query_params["activity"] = params.activity
            if params.active is not None:
                query_params["active"] = "1" if params.active else "0"
            if params.exported is not None:
                query_params["exported"] = "1" if params.exported else "0"
            if params.begin:
                query_params["begin"] = params.begin
            if params.end:
                query_params["end"] = params.end

            result = await client.request("GET", "timesheets", params=query_params)

            if params.format == "markdown":
                return [TextContent(type="text", text=format_timesheets_markdown(result))]
            return [TextContent(type="text", text=truncate_if_needed(str(result)))]

        elif name == "get_timesheet":
            params = GetTimesheetInput(**arguments)
            result = await client.request("GET", f"timesheets/{params.id}")

            if params.format == "markdown":
                return [TextContent(type="text", text=format_timesheet_markdown(result))]
            return [TextContent(type="text", text=str(result))]

        elif name == "start_timesheet":
            params = StartTimesheetInput(**arguments)
            data = {
                "project": params.project,
                "activity": params.activity,
                "begin": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            if params.description:
                data["description"] = params.description
            if params.tags:
                data["tags"] = params.tags

            result = await client.request("POST", "timesheets", json_data=data)
            return [TextContent(
                type="text",
                text=f"✓ Timesheet started successfully!\n\n{format_timesheet_markdown(result)}"
            )]

        elif name == "stop_timesheet":
            params = StopTimesheetInput(**arguments)
            # First get the current timesheet to validate it's running
            current = await client.request("GET", f"timesheets/{params.id}")
            if current.get("end") is not None:
                return [TextContent(
                    type="text",
                    text=f"❌ Error: Timesheet #{params.id} is not running (already has an end time)."
                )]

            # Stop the timesheet
            data = {
                "end": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            }
            result = await client.request("PATCH", f"timesheets/{params.id}", json_data=data)
            return [TextContent(
                type="text",
                text=f"✓ Timesheet stopped successfully!\n\n{format_timesheet_markdown(result)}"
            )]

        elif name == "create_timesheet":
            params = CreateTimesheetInput(**arguments)
            data = {
                "project": params.project,
                "activity": params.activity,
                "begin": params.begin,
            }
            if params.end:
                data["end"] = params.end
            if params.description:
                data["description"] = params.description
            if params.tags:
                data["tags"] = params.tags

            result = await client.request("POST", "timesheets", json_data=data)
            return [TextContent(
                type="text",
                text=f"✓ Timesheet created successfully!\n\n{format_timesheet_markdown(result)}"
            )]

        elif name == "update_timesheet":
            params = UpdateTimesheetInput(**arguments)
            data = {}
            if params.begin:
                data["begin"] = params.begin
            if params.end:
                data["end"] = params.end
            if params.description is not None:
                data["description"] = params.description
            if params.tags is not None:
                data["tags"] = params.tags

            result = await client.request("PATCH", f"timesheets/{params.id}", json_data=data)
            return [TextContent(
                type="text",
                text=f"✓ Timesheet updated successfully!\n\n{format_timesheet_markdown(result)}"
            )]

        elif name == "delete_timesheet":
            params = DeleteTimesheetInput(**arguments)
            await client.request("DELETE", f"timesheets/{params.id}")
            return [TextContent(
                type="text",
                text=f"✓ Timesheet #{params.id} deleted successfully."
            )]

        # Project Tools
        elif name == "list_projects":
            params = ListProjectsInput(**arguments)
            query_params = {
                "page": params.page,
                "size": params.size,
            }
            if params.customer is not None:
                query_params["customer"] = params.customer
            if params.visible is not None:
                query_params["visible"] = "1" if params.visible else "0"

            result = await client.request("GET", "projects", params=query_params)

            if params.format == "markdown":
                return [TextContent(type="text", text=format_projects_markdown(result))]
            return [TextContent(type="text", text=truncate_if_needed(str(result)))]

        elif name == "get_project":
            params = GetProjectInput(**arguments)
            result = await client.request("GET", f"projects/{params.id}")

            if params.format == "markdown":
                return [TextContent(type="text", text=format_project_markdown(result))]
            return [TextContent(type="text", text=str(result))]

        elif name == "create_project":
            params = CreateProjectInput(**arguments)
            data = {
                "name": params.name,
                "customer": params.customer,
                "visible": params.visible,
                "billable": params.billable,
            }
            if params.color:
                data["color"] = params.color

            result = await client.request("POST", "projects", json_data=data)
            return [TextContent(
                type="text",
                text=f"✓ Project created successfully!\n\n{format_project_markdown(result)}"
            )]

        elif name == "update_project":
            params = UpdateProjectInput(**arguments)
            data = {}
            if params.name:
                data["name"] = params.name
            if params.visible is not None:
                data["visible"] = params.visible
            if params.billable is not None:
                data["billable"] = params.billable
            if params.color:
                data["color"] = params.color

            result = await client.request("PATCH", f"projects/{params.id}", json_data=data)
            return [TextContent(
                type="text",
                text=f"✓ Project updated successfully!\n\n{format_project_markdown(result)}"
            )]

        # Activity Tools
        elif name == "list_activities":
            params = ListActivitiesInput(**arguments)
            query_params = {
                "page": params.page,
                "size": params.size,
            }
            if params.project is not None:
                query_params["project"] = params.project
            if params.visible is not None:
                query_params["visible"] = "1" if params.visible else "0"
            if params.term:
                query_params["term"] = params.term

            result = await client.request("GET", "activities", params=query_params)

            if params.format == "markdown":
                return [TextContent(type="text", text=format_activities_markdown(result))]
            return [TextContent(type="text", text=truncate_if_needed(str(result)))]

        elif name == "get_activity":
            params = GetActivityInput(**arguments)
            result = await client.request("GET", f"activities/{params.id}")

            if params.format == "markdown":
                return [TextContent(type="text", text=format_activity_markdown(result))]
            return [TextContent(type="text", text=str(result))]

        elif name == "create_activity":
            params = CreateActivityInput(**arguments)
            data = {
                "name": params.name,
                "visible": params.visible,
                "billable": params.billable,
            }
            if params.project is not None:
                data["project"] = params.project
            if params.color:
                data["color"] = params.color

            result = await client.request("POST", "activities", json_data=data)
            return [TextContent(
                type="text",
                text=f"✓ Activity created successfully!\n\n{format_activity_markdown(result)}"
            )]

        elif name == "update_activity":
            params = UpdateActivityInput(**arguments)
            data = {}
            if params.name:
                data["name"] = params.name
            if params.visible is not None:
                data["visible"] = params.visible
            if params.billable is not None:
                data["billable"] = params.billable
            if params.color:
                data["color"] = params.color

            result = await client.request("PATCH", f"activities/{params.id}", json_data=data)
            return [TextContent(
                type="text",
                text=f"✓ Activity updated successfully!\n\n{format_activity_markdown(result)}"
            )]

        # Customer Tools
        elif name == "list_customers":
            params = ListCustomersInput(**arguments)
            query_params = {
                "page": params.page,
                "size": params.size,
            }
            if params.visible is not None:
                query_params["visible"] = "1" if params.visible else "0"

            result = await client.request("GET", "customers", params=query_params)

            if params.format == "markdown":
                return [TextContent(type="text", text=format_customers_markdown(result))]
            return [TextContent(type="text", text=truncate_if_needed(str(result)))]

        elif name == "get_customer":
            params = GetCustomerInput(**arguments)
            result = await client.request("GET", f"customers/{params.id}")

            if params.format == "markdown":
                return [TextContent(type="text", text=format_customer_markdown(result))]
            return [TextContent(type="text", text=str(result))]

        elif name == "create_customer":
            params = CreateCustomerInput(**arguments)
            data = {
                "name": params.name,
                "currency": params.currency,
                "visible": params.visible,
                "billable": params.billable,
            }
            if params.color:
                data["color"] = params.color

            result = await client.request("POST", "customers", json_data=data)
            return [TextContent(
                type="text",
                text=f"✓ Customer created successfully!\n\n{format_customer_markdown(result)}"
            )]

        elif name == "update_customer":
            params = UpdateCustomerInput(**arguments)
            data = {}
            if params.name:
                data["name"] = params.name
            if params.currency:
                data["currency"] = params.currency
            if params.visible is not None:
                data["visible"] = params.visible
            if params.billable is not None:
                data["billable"] = params.billable
            if params.color:
                data["color"] = params.color

            result = await client.request("PATCH", f"customers/{params.id}", json_data=data)
            return [TextContent(
                type="text",
                text=f"✓ Customer updated successfully!\n\n{format_customer_markdown(result)}"
            )]

        # Reporting Tool
        elif name == "get_timesheet_summary":
            params = GetTimesheetSummaryInput(**arguments)
            query_params = {"size": 1000}  # Get more entries for aggregation

            if params.user is not None:
                query_params["user"] = params.user
            if params.customer is not None:
                query_params["customer"] = params.customer
            if params.project is not None:
                query_params["project"] = params.project
            if params.activity is not None:
                query_params["activity"] = params.activity
            if params.begin:
                query_params["begin"] = params.begin
            if params.end:
                query_params["end"] = params.end

            timesheets = await client.request("GET", "timesheets", params=query_params)

            # Calculate summary statistics
            total_duration = sum(t.get("duration", 0) for t in timesheets)
            total_hours = total_duration / 3600
            billable_duration = sum(t.get("duration", 0) for t in timesheets if t.get("billable"))
            billable_hours = billable_duration / 3600
            non_billable_hours = total_hours - billable_hours

            # Group by project
            by_project = {}
            for ts in timesheets:
                proj_id = ts.get("project")
                if proj_id not in by_project:
                    by_project[proj_id] = {"duration": 0, "count": 0}
                by_project[proj_id]["duration"] += ts.get("duration", 0)
                by_project[proj_id]["count"] += 1

            # Group by activity
            by_activity = {}
            for ts in timesheets:
                act_id = ts.get("activity")
                if act_id not in by_activity:
                    by_activity[act_id] = {"duration": 0, "count": 0}
                by_activity[act_id]["duration"] += ts.get("duration", 0)
                by_activity[act_id]["count"] += 1

            if params.format == "markdown":
                lines = [
                    "# Timesheet Summary Report",
                    "",
                    "## Overview",
                    f"**Total Entries:** {len(timesheets)}",
                    f"**Total Time:** {total_hours:.2f} hours",
                    f"**Billable Time:** {billable_hours:.2f} hours ({(billable_hours/total_hours*100) if total_hours > 0 else 0:.1f}%)",
                    f"**Non-Billable Time:** {non_billable_hours:.2f} hours ({(non_billable_hours/total_hours*100) if total_hours > 0 else 0:.1f}%)",
                    "",
                    "## By Project",
                ]

                for proj_id, data in sorted(by_project.items(), key=lambda x: x[1]["duration"], reverse=True):
                    hours = data["duration"] / 3600
                    lines.append(f"- Project #{proj_id}: {hours:.2f} hours ({data['count']} entries)")

                lines.append("")
                lines.append("## By Activity")

                for act_id, data in sorted(by_activity.items(), key=lambda x: x[1]["duration"], reverse=True):
                    hours = data["duration"] / 3600
                    lines.append(f"- Activity #{act_id}: {hours:.2f} hours ({data['count']} entries)")

                return [TextContent(type="text", text="\n".join(lines))]

            # JSON format
            summary = {
                "total_entries": len(timesheets),
                "total_hours": round(total_hours, 2),
                "billable_hours": round(billable_hours, 2),
                "non_billable_hours": round(non_billable_hours, 2),
                "by_project": {
                    str(k): {"hours": round(v["duration"] / 3600, 2), "count": v["count"]}
                    for k, v in by_project.items()
                },
                "by_activity": {
                    str(k): {"hours": round(v["duration"] / 3600, 2), "count": v["count"]}
                    for k, v in by_activity.items()
                },
            }
            return [TextContent(type="text", text=str(summary))]

        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]


# ============================================================================
# Main Entry Point
# ============================================================================

async def main():
    """Run the MCP server."""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
