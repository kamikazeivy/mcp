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

"""Base classes for agents."""

from abc import ABC, abstractmethod
from awslabs.sentinel_agent_mcp_server.models import (
    AgentStatus,
    CrawlerAgent,
    DataReport,
    SentinelAgent,
)
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class BaseCrawlerAgent(ABC):
    """Base class for scoped crawler agents."""

    def __init__(self, config: CrawlerAgent):
        """Initialize the crawler agent.

        Args:
            config: Configuration for the crawler agent
        """
        self.config = config
        self._status = config.status

    @property
    def agent_id(self) -> str:
        """Get the agent ID."""
        return self.config.agent_id

    @property
    def sentinel_id(self) -> str:
        """Get the assigned sentinel ID."""
        return self.config.sentinel_id

    @property
    def status(self) -> AgentStatus:
        """Get the current status."""
        return self._status

    @status.setter
    def status(self, value: AgentStatus):
        """Set the current status."""
        self._status = value
        self.config.status = value

    @abstractmethod
    async def crawl(self) -> List[Dict[str, Any]]:
        """Perform crawling within the configured scope.

        Returns:
            List of discovered data items
        """
        pass

    async def report_to_sentinel(
        self, data: Dict[str, Any], data_type: str, metadata: Optional[Dict[str, Any]] = None
    ) -> DataReport:
        """Create a data report to send to the assigned sentinel.

        Args:
            data: The data payload to report
            data_type: Type of data being reported
            metadata: Optional metadata about the data

        Returns:
            DataReport object
        """
        report = DataReport(
            crawler_id=self.agent_id,
            sentinel_id=self.sentinel_id,
            timestamp=datetime.now(timezone.utc),
            data_type=data_type,
            data=data,
            metadata=metadata or {},
            status=self.status,
        )
        self.config.last_report_at = report.timestamp
        self.config.report_count += 1
        return report

    async def start(self) -> Dict[str, Any]:
        """Start the crawler agent.

        Returns:
            Status information
        """
        self.status = AgentStatus.ACTIVE
        return {'agent_id': self.agent_id, 'status': self.status.value, 'message': 'Agent started'}

    async def stop(self) -> Dict[str, Any]:
        """Stop the crawler agent.

        Returns:
            Status information
        """
        self.status = AgentStatus.STOPPED
        return {'agent_id': self.agent_id, 'status': self.status.value, 'message': 'Agent stopped'}


class BaseSentinelAgent:
    """Base class for sentinel agents."""

    def __init__(self, config: SentinelAgent):
        """Initialize the sentinel agent.

        Args:
            config: Configuration for the sentinel agent
        """
        self.config = config
        self._status = config.status

    @property
    def agent_id(self) -> str:
        """Get the agent ID."""
        return self.config.agent_id

    @property
    def status(self) -> AgentStatus:
        """Get the current status."""
        return self._status

    @status.setter
    def status(self, value: AgentStatus):
        """Set the current status."""
        self._status = value
        self.config.status = value

    async def receive_report(self, report: DataReport) -> Dict[str, Any]:
        """Receive a data report from an assigned crawler.

        Args:
            report: DataReport from a crawler

        Returns:
            Acknowledgment with status
        """
        # Verify crawler is assigned to this sentinel
        if report.crawler_id not in self.config.assigned_crawlers:
            return {
                'success': False,
                'message': f'Crawler {report.crawler_id} is not assigned to this sentinel',
            }

        # Add to buffer
        self.config.data_buffer.append(report)

        # Maintain buffer size
        if len(self.config.data_buffer) > self.config.max_buffer_size:
            self.config.data_buffer = self.config.data_buffer[-self.config.max_buffer_size :]

        return {
            'success': True,
            'message': 'Report received',
            'buffer_size': len(self.config.data_buffer),
            'report_timestamp': report.timestamp.isoformat(),
        }

    async def get_reports(
        self,
        crawler_id: Optional[str] = None,
        data_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[DataReport]:
        """Get reports from the buffer.

        Args:
            crawler_id: Optional filter by crawler ID
            data_type: Optional filter by data type
            limit: Maximum number of reports to return

        Returns:
            List of matching reports
        """
        reports = self.config.data_buffer

        if crawler_id:
            reports = [r for r in reports if r.crawler_id == crawler_id]

        if data_type:
            reports = [r for r in reports if r.data_type == data_type]

        return reports[-limit:]

    async def clear_reports(self, crawler_id: Optional[str] = None) -> Dict[str, Any]:
        """Clear reports from the buffer.

        Args:
            crawler_id: Optional - clear only reports from this crawler

        Returns:
            Status information
        """
        if crawler_id:
            original_count = len(self.config.data_buffer)
            self.config.data_buffer = [
                r for r in self.config.data_buffer if r.crawler_id != crawler_id
            ]
            cleared_count = original_count - len(self.config.data_buffer)
        else:
            cleared_count = len(self.config.data_buffer)
            self.config.data_buffer = []

        return {'success': True, 'cleared_count': cleared_count}

    async def assign_crawler(self, crawler_id: str) -> Dict[str, Any]:
        """Assign a crawler to this sentinel.

        Args:
            crawler_id: ID of the crawler to assign

        Returns:
            Status information
        """
        if crawler_id in self.config.assigned_crawlers:
            return {'success': False, 'message': 'Crawler already assigned'}

        self.config.assigned_crawlers.append(crawler_id)
        return {
            'success': True,
            'message': f'Crawler {crawler_id} assigned',
            'total_crawlers': len(self.config.assigned_crawlers),
        }

    async def unassign_crawler(self, crawler_id: str) -> Dict[str, Any]:
        """Unassign a crawler from this sentinel.

        Args:
            crawler_id: ID of the crawler to unassign

        Returns:
            Status information
        """
        if crawler_id not in self.config.assigned_crawlers:
            return {'success': False, 'message': 'Crawler not assigned'}

        self.config.assigned_crawlers.remove(crawler_id)
        # Optionally clear reports from this crawler
        await self.clear_reports(crawler_id)
        return {
            'success': True,
            'message': f'Crawler {crawler_id} unassigned',
            'total_crawlers': len(self.config.assigned_crawlers),
        }

    async def get_status(self) -> Dict[str, Any]:
        """Get the status of this sentinel.

        Returns:
            Status information including assigned crawlers and buffer stats
        """
        return {
            'agent_id': self.agent_id,
            'status': self.status.value,
            'assigned_crawlers': self.config.assigned_crawlers,
            'buffer_size': len(self.config.data_buffer),
            'max_buffer_size': self.config.max_buffer_size,
            'created_at': self.config.created_at.isoformat(),
        }
