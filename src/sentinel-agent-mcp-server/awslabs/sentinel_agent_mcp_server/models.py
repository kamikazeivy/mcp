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

"""Data models for Sentinel Agent MCP Server."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    """Status of an agent."""

    IDLE = 'idle'
    ACTIVE = 'active'
    REPORTING = 'reporting'
    ERROR = 'error'
    STOPPED = 'stopped'


class CrawlerScope(BaseModel):
    """Scope configuration for a crawler agent."""

    resource_type: str = Field(..., description='Type of resource to crawl (e.g., s3, database)')
    scope_filters: Dict[str, Any] = Field(
        default_factory=dict, description='Filters to limit crawler scope'
    )
    max_depth: int = Field(default=1, description='Maximum depth for hierarchical crawling')
    include_patterns: List[str] = Field(
        default_factory=list, description='Patterns to include in crawling'
    )
    exclude_patterns: List[str] = Field(
        default_factory=list, description='Patterns to exclude from crawling'
    )


class DataReport(BaseModel):
    """Data report from a crawler to its sentinel."""

    crawler_id: str = Field(..., description='ID of the crawler that generated this report')
    sentinel_id: str = Field(..., description='ID of the assigned sentinel')
    timestamp: datetime = Field(default_factory=datetime.utcnow, description='Report timestamp')
    data_type: str = Field(..., description='Type of data being reported')
    data: Dict[str, Any] = Field(..., description='The actual data payload')
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description='Additional metadata about the data'
    )
    status: AgentStatus = Field(default=AgentStatus.ACTIVE, description='Status at report time')


class CrawlerAgent(BaseModel):
    """Configuration for a scoped crawler agent."""

    agent_id: str = Field(..., description='Unique identifier for the crawler')
    name: str = Field(..., description='Human-readable name for the crawler')
    sentinel_id: str = Field(..., description='ID of the assigned sentinel')
    scope: CrawlerScope = Field(..., description='Scope configuration for this crawler')
    status: AgentStatus = Field(default=AgentStatus.IDLE, description='Current status')
    created_at: datetime = Field(default_factory=datetime.utcnow, description='Creation timestamp')
    last_report_at: Optional[datetime] = Field(
        default=None, description='Timestamp of last report'
    )
    report_count: int = Field(default=0, description='Number of reports submitted')
    config: Dict[str, Any] = Field(
        default_factory=dict, description='Additional configuration'
    )


class SentinelAgent(BaseModel):
    """Configuration for a sentinel agent."""

    agent_id: str = Field(..., description='Unique identifier for the sentinel')
    name: str = Field(..., description='Human-readable name for the sentinel')
    assigned_crawlers: List[str] = Field(
        default_factory=list, description='List of assigned crawler IDs'
    )
    status: AgentStatus = Field(default=AgentStatus.IDLE, description='Current status')
    created_at: datetime = Field(default_factory=datetime.utcnow, description='Creation timestamp')
    data_buffer: List[DataReport] = Field(
        default_factory=list, description='Buffer of received data reports'
    )
    max_buffer_size: int = Field(
        default=1000, description='Maximum number of reports to buffer'
    )
    config: Dict[str, Any] = Field(
        default_factory=dict, description='Additional configuration'
    )


class AgentAssignment(BaseModel):
    """Assignment of a crawler to a sentinel."""

    crawler_id: str = Field(..., description='ID of the crawler')
    sentinel_id: str = Field(..., description='ID of the sentinel')
    created_at: datetime = Field(default_factory=datetime.utcnow, description='Assignment timestamp')
    active: bool = Field(default=True, description='Whether assignment is active')
