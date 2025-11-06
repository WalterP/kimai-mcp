#!/usr/bin/env python3
"""
Test KIMAI API Connection

Quick test script to verify KIMAI instance connectivity and API token validity.
"""

import asyncio
import os
import sys
from server import KimaiConfig, KimaiClient


async def test_connection():
    """Test connection to KIMAI instance."""
    print("🔍 Testing KIMAI API Connection...\n")

    # Get configuration
    base_url = os.environ.get("KIMAI_BASE_URL")
    api_token = os.environ.get("KIMAI_API_TOKEN")

    if not base_url or not api_token:
        print("❌ Error: Missing environment variables")
        print("   Please set KIMAI_BASE_URL and KIMAI_API_TOKEN")
        print("\n   Example:")
        print("   export KIMAI_BASE_URL=http://localhost:8001")
        print("   export KIMAI_API_TOKEN=your_token_here")
        return False

    print(f"📍 KIMAI URL: {base_url}")
    print(f"🔑 API Token: {api_token[:8]}...{api_token[-4:]}\n")

    try:
        # Create client
        config = KimaiConfig(base_url=base_url, api_token=api_token)
        client = KimaiClient(config)

        # Test version endpoint
        print("1️⃣  Testing version endpoint...")
        version = await client.request("GET", "version")
        print(f"   ✓ Connected to KIMAI {version.get('version')}")

        # Test timesheets endpoint
        print("\n2️⃣  Testing timesheets endpoint...")
        timesheets = await client.request("GET", "timesheets", params={"size": 5})
        print(f"   ✓ Found {len(timesheets)} recent timesheets")

        # Test projects endpoint
        print("\n3️⃣  Testing projects endpoint...")
        projects = await client.request("GET", "projects", params={"size": 5})
        print(f"   ✓ Found {len(projects)} projects")

        # Test activities endpoint
        print("\n4️⃣  Testing activities endpoint...")
        activities = await client.request("GET", "activities", params={"size": 5})
        print(f"   ✓ Found {len(activities)} activities")

        # Test customers endpoint
        print("\n5️⃣  Testing customers endpoint...")
        customers = await client.request("GET", "customers", params={"size": 5})
        print(f"   ✓ Found {len(customers)} customers")

        print("\n✅ All tests passed! KIMAI MCP server is ready to use.")
        return True

    except Exception as e:
        print(f"\n❌ Connection test failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)
