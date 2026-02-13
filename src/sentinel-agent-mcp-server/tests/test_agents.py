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

"""Tests for base agent classes."""

import pytest
from datetime import datetime
from awslabs.sentinel_agent_mcp_server.models import (
    AgentStatus,
    CrawlerAgent,
    CrawlerScope,
    DataReport,
    SentinelAgent,
)
from awslabs.sentinel_agent_mcp_server.agents.base import BaseCrawlerAgent, BaseSentinelAgent


class MockCrawlerAgent(BaseCrawlerAgent):
    """Mock crawler agent for testing."""

    async def crawl(self):
        """Mock crawl implementation."""
        return [
            {'resource_type': 'test', 'name': 'resource1'},
            {'resource_type': 'test', 'name': 'resource2'},
        ]


@pytest.mark.asyncio
async def test_crawler_agent_initialization():
    """Test crawler agent initialization."""
    scope = CrawlerScope(resource_type='test')
    config = CrawlerAgent(
        agent_id='test-crawler',
        name='Test Crawler',
        sentinel_id='test-sentinel',
        scope=scope,
    )
    agent = MockCrawlerAgent(config)

    assert agent.agent_id == 'test-crawler'
    assert agent.sentinel_id == 'test-sentinel'
    assert agent.status == AgentStatus.IDLE


@pytest.mark.asyncio
async def test_crawler_agent_start():
    """Test starting a crawler agent."""
    scope = CrawlerScope(resource_type='test')
    config = CrawlerAgent(
        agent_id='test-crawler',
        name='Test Crawler',
        sentinel_id='test-sentinel',
        scope=scope,
    )
    agent = MockCrawlerAgent(config)

    result = await agent.start()

    assert result['agent_id'] == 'test-crawler'
    assert result['status'] == 'active'
    assert agent.status == AgentStatus.ACTIVE


@pytest.mark.asyncio
async def test_crawler_agent_stop():
    """Test stopping a crawler agent."""
    scope = CrawlerScope(resource_type='test')
    config = CrawlerAgent(
        agent_id='test-crawler',
        name='Test Crawler',
        sentinel_id='test-sentinel',
        scope=scope,
    )
    agent = MockCrawlerAgent(config)

    result = await agent.stop()

    assert result['agent_id'] == 'test-crawler'
    assert result['status'] == 'stopped'
    assert agent.status == AgentStatus.STOPPED


@pytest.mark.asyncio
async def test_crawler_agent_report():
    """Test crawler agent reporting."""
    scope = CrawlerScope(resource_type='test')
    config = CrawlerAgent(
        agent_id='test-crawler',
        name='Test Crawler',
        sentinel_id='test-sentinel',
        scope=scope,
    )
    agent = MockCrawlerAgent(config)

    report = await agent.report_to_sentinel(
        data={'name': 'test-resource'},
        data_type='test',
        metadata={'source': 'test'},
    )

    assert isinstance(report, DataReport)
    assert report.crawler_id == 'test-crawler'
    assert report.sentinel_id == 'test-sentinel'
    assert report.data_type == 'test'
    assert report.data == {'name': 'test-resource'}
    assert report.metadata == {'source': 'test'}
    assert config.report_count == 1
    assert config.last_report_at is not None


@pytest.mark.asyncio
async def test_sentinel_agent_initialization():
    """Test sentinel agent initialization."""
    config = SentinelAgent(
        agent_id='test-sentinel',
        name='Test Sentinel',
        max_buffer_size=100,
    )
    sentinel = BaseSentinelAgent(config)

    assert sentinel.agent_id == 'test-sentinel'
    assert sentinel.status == AgentStatus.IDLE
    assert len(sentinel.config.assigned_crawlers) == 0
    assert len(sentinel.config.data_buffer) == 0


@pytest.mark.asyncio
async def test_sentinel_assign_crawler():
    """Test assigning a crawler to a sentinel."""
    config = SentinelAgent(
        agent_id='test-sentinel',
        name='Test Sentinel',
    )
    sentinel = BaseSentinelAgent(config)

    result = await sentinel.assign_crawler('crawler-1')

    assert result['success'] is True
    assert 'crawler-1' in sentinel.config.assigned_crawlers
    assert result['total_crawlers'] == 1


@pytest.mark.asyncio
async def test_sentinel_assign_duplicate_crawler():
    """Test assigning the same crawler twice."""
    config = SentinelAgent(
        agent_id='test-sentinel',
        name='Test Sentinel',
    )
    sentinel = BaseSentinelAgent(config)

    await sentinel.assign_crawler('crawler-1')
    result = await sentinel.assign_crawler('crawler-1')

    assert result['success'] is False
    assert len(sentinel.config.assigned_crawlers) == 1


@pytest.mark.asyncio
async def test_sentinel_receive_report():
    """Test sentinel receiving a report from a crawler."""
    config = SentinelAgent(
        agent_id='test-sentinel',
        name='Test Sentinel',
    )
    sentinel = BaseSentinelAgent(config)
    await sentinel.assign_crawler('crawler-1')

    report = DataReport(
        crawler_id='crawler-1',
        sentinel_id='test-sentinel',
        data_type='test',
        data={'name': 'test'},
    )

    result = await sentinel.receive_report(report)

    assert result['success'] is True
    assert result['buffer_size'] == 1
    assert len(sentinel.config.data_buffer) == 1


