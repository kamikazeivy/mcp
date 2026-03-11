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
import uuid
from awslabs.sentinel_agent_mcp_server.agents.base import BaseCrawlerAgent, BaseSentinelAgent
from awslabs.sentinel_agent_mcp_server.agents.local_fs_crawler import LocalFileSystemCrawler
from awslabs.sentinel_agent_mcp_server.models import (
    CrawlerAgent,
    CrawlerScope,
    SentinelAgent,
)
from datetime import datetime, timezone
from fastmcp import FastMCP
from pydantic import Field
from typing import Annotated, Any, Dict, List, Optional, Union


# Try to import AWS Glue crawler (optional dependency)
try:
    from awslabs.sentinel_agent_mcp_server.agents.glue_crawler import GlueCrawlerAgent

    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False

# Try to import OpenAI crawler (optional dependency)
try:
    from awslabs.sentinel_agent_mcp_server.agents.openai_crawler import OpenAICrawler

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


# Initialize MCP server
mcp = FastMCP(
    'Sentinel Agent MCP Server - Manage scoped crawler agents that report to sentinel agents'
)

# In-memory storage for agents
sentinels: Dict[str, BaseSentinelAgent] = {}
crawlers: Dict[str, Union[BaseCrawlerAgent, LocalFileSystemCrawler]] = {}


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
        agent_id = f'sentinel-{uuid.uuid4().hex[:12]}'

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
            description='Type of resource to crawl. Local: directory, file, all. AWS (if available): glue-crawler, glue-database, glue-table'
        ),
    ],
    crawler_type: Annotated[
        str,
        Field(
            description='Type of crawler: "local" (free), "openai" (AI-enhanced), or "aws-glue" (requires AWS)'
        ),
    ] = 'local',
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
    base_path: Annotated[
        Optional[str],
        Field(description='Base directory path for local/openai crawler (default: current directory)'),
    ] = None,
    openai_api_key: Annotated[
        Optional[str],
        Field(description='OpenAI API key (for openai crawler, uses OPENAI_API_KEY env var if not provided)'),
    ] = None,
    openai_model: Annotated[
        str, Field(description='OpenAI model to use (default: gpt-3.5-turbo)')
    ] = 'gpt-3.5-turbo',
    enable_content_analysis: Annotated[
        bool, Field(description='Enable AI content analysis for openai crawler (default: True)')
    ] = True,
    region_name: Annotated[
        Optional[str], Field(description='AWS region name (for aws-glue crawler only)')
    ] = None,
) -> str:
    """Create a new scoped crawler agent assigned to a sentinel.

    Crawler agents discover and report data within their configured scope
    to their assigned sentinel agent.

    Args:
        name: Human-readable name for the crawler
        sentinel_id: ID of the sentinel to assign this crawler to
        resource_type: Type of resource to crawl
            - Local: directory, file, all
            - AWS Glue: glue-crawler, glue-database, glue-table
        crawler_type: Type of crawler:
            - "local" (free, no AWS, no AI)
            - "openai" (AI-enhanced, requires OpenAI API key)
            - "aws-glue" (requires AWS)
        agent_id: Optional unique ID (auto-generated if not provided)
        scope_filters: Optional filters to limit crawler scope
        include_patterns: Optional patterns to include in crawling
        exclude_patterns: Optional patterns to exclude from crawling
        max_depth: Maximum depth for hierarchical crawling (default: 1)
        base_path: Base directory path for local/openai crawler
        openai_api_key: OpenAI API key (for openai crawler)
        openai_model: OpenAI model to use (default: gpt-3.5-turbo)
        enable_content_analysis: Enable AI content analysis (default: True)
        region_name: Optional AWS region name (for aws-glue crawler)

    Returns:
        JSON string with crawler creation status and details
    """
    if agent_id is None:
        agent_id = f'crawler-{uuid.uuid4().hex[:12]}'

    if agent_id in crawlers:
        return json.dumps({'success': False, 'error': 'Crawler ID already exists'})

    if sentinel_id not in sentinels:
        return json.dumps({'success': False, 'error': 'Sentinel not found'})

    # Check if OpenAI crawler is requested but not available
    if crawler_type == 'openai' and not OPENAI_AVAILABLE:
        return json.dumps(
            {
                'success': False,
                'error': 'OpenAI crawler requires openai package. Install with: pip install awslabs.sentinel-agent-mcp-server[openai]',
            }
        )

    # Check if AWS crawler is requested but not available
    if crawler_type == 'aws-glue' and not AWS_AVAILABLE:
        return json.dumps(
            {
                'success': False,
                'error': 'AWS Glue crawler requires boto3. Install with: pip install awslabs.sentinel-agent-mcp-server[aws]',
            }
        )

    scope = CrawlerScope(
        resource_type=resource_type,
        scope_filters=scope_filters or {},
        max_depth=max_depth,
        include_patterns=include_patterns or [],
        exclude_patterns=exclude_patterns or [],
    )

    config = CrawlerAgent(agent_id=agent_id, name=name, sentinel_id=sentinel_id, scope=scope)

    # Create appropriate crawler type
    if crawler_type == 'local':
        crawler = LocalFileSystemCrawler(config, base_path=base_path or '.')
    elif crawler_type == 'openai':
        crawler = OpenAICrawler(
            config,
            base_path=base_path or '.',
            api_key=openai_api_key,
            model=openai_model,
            enable_content_analysis=enable_content_analysis,
        )
    elif crawler_type == 'aws-glue':
        crawler = GlueCrawlerAgent(config, region_name=region_name)
    else:
        return json.dumps(
            {
                'success': False,
                'error': f'Unknown crawler type: {crawler_type}. Use "local", "openai", or "aws-glue"',
            }
        )

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
                'crawler_type': crawler_type,
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
            metadata={'crawl_timestamp': datetime.now(timezone.utc).isoformat()},
        )
        # Send report to sentinel
        receipt = await sentinel.receive_report(report)
        reports.append(
            {
                'data_type': report.data_type,
                'timestamp': report.timestamp.isoformat(),
                'receipt': receipt,
            }
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
                'crawler_type': (
                    'openai'
                    if 'OpenAICrawler' in type(c).__name__
                    else 'local' if isinstance(c, LocalFileSystemCrawler) else 'aws-glue'
                ),
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


@mcp.tool(name='classify_crawler_data_with_ai')
async def classify_crawler_data_with_ai(
    crawler_id: Annotated[str, Field(description='ID of the OpenAI crawler')],
    sentinel_id: Annotated[str, Field(description='ID of the sentinel with reports')],
) -> str:
    """Use AI to classify and analyze discovered data (OpenAI crawler only).

    This tool uses OpenAI to provide intelligent classification and insights
    about the data discovered by a crawler. Only works with openai crawler type.

    Args:
        crawler_id: ID of the OpenAI crawler
        sentinel_id: ID of the sentinel containing reports

    Returns:
        JSON string with AI classification and insights
    """
    if crawler_id not in crawlers:
        return json.dumps({'success': False, 'error': 'Crawler not found'})

    crawler = crawlers[crawler_id]

    # Check if crawler is OpenAI type
    if 'OpenAICrawler' not in type(crawler).__name__:
        return json.dumps(
            {
                'success': False,
                'error': 'This tool only works with OpenAI crawler type. Create crawler with crawler_type="openai"',
            }
        )

    if sentinel_id not in sentinels:
        return json.dumps({'success': False, 'error': 'Sentinel not found'})

    sentinel = sentinels[sentinel_id]

    # Get reports for this crawler
    reports = await sentinel.get_reports(crawler_id=crawler_id)

    if not reports:
        return json.dumps(
            {
                'success': False,
                'error': 'No reports found. Run the crawler first with run_crawler_agent',
            }
        )

    # Extract discovered data from reports
    discovered_data = [report.data for report in reports]

    # Use OpenAI to classify
    classification_result = await crawler.classify_discovered_data(discovered_data)

    return json.dumps(classification_result)


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == '__main__':
    main()
