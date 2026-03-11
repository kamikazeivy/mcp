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

"""Local file system crawler for cost-free data discovery."""

import os
from awslabs.sentinel_agent_mcp_server.agents.base import BaseCrawlerAgent
from awslabs.sentinel_agent_mcp_server.models import AgentStatus, CrawlerAgent
from pathlib import Path
from typing import Any, Dict, List


class LocalFileSystemCrawler(BaseCrawlerAgent):
    """Scoped crawler agent for local file system (no AWS costs)."""

    def __init__(self, config: CrawlerAgent, base_path: str = '.'):
        """Initialize the Local File System crawler agent.

        Args:
            config: Configuration for the crawler agent
            base_path: Base directory path to crawl (default: current directory)
        """
        super().__init__(config)
        self.base_path = Path(base_path).resolve()

    async def crawl(self) -> List[Dict[str, Any]]:
        """Perform crawling of local file system within the configured scope.

        Returns:
            List of discovered file/directory items
        """
        self.status = AgentStatus.ACTIVE
        discovered_data = []

        try:
            scope = self.config.scope
            resource_type = scope.resource_type

            if resource_type == 'directory':
                # Crawl directories
                directories = await self._list_directories()
                for directory in directories:
                    dir_data = await self._get_directory_info(directory)
                    discovered_data.append(dir_data)

            elif resource_type == 'file':
                # Crawl files
                files = await self._list_files()
                for file_path in files:
                    file_data = await self._get_file_info(file_path)
                    discovered_data.append(file_data)

            elif resource_type == 'all':
                # Crawl both files and directories
                items = await self._list_all_items()
                for item_path in items:
                    if item_path.is_dir():
                        item_data = await self._get_directory_info(item_path)
                    else:
                        item_data = await self._get_file_info(item_path)
                    discovered_data.append(item_data)

        except Exception as e:
            self.status = AgentStatus.ERROR
            discovered_data.append({'error': str(e), 'resource_type': resource_type})

        return discovered_data

    async def _list_directories(self) -> List[Path]:
        """List directories matching the scope filters.

        Returns:
            List of directory paths
        """
        directories = []
        max_depth = self.config.scope.max_depth

        for root, dirs, _ in os.walk(self.base_path):
            root_path = Path(root)
            # Calculate depth relative to base_path
            try:
                depth = len(root_path.relative_to(self.base_path).parts)
            except ValueError:
                depth = 0

            if depth >= max_depth:
                dirs.clear()  # Don't descend further
                continue

            for dir_name in dirs:
                if self._matches_scope_patterns(dir_name):
                    directories.append(root_path / dir_name)

        return directories

    async def _list_files(self) -> List[Path]:
        """List files matching the scope filters.

        Returns:
            List of file paths
        """
        files = []
        max_depth = self.config.scope.max_depth

        for root, dirs, filenames in os.walk(self.base_path):
            root_path = Path(root)
            # Calculate depth relative to base_path
            try:
                depth = len(root_path.relative_to(self.base_path).parts)
            except ValueError:
                depth = 0

            if depth >= max_depth:
                dirs.clear()  # Don't descend further
                continue

            for filename in filenames:
                if self._matches_scope_patterns(filename):
                    files.append(root_path / filename)

        return files

    async def _list_all_items(self) -> List[Path]:
        """List all items (files and directories) matching the scope filters.

        Returns:
            List of paths
        """
        items = []
        max_depth = self.config.scope.max_depth

        for root, dirs, filenames in os.walk(self.base_path):
            root_path = Path(root)
            # Calculate depth relative to base_path
            try:
                depth = len(root_path.relative_to(self.base_path).parts)
            except ValueError:
                depth = 0

            if depth >= max_depth:
                dirs.clear()  # Don't descend further
                continue

            # Add directories
            for dir_name in dirs:
                if self._matches_scope_patterns(dir_name):
                    items.append(root_path / dir_name)

            # Add files
            for filename in filenames:
                if self._matches_scope_patterns(filename):
                    items.append(root_path / filename)

        return items

    async def _get_directory_info(self, directory_path: Path) -> Dict[str, Any]:
        """Get information about a specific directory.

        Args:
            directory_path: Path to the directory

        Returns:
            Dictionary with directory information
        """
        try:
            stat_info = directory_path.stat()
            # Count items in directory
            try:
                item_count = len(list(directory_path.iterdir()))
            except PermissionError:
                item_count = 'N/A (Permission Denied)'

            return {
                'resource_type': 'directory',
                'name': directory_path.name,
                'path': str(directory_path),
                'size_bytes': stat_info.st_size,
                'item_count': item_count,
                'modified_time': stat_info.st_mtime,
                'created_time': stat_info.st_ctime,
                'permissions': oct(stat_info.st_mode)[-3:],
            }
        except Exception as e:
            return {
                'resource_type': 'directory',
                'name': directory_path.name,
                'path': str(directory_path),
                'error': str(e),
            }

    async def _get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """Get information about a specific file.

        Args:
            file_path: Path to the file

        Returns:
            Dictionary with file information
        """
        try:
            stat_info = file_path.stat()
            return {
                'resource_type': 'file',
                'name': file_path.name,
                'path': str(file_path),
                'size_bytes': stat_info.st_size,
                'extension': file_path.suffix,
                'modified_time': stat_info.st_mtime,
                'created_time': stat_info.st_ctime,
                'permissions': oct(stat_info.st_mode)[-3:],
            }
        except Exception as e:
            return {
                'resource_type': 'file',
                'name': file_path.name,
                'path': str(file_path),
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
