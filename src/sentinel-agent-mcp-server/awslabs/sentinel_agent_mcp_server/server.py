# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Sentinel Agent MCP Server - Scoped crawler agents with sentinel reporting."""

import json
from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional
from fastmcp import FastMCP
from pydantic import Field
from awslabs.sentinel_agent_mcp_server.models import (
    AgentStatus,
    CrawlerAgent,
    CrawlerScope,
    DataReport,
    SentinelAgent,
)
from awslabs.sentinel_agent_mcp_server.agents.base import BaseSentinelAgent
from awslabs.sentinel_agent_mcp_server.agents.glue_crawler import GlueCrawlerAgent


# Initialize MCP server
mcp = FastMCP(
    'Sentinel Agent MCP Server - Manage scoped crawler agents that report to sentinel agents'
)

# In-memory storage for agents
sentinels: Dict[str, BaseSentinelAgent] = {}
crawlers: Dict[str, GlueCrawlerAgent] = {}


@mcp.tool(name='create_sentinel_agent')
async def create_sentinel_agent(
    name: Annotated[str, Field(description='Human-readable name for the sentinel')],
    agent_id: Annotated[
        Optional[str], Field(description='Unique ID (auto-generated if not provided)')
    ] = None,
    max_buffer_size: Annotated[
        int, Field(description='Maximum number of reports to buffer')
    ] = 1000,
) -> str:
    """Create a new sentinel agent to receive reports from crawlers.

    Sentinel agents act as coordinators that receive and manage data reports
    from assigned scoped crawler agents.

    Args:
        name: Human-readable name for the sentinel
        agent_id: Optional unique ID (auto-generated if not provided)
        max_buffer_size: Maximum number of reports to buffer (default: 1000)

    Returns:
        JSON string with sentinel creation status and details
    """
    if agent_id is None:
        agent_id = f'sentinel-{datetime.utcnow().timestamp()}'

    if agent_id in sentinels:
        return json.dumps({'success': False, 'error': 'Sentinel ID already exists'})

    config = SentinelAgent(
        agent_id=agent_id, name=name, max_buffer_size=max_buffer_size, assigned_crawlers=[]
    )
    sentinel = BaseSentinelAgent(config)
    sentinels[agent_id] = sentinel

    return json.dumps(
        {
            'success': True,
            'sentinel': {
                'agent_id': agent_id,
                'name': name,
                'status': sentinel.status.value,
                'max_buffer_size': max_buffer_size,
                'created_at': config.created_at.isoformat(),
            },
        }
    )


@mcp.tool(name='create_crawler_agent')
async def create_crawler_agent(
    name: Annotated[str, Field(description='Human-readable name for the crawler')],
    sentinel_id: Annotated[str, Field(description='ID of the sentinel to assign to')],
    resource_type: Annotated[
        str,
        Field(
            description='Type of resource to crawl (e.g., glue-crawler, glue-database, glue-table)'
        ),
    ],
    agent_id: Annotated[
        Optional[str], Field(description='Unique ID (auto-generated if not provided)')
    ] = None,
    scope_filters: Annotated[
        Optional[Dict[str, Any]], Field(description='Filters to limit crawler scope')
    ] = None,
    include_patterns: Annotated[
        Optional[List[str]], Field(description='Patterns to include in crawling')
    ] = None,
    exclude_patterns: Annotated[
        Optional[List[str]], Field(description='Patterns to exclude from crawling')
    ] = None,
    max_depth: Annotated[int, Field(description='Maximum depth for hierarchical crawling')] = 1,
    region_name: Annotated[
        Optional[str], Field(description='AWS region name (uses default if not specified)')
    ] = None,
) -> str:
    """Create a new scoped crawler agent assigned to a sentinel.

    Crawler agents discover and report data within their configured scope
    to their assigned sentinel agent.

    Args:
        name: Human-readable name for the crawler
        sentinel_id: ID of the sentinel to assign this crawler to
        resource_type: Type of resource to crawl (glue-crawler, glue-database, glue-table)
        agent_id: Optional unique ID (auto-generated if not provided)
        scope_filters: Optional filters to limit crawler scope
        include_patterns: Optional patterns to include in crawling
        exclude_patterns: Optional patterns to exclude from crawling
        max_depth: Maximum depth for hierarchical crawling (default: 1)
        region_name: Optional AWS region name

    Returns:
        JSON string with crawler creation status and details
    """
    if agent_id is None:
        agent_id = f'crawler-{datetime.utcnow().timestamp()}'

    if agent_id in crawlers:
        return json.dumps({'success': False, 'error': 'Crawler ID already exists'})

    if sentinel_id not in sentinels:
        return json.dumps({'success': False, 'error': 'Sentinel not found'})

    scope = CrawlerScope(
        resource_type=resource_type,
        scope_filters=scope_filters or {},
        max_depth=max_depth,
        include_patterns=include_patterns or [],
        exclude_patterns=exclude_patterns or [],
    )

    config = CrawlerAgent(agent_id=agent_id, name=name, sentinel_id=sentinel_id, scope=scope)

    crawler = GlueCrawlerAgent(config, region_name=region_name)
    crawlers[agent_id] = crawler

    # Assign crawler to sentinel
    sentinel = sentinels[sentinel_id]
    await sentinel.assign_crawler(agent_id)

    return json.dumps(
        {
            'success': True,
            'crawler': {
                'agent_id': agent_id,
                'name': name,
                'sentinel_id': sentinel_id,
                'resource_type': resource_type,
                'status': crawler.status.value,
                'created_at': config.created_at.isoformat(),
            },
        }
    )


