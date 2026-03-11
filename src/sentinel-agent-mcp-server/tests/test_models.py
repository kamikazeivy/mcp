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

"""Tests for agent models."""

from awslabs.sentinel_agent_mcp_server.models import (
    AgentAssignment,
    AgentStatus,
    CrawlerAgent,
    CrawlerScope,
    DataReport,
    SentinelAgent,
)
from datetime import datetime


def test_agent_status_enum():
    """Test AgentStatus enum values."""
    assert AgentStatus.IDLE == 'idle'
    assert AgentStatus.ACTIVE == 'active'
    assert AgentStatus.REPORTING == 'reporting'
    assert AgentStatus.ERROR == 'error'
    assert AgentStatus.STOPPED == 'stopped'


def test_crawler_scope_model():
    """Test CrawlerScope model."""
    scope = CrawlerScope(
        resource_type='glue-database',
        scope_filters={'region': 'us-east-1'},
        max_depth=2,
        include_patterns=['prod_*'],
        exclude_patterns=['test_*'],
    )

    assert scope.resource_type == 'glue-database'
    assert scope.scope_filters == {'region': 'us-east-1'}
    assert scope.max_depth == 2
    assert scope.include_patterns == ['prod_*']
    assert scope.exclude_patterns == ['test_*']


def test_crawler_scope_defaults():
    """Test CrawlerScope with default values."""
    scope = CrawlerScope(resource_type='glue-table')

    assert scope.resource_type == 'glue-table'
    assert scope.scope_filters == {}
    assert scope.max_depth == 1
    assert scope.include_patterns == []
    assert scope.exclude_patterns == []


def test_data_report_model():
    """Test DataReport model."""
    report = DataReport(
        crawler_id='crawler-1',
        sentinel_id='sentinel-1',
        data_type='glue-database',
        data={'name': 'test_db', 'tables': 5},
        metadata={'region': 'us-east-1'},
    )

    assert report.crawler_id == 'crawler-1'
    assert report.sentinel_id == 'sentinel-1'
    assert report.data_type == 'glue-database'
    assert report.data['name'] == 'test_db'
    assert report.metadata['region'] == 'us-east-1'
    assert report.status == AgentStatus.ACTIVE
    assert isinstance(report.timestamp, datetime)


def test_crawler_agent_model():
    """Test CrawlerAgent model."""
    scope = CrawlerScope(resource_type='glue-database')
    agent = CrawlerAgent(
        agent_id='crawler-1',
        name='Test Crawler',
        sentinel_id='sentinel-1',
        scope=scope,
    )

    assert agent.agent_id == 'crawler-1'
    assert agent.name == 'Test Crawler'
    assert agent.sentinel_id == 'sentinel-1'
    assert agent.scope.resource_type == 'glue-database'
    assert agent.status == AgentStatus.IDLE
    assert agent.report_count == 0
    assert agent.last_report_at is None
    assert isinstance(agent.created_at, datetime)


def test_sentinel_agent_model():
    """Test SentinelAgent model."""
    sentinel = SentinelAgent(
        agent_id='sentinel-1',
        name='Test Sentinel',
        max_buffer_size=500,
    )

    assert sentinel.agent_id == 'sentinel-1'
    assert sentinel.name == 'Test Sentinel'
    assert sentinel.max_buffer_size == 500
    assert sentinel.assigned_crawlers == []
    assert sentinel.data_buffer == []
    assert sentinel.status == AgentStatus.IDLE
    assert isinstance(sentinel.created_at, datetime)


def test_agent_assignment_model():
    """Test AgentAssignment model."""
    assignment = AgentAssignment(
        crawler_id='crawler-1',
        sentinel_id='sentinel-1',
    )

    assert assignment.crawler_id == 'crawler-1'
    assert assignment.sentinel_id == 'sentinel-1'
    assert assignment.active is True
    assert isinstance(assignment.created_at, datetime)
