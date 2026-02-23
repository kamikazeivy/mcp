#!/usr/bin/env python
"""
Demo script showing local file system crawler usage (NO AWS COSTS).

This demonstrates how to use the Sentinel Agent MCP Server
without any AWS account or costs.
"""

import asyncio
import json
from awslabs.sentinel_agent_mcp_server.server import (
    create_sentinel_agent,
    create_crawler_agent,
    run_crawler_agent,
    get_sentinel_reports,
    list_agents,
)


async def main():
    """Run a demo of the local file system crawler."""
    print('=' * 70)
    print('Sentinel Agent MCP Server - Local File System Crawler Demo')
    print('NO AWS COSTS - Completely Free!')
    print('=' * 70)
    print()

    # Step 1: Create a sentinel agent
    print('Step 1: Creating a sentinel agent...')
    sentinel_result = await create_sentinel_agent(
        name='LocalFileDiscoverySentinel', max_buffer_size=500
    )
    sentinel_data = json.loads(sentinel_result)
    sentinel_id = sentinel_data['sentinel']['agent_id']
    print(f'✓ Created sentinel: {sentinel_id}')
    print(f'  Name: {sentinel_data["sentinel"]["name"]}')
    print()

    # Step 2: Create a local file crawler for Python files
    print('Step 2: Creating a local file system crawler...')
    crawler_result = await create_crawler_agent(
        name='PythonFilesCrawler',
        sentinel_id=sentinel_id,
        resource_type='file',
        crawler_type='local',  # FREE - no AWS needed!
        base_path='.',
        include_patterns=['.py'],
        exclude_patterns=['__pycache__', '.venv', 'test_'],
        max_depth=2,
    )
    crawler_data = json.loads(crawler_result)
    if not crawler_data['success']:
        print(f'✗ Error creating crawler: {crawler_data.get("error")}')
        return

    crawler_id = crawler_data['crawler']['agent_id']
    print(f'✓ Created local crawler: {crawler_id}')
    print(f'  Name: {crawler_data["crawler"]["name"]}')
    print(f'  Type: {crawler_data["crawler"]["crawler_type"]} (FREE!)')
    print(f'  Resource: {crawler_data["crawler"]["resource_type"]}')
    print()

    # Step 3: Run the crawler
    print('Step 3: Running the crawler to discover local files...')
    run_result = await run_crawler_agent(crawler_id=crawler_id)
    run_data = json.loads(run_result)
    print(f'✓ Crawler completed')
    print(f'  Items discovered: {run_data.get("items_discovered", 0)}')
    print(f'  Reports sent: {run_data.get("reports_sent", 0)}')
    print()

    # Step 4: Get reports from sentinel
    print('Step 4: Retrieving reports from sentinel...')
    reports_result = await get_sentinel_reports(sentinel_id=sentinel_id, limit=10)
    reports_data = json.loads(reports_result)
    reports = reports_data.get('reports', [])

    print(f'✓ Retrieved {len(reports)} reports')
    print('\nSample discovered files:')
    for i, report in enumerate(reports[:5], 1):
        data = report['data']
        if 'error' not in data:
            print(f"  {i}. {data.get('name', 'unknown')}")
            print(f"     Path: {data.get('path', 'unknown')}")
            print(f"     Size: {data.get('size_bytes', 0)} bytes")
            print(
                f"     Modified: {data.get('modified_time', 'unknown')}"
            )
    print()

    # Step 5: List all agents
    print('Step 5: Listing all agents...')
    list_result = await list_agents()
    list_data = json.loads(list_result)

    sentinels = list_data.get('sentinels', [])
    crawlers = list_data.get('crawlers', [])

    print(f'✓ Total sentinels: {len(sentinels)}')
    print(f'✓ Total crawlers: {len(crawlers)}')
    for crawler in crawlers:
        print(f'  - {crawler["name"]} ({crawler["crawler_type"]})')
    print()

    print('=' * 70)
    print('Demo completed successfully!')
    print('All operations performed locally - NO AWS COSTS!')
    print('=' * 70)


if __name__ == '__main__':
    asyncio.run(main())