@mcp.tool(name='run_crawler_agent')
async def run_crawler_agent(
    crawler_id: Annotated[str, Field(description='ID of the crawler to run')],
) -> str:
    """Run a crawler agent to discover data and report to its sentinel.

    The crawler will execute its crawling logic within its configured scope
    and send data reports to its assigned sentinel agent.

    Args:
        crawler_id: ID of the crawler to run

    Returns:
        JSON string with crawl results and report status
    """
    if crawler_id not in crawlers:
        return json.dumps({'success': False, 'error': 'Crawler not found'})

    crawler = crawlers[crawler_id]
    sentinel_id = crawler.sentinel_id

    if sentinel_id not in sentinels:
        return json.dumps({'success': False, 'error': 'Assigned sentinel not found'})

    sentinel = sentinels[sentinel_id]

    # Start crawler
    await crawler.start()

    # Perform crawling
    discovered_data = await crawler.crawl()

    # Report each discovered item to sentinel
    reports = []
    for data_item in discovered_data:
        report = await crawler.report_to_sentinel(
            data=data_item,
            data_type=data_item.get('resource_type', 'unknown'),
            metadata={'crawl_timestamp': datetime.utcnow().isoformat()},
        )
        # Send report to sentinel
        receipt = await sentinel.receive_report(report)
        reports.append(
            {'data_type': report.data_type, 'timestamp': report.timestamp.isoformat(), 'receipt': receipt}
        )

    return json.dumps(
        {
            'success': True,
            'crawler_id': crawler_id,
            'sentinel_id': sentinel_id,
            'items_discovered': len(discovered_data),
            'reports_sent': len(reports),
            'status': crawler.status.value,
            'reports': reports[:10],  # Limit to first 10 for readability
        }
    )


@mcp.tool(name='get_sentinel_reports')
async def get_sentinel_reports(
    sentinel_id: Annotated[str, Field(description='ID of the sentinel')],
    crawler_id: Annotated[
        Optional[str], Field(description='Optional filter by crawler ID')
    ] = None,
    data_type: Annotated[Optional[str], Field(description='Optional filter by data type')] = None,
    limit: Annotated[int, Field(description='Maximum number of reports to return')] = 100,
) -> str:
    """Get data reports from a sentinel agent.

    Retrieve reports that have been sent to a sentinel by its assigned crawlers.

    Args:
        sentinel_id: ID of the sentinel
        crawler_id: Optional filter by crawler ID
        data_type: Optional filter by data type
        limit: Maximum number of reports to return (default: 100)

    Returns:
        JSON string with reports
    """
    if sentinel_id not in sentinels:
        return json.dumps({'success': False, 'error': 'Sentinel not found'})

    sentinel = sentinels[sentinel_id]
    reports = await sentinel.get_reports(crawler_id=crawler_id, data_type=data_type, limit=limit)

    return json.dumps(
        {
            'success': True,
            'sentinel_id': sentinel_id,
            'report_count': len(reports),
            'reports': [
                {
                    'crawler_id': r.crawler_id,
                    'timestamp': r.timestamp.isoformat(),
                    'data_type': r.data_type,
                    'data': r.data,
                    'metadata': r.metadata,
                    'status': r.status.value,
                }
                for r in reports
            ],
        }
    )


@mcp.tool(name='get_sentinel_status')
async def get_sentinel_status(
    sentinel_id: Annotated[str, Field(description='ID of the sentinel')],
) -> str:
    """Get the status of a sentinel agent.

    Returns information about the sentinel including assigned crawlers
    and buffer statistics.

    Args:
        sentinel_id: ID of the sentinel

    Returns:
        JSON string with sentinel status
    """
    if sentinel_id not in sentinels:
        return json.dumps({'success': False, 'error': 'Sentinel not found'})

    sentinel = sentinels[sentinel_id]
    status = await sentinel.get_status()

    return json.dumps({'success': True, 'status': status})


@mcp.tool(name='list_agents')
async def list_agents(
    agent_type: Annotated[
        Optional[str], Field(description='Filter by agent type: "sentinel" or "crawler"')
    ] = None,
) -> str:
    """List all agents (sentinels and/or crawlers).

    Args:
        agent_type: Optional filter by agent type ("sentinel" or "crawler")

    Returns:
        JSON string with list of agents
    """
    result = {'success': True}

    if agent_type is None or agent_type == 'sentinel':
        result['sentinels'] = [
            {
                'agent_id': s.agent_id,
                'name': s.config.name,
                'status': s.status.value,
                'assigned_crawlers': len(s.config.assigned_crawlers),
                'buffer_size': len(s.config.data_buffer),
            }
            for s in sentinels.values()
        ]

    if agent_type is None or agent_type == 'crawler':
        result['crawlers'] = [
            {
                'agent_id': c.agent_id,
                'name': c.config.name,
                'sentinel_id': c.sentinel_id,
                'resource_type': c.config.scope.resource_type,
                'status': c.status.value,
                'report_count': c.config.report_count,
            }
            for c in crawlers.values()
        ]

    return json.dumps(result)


@mcp.tool(name='clear_sentinel_reports')
async def clear_sentinel_reports(
    sentinel_id: Annotated[str, Field(description='ID of the sentinel')],
    crawler_id: Annotated[
        Optional[str], Field(description='Optional - clear only reports from this crawler')
    ] = None,
) -> str:
    """Clear reports from a sentinel's buffer.

    Args:
        sentinel_id: ID of the sentinel
        crawler_id: Optional - clear only reports from this crawler

    Returns:
        JSON string with status
    """
    if sentinel_id not in sentinels:
        return json.dumps({'success': False, 'error': 'Sentinel not found'})

    sentinel = sentinels[sentinel_id]
    result = await sentinel.clear_reports(crawler_id=crawler_id)

    return json.dumps(result)


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == '__main__':
    main()
