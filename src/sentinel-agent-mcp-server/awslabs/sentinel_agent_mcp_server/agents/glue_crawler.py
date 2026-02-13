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

"""AWS Glue Crawler integration for scoped crawling."""

import boto3
from typing import Any, Dict, List, Optional
from awslabs.sentinel_agent_mcp_server.agents.base import BaseCrawlerAgent
from awslabs.sentinel_agent_mcp_server.models import CrawlerAgent, AgentStatus


class GlueCrawlerAgent(BaseCrawlerAgent):
    """Scoped crawler agent that integrates with AWS Glue Crawlers."""

    def __init__(self, config: CrawlerAgent, region_name: Optional[str] = None):
        """Initialize the Glue Crawler agent.

        Args:
            config: Configuration for the crawler agent
            region_name: AWS region name (optional, uses default if not specified)
        """
        super().__init__(config)
        self.glue_client = boto3.client('glue', region_name=region_name)

    async def crawl(self) -> List[Dict[str, Any]]:
        """Perform crawling using AWS Glue Crawlers within the configured scope.

        Returns:
            List of discovered data items
        """
        self.status = AgentStatus.ACTIVE
        discovered_data = []

        try:
            scope = self.config.scope
            resource_type = scope.resource_type

            if resource_type == 'glue-crawler':
                # Get list of crawlers matching the scope
                crawlers = await self._list_scoped_crawlers()
                for crawler_name in crawlers:
                    crawler_data = await self._get_crawler_info(crawler_name)
                    discovered_data.append(crawler_data)

            elif resource_type == 'glue-database':
                # Get list of databases matching the scope
                databases = await self._list_scoped_databases()
                for database_name in databases:
                    database_data = await self._get_database_info(database_name)
                    discovered_data.append(database_data)

            elif resource_type == 'glue-table':
                # Get list of tables matching the scope
                tables = await self._list_scoped_tables()
                for table_info in tables:
                    table_data = await self._get_table_info(
                        table_info['database'], table_info['table']
                    )
                    discovered_data.append(table_data)

        except Exception as e:
            self.status = AgentStatus.ERROR
            discovered_data.append({'error': str(e), 'resource_type': resource_type})

        return discovered_data

    async def _list_scoped_crawlers(self) -> List[str]:
        """List crawlers matching the scope filters.

        Returns:
            List of crawler names
        """
        crawlers = []
        scope = self.config.scope
        paginator = self.glue_client.get_paginator('list_crawlers')

        for page in paginator.paginate():
            for crawler_name in page.get('CrawlerNames', []):
                if self._matches_scope_patterns(crawler_name):
                    crawlers.append(crawler_name)

        return crawlers

    async def _list_scoped_databases(self) -> List[str]:
        """List databases matching the scope filters.

        Returns:
            List of database names
        """
        databases = []
        scope = self.config.scope
        filters = scope.scope_filters.get('catalog_id')
        catalog_id = filters if isinstance(filters, str) else None

        paginator = self.glue_client.get_paginator('get_databases')
        params = {}
        if catalog_id:
            params['CatalogId'] = catalog_id

        for page in paginator.paginate(**params):
            for database in page.get('DatabaseList', []):
                db_name = database['Name']
                if self._matches_scope_patterns(db_name):
                    databases.append(db_name)

        return databases

    async def _list_scoped_tables(self) -> List[Dict[str, str]]:
        """List tables matching the scope filters.

        Returns:
            List of table info dicts with 'database' and 'table' keys
        """
        tables = []
        scope = self.config.scope

        # Get databases first
        databases = await self._list_scoped_databases()

        for database_name in databases:
            paginator = self.glue_client.get_paginator('get_tables')
            for page in paginator.paginate(DatabaseName=database_name):
                for table in page.get('TableList', []):
                    table_name = table['Name']
                    if self._matches_scope_patterns(table_name):
                        tables.append({'database': database_name, 'table': table_name})

        return tables

    async def _get_crawler_info(self, crawler_name: str) -> Dict[str, Any]:
        """Get information about a specific crawler.

        Args:
            crawler_name: Name of the crawler

        Returns:
            Dictionary with crawler information
        """
        try:
            response = self.glue_client.get_crawler(Name=crawler_name)
            crawler = response['Crawler']
            return {
                'resource_type': 'glue-crawler',
                'name': crawler['Name'],
                'state': crawler.get('State'),
                'targets': crawler.get('Targets', {}),
                'database_name': crawler.get('DatabaseName'),
                'last_crawl': crawler.get('LastCrawl', {}),
                'crawl_elapsed_time': crawler.get('CrawlElapsedTime'),
            }
        except Exception as e:
            return {'resource_type': 'glue-crawler', 'name': crawler_name, 'error': str(e)}

    async def _get_database_info(self, database_name: str) -> Dict[str, Any]:
        """Get information about a specific database.

        Args:
            database_name: Name of the database

        Returns:
            Dictionary with database information
        """
        try:
            response = self.glue_client.get_database(Name=database_name)
            database = response['Database']
            return {
                'resource_type': 'glue-database',
                'name': database['Name'],
                'description': database.get('Description', ''),
                'location_uri': database.get('LocationUri', ''),
                'create_time': str(database.get('CreateTime', '')),
            }
        except Exception as e:
            return {'resource_type': 'glue-database', 'name': database_name, 'error': str(e)}

    async def _get_table_info(self, database_name: str, table_name: str) -> Dict[str, Any]:
        """Get information about a specific table.

        Args:
            database_name: Name of the database
            table_name: Name of the table

        Returns:
            Dictionary with table information
        """
        try:
            response = self.glue_client.get_table(DatabaseName=database_name, Name=table_name)
            table = response['Table']
            return {
                'resource_type': 'glue-table',
                'database': database_name,
                'name': table['Name'],
                'storage_descriptor': {
                    'location': table.get('StorageDescriptor', {}).get('Location', ''),
                    'columns': len(table.get('StorageDescriptor', {}).get('Columns', [])),
                },
                'partition_keys': len(table.get('PartitionKeys', [])),
                'create_time': str(table.get('CreateTime', '')),
                'update_time': str(table.get('UpdateTime', '')),
            }
        except Exception as e:
            return {
                'resource_type': 'glue-table',
                'database': database_name,
                'name': table_name,
                'error': str(e),
            }

    def _matches_scope_patterns(self, name: str) -> bool:
        """Check if a name matches the scope include/exclude patterns.

        Args:
            name: Name to check

        Returns:
            True if name matches patterns, False otherwise
        """
        scope = self.config.scope

        # Check exclude patterns first
        for pattern in scope.exclude_patterns:
            if pattern in name or name.startswith(pattern) or name.endswith(pattern):
                return False

        # If include patterns specified, name must match at least one
        if scope.include_patterns:
            for pattern in scope.include_patterns:
                if pattern in name or name.startswith(pattern) or name.endswith(pattern):
                    return True
            return False

        # No include patterns, and not excluded
        return True