@pytest.mark.asyncio
async def test_sentinel_receive_report_unassigned_crawler():
    """Test sentinel receiving a report from an unassigned crawler."""
    config = SentinelAgent(
        agent_id='test-sentinel',
        name='Test Sentinel',
    )
    sentinel = BaseSentinelAgent(config)

    report = DataReport(
        crawler_id='crawler-1',
        sentinel_id='test-sentinel',
        data_type='test',
        data={'name': 'test'},
    )

    result = await sentinel.receive_report(report)

    assert result['success'] is False
    assert len(sentinel.config.data_buffer) == 0


@pytest.mark.asyncio
async def test_sentinel_get_reports():
    """Test getting reports from sentinel."""
    config = SentinelAgent(
        agent_id='test-sentinel',
        name='Test Sentinel',
    )
    sentinel = BaseSentinelAgent(config)
    await sentinel.assign_crawler('crawler-1')
    await sentinel.assign_crawler('crawler-2')

    # Add multiple reports
    for i in range(5):
        report = DataReport(
            crawler_id=f'crawler-{(i % 2) + 1}',
            sentinel_id='test-sentinel',
            data_type='test',
            data={'index': i},
        )
        await sentinel.receive_report(report)

    # Get all reports
    all_reports = await sentinel.get_reports()
    assert len(all_reports) == 5

    # Get reports from specific crawler
    crawler1_reports = await sentinel.get_reports(crawler_id='crawler-1')
    assert len(crawler1_reports) == 3

    # Get reports with limit
    limited_reports = await sentinel.get_reports(limit=3)
    assert len(limited_reports) == 3


@pytest.mark.asyncio
async def test_sentinel_clear_reports():
    """Test clearing reports from sentinel."""
    config = SentinelAgent(
        agent_id='test-sentinel',
        name='Test Sentinel',
    )
    sentinel = BaseSentinelAgent(config)
    await sentinel.assign_crawler('crawler-1')
    await sentinel.assign_crawler('crawler-2')

    # Add multiple reports
    for i in range(5):
        report = DataReport(
            crawler_id=f'crawler-{(i % 2) + 1}',
            sentinel_id='test-sentinel',
            data_type='test',
            data={'index': i},
        )
        await sentinel.receive_report(report)

    # Clear reports from crawler-1
    result = await sentinel.clear_reports(crawler_id='crawler-1')
    assert result['success'] is True
    assert result['cleared_count'] == 3
    assert len(sentinel.config.data_buffer) == 2

    # Clear all remaining reports
    result = await sentinel.clear_reports()
    assert result['cleared_count'] == 2
    assert len(sentinel.config.data_buffer) == 0


@pytest.mark.asyncio
async def test_sentinel_unassign_crawler():
    """Test unassigning a crawler from sentinel."""
    config = SentinelAgent(
        agent_id='test-sentinel',
        name='Test Sentinel',
    )
    sentinel = BaseSentinelAgent(config)
    await sentinel.assign_crawler('crawler-1')

    # Add a report
    report = DataReport(
        crawler_id='crawler-1',
        sentinel_id='test-sentinel',
        data_type='test',
        data={'name': 'test'},
    )
    await sentinel.receive_report(report)

    # Unassign crawler
    result = await sentinel.unassign_crawler('crawler-1')

    assert result['success'] is True
    assert 'crawler-1' not in sentinel.config.assigned_crawlers
    assert len(sentinel.config.data_buffer) == 0  # Reports should be cleared


@pytest.mark.asyncio
async def test_sentinel_buffer_size_limit():
    """Test sentinel buffer size limit."""
    config = SentinelAgent(
        agent_id='test-sentinel',
        name='Test Sentinel',
        max_buffer_size=5,
    )
    sentinel = BaseSentinelAgent(config)
    await sentinel.assign_crawler('crawler-1')

    # Add more reports than buffer size
    for i in range(10):
        report = DataReport(
            crawler_id='crawler-1',
            sentinel_id='test-sentinel',
            data_type='test',
            data={'index': i},
        )
        await sentinel.receive_report(report)

    # Buffer should be limited to max_buffer_size
    assert len(sentinel.config.data_buffer) == 5

    # Should contain the most recent reports (5-9)
    reports = await sentinel.get_reports()
    assert reports[0].data['index'] == 5
    assert reports[-1].data['index'] == 9


@pytest.mark.asyncio
async def test_sentinel_get_status():
    """Test getting sentinel status."""
    config = SentinelAgent(
        agent_id='test-sentinel',
        name='Test Sentinel',
        max_buffer_size=100,
    )
    sentinel = BaseSentinelAgent(config)
    await sentinel.assign_crawler('crawler-1')
    await sentinel.assign_crawler('crawler-2')

    status = await sentinel.get_status()

    assert status['agent_id'] == 'test-sentinel'
    assert status['status'] == 'idle'
    assert status['assigned_crawlers'] == ['crawler-1', 'crawler-2']
    assert status['buffer_size'] == 0
    assert status['max_buffer_size'] == 100
    assert 'created_at' in status
