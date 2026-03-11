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

"""Tests for local file system crawler."""

import pytest
import tempfile
from awslabs.sentinel_agent_mcp_server.agents.local_fs_crawler import LocalFileSystemCrawler
from awslabs.sentinel_agent_mcp_server.models import AgentStatus, CrawlerAgent, CrawlerScope
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Create a temporary directory with test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create test structure
        (tmp_path / 'test_dir1').mkdir()
        (tmp_path / 'test_dir2').mkdir()
        (tmp_path / 'prod_dir').mkdir()
        (tmp_path / 'test_dir1' / 'subdir').mkdir()

        # Create test files
        (tmp_path / 'file1.txt').write_text('test1')
        (tmp_path / 'file2.py').write_text('test2')
        (tmp_path / 'prod_config.json').write_text('{}')
        (tmp_path / 'test_dir1' / 'readme.md').write_text('readme')
        (tmp_path / 'test_dir1' / 'subdir' / 'deep.txt').write_text('deep')

        yield tmp_path


@pytest.mark.asyncio
async def test_local_crawler_initialization(temp_dir):
    """Test local crawler initialization."""
    scope = CrawlerScope(resource_type='file')
    config = CrawlerAgent(
        agent_id='test-crawler',
        name='Test Crawler',
        sentinel_id='test-sentinel',
        scope=scope,
    )
    crawler = LocalFileSystemCrawler(config, base_path=str(temp_dir))

    assert crawler.agent_id == 'test-crawler'
    assert crawler.sentinel_id == 'test-sentinel'
    assert crawler.status == AgentStatus.IDLE
    assert crawler.base_path == temp_dir


@pytest.mark.asyncio
async def test_crawl_files(temp_dir):
    """Test crawling files in a directory."""
    scope = CrawlerScope(resource_type='file', max_depth=1)
    config = CrawlerAgent(
        agent_id='test-crawler',
        name='Test Crawler',
        sentinel_id='test-sentinel',
        scope=scope,
    )
    crawler = LocalFileSystemCrawler(config, base_path=str(temp_dir))

    results = await crawler.crawl()

    # Should find files in root directory only (max_depth=1)
    assert len(results) >= 3
    file_names = [r['name'] for r in results if 'error' not in r]
    assert 'file1.txt' in file_names
    assert 'file2.py' in file_names
    assert 'prod_config.json' in file_names


@pytest.mark.asyncio
async def test_crawl_directories(temp_dir):
    """Test crawling directories."""
    scope = CrawlerScope(resource_type='directory', max_depth=1)
    config = CrawlerAgent(
        agent_id='test-crawler',
        name='Test Crawler',
        sentinel_id='test-sentinel',
        scope=scope,
    )
    crawler = LocalFileSystemCrawler(config, base_path=str(temp_dir))

    results = await crawler.crawl()

    # Should find directories in root
    assert len(results) >= 3
    dir_names = [r['name'] for r in results if 'error' not in r]
    assert 'test_dir1' in dir_names
    assert 'test_dir2' in dir_names
    assert 'prod_dir' in dir_names


@pytest.mark.asyncio
async def test_crawl_with_include_patterns(temp_dir):
    """Test crawling with include patterns."""
    scope = CrawlerScope(resource_type='file', include_patterns=['prod_', '.json'], max_depth=1)
    config = CrawlerAgent(
        agent_id='test-crawler',
        name='Test Crawler',
        sentinel_id='test-sentinel',
        scope=scope,
    )
    crawler = LocalFileSystemCrawler(config, base_path=str(temp_dir))

    results = await crawler.crawl()

    # Should only find files matching patterns
    file_names = [r['name'] for r in results if 'error' not in r]
    assert 'prod_config.json' in file_names
    assert 'file1.txt' not in file_names


@pytest.mark.asyncio
async def test_crawl_with_exclude_patterns(temp_dir):
    """Test crawling with exclude patterns."""
    scope = CrawlerScope(resource_type='file', exclude_patterns=['test_', '.py'], max_depth=2)
    config = CrawlerAgent(
        agent_id='test-crawler',
        name='Test Crawler',
        sentinel_id='test-sentinel',
        scope=scope,
    )
    crawler = LocalFileSystemCrawler(config, base_path=str(temp_dir))

    results = await crawler.crawl()

    # Should exclude files matching patterns
    file_names = [r['name'] for r in results if 'error' not in r]
    assert 'file2.py' not in file_names
    assert 'file1.txt' in file_names or 'prod_config.json' in file_names


@pytest.mark.asyncio
async def test_crawl_all_items(temp_dir):
    """Test crawling all items (files and directories)."""
    scope = CrawlerScope(resource_type='all', max_depth=1)
    config = CrawlerAgent(
        agent_id='test-crawler',
        name='Test Crawler',
        sentinel_id='test-sentinel',
        scope=scope,
    )
    crawler = LocalFileSystemCrawler(config, base_path=str(temp_dir))

    results = await crawler.crawl()

    # Should find both files and directories
    assert len(results) >= 6  # 3 dirs + 3 files
    resource_types = [r['resource_type'] for r in results if 'error' not in r]
    assert 'file' in resource_types
    assert 'directory' in resource_types


@pytest.mark.asyncio
async def test_file_info_structure(temp_dir):
    """Test that file info has expected structure."""
    scope = CrawlerScope(resource_type='file', max_depth=1)
    config = CrawlerAgent(
        agent_id='test-crawler',
        name='Test Crawler',
        sentinel_id='test-sentinel',
        scope=scope,
    )
    crawler = LocalFileSystemCrawler(config, base_path=str(temp_dir))

    results = await crawler.crawl()

    # Check first valid file result
    file_result = next((r for r in results if r.get('resource_type') == 'file'), None)
    assert file_result is not None
    assert 'name' in file_result
    assert 'path' in file_result
    assert 'size_bytes' in file_result
    assert 'extension' in file_result
    assert 'modified_time' in file_result
    assert 'permissions' in file_result


@pytest.mark.asyncio
async def test_directory_info_structure(temp_dir):
    """Test that directory info has expected structure."""
    scope = CrawlerScope(resource_type='directory', max_depth=1)
    config = CrawlerAgent(
        agent_id='test-crawler',
        name='Test Crawler',
        sentinel_id='test-sentinel',
        scope=scope,
    )
    crawler = LocalFileSystemCrawler(config, base_path=str(temp_dir))

    results = await crawler.crawl()

    # Check first valid directory result
    dir_result = next((r for r in results if r.get('resource_type') == 'directory'), None)
    assert dir_result is not None
    assert 'name' in dir_result
    assert 'path' in dir_result
    assert 'item_count' in dir_result
    assert 'modified_time' in dir_result
    assert 'permissions' in dir_result


@pytest.mark.asyncio
async def test_max_depth_enforcement(temp_dir):
    """Test that max_depth is properly enforced."""
    # Create deeper structure
    deep_path = temp_dir / 'test_dir1' / 'subdir'
    (deep_path / 'deeper').mkdir()
    (deep_path / 'deeper' / 'deepest.txt').write_text('very deep')

    # Crawl with max_depth=1 (only root level)
    scope = CrawlerScope(resource_type='file', max_depth=1)
    config = CrawlerAgent(
        agent_id='test-crawler',
        name='Test Crawler',
        sentinel_id='test-sentinel',
        scope=scope,
    )
    crawler = LocalFileSystemCrawler(config, base_path=str(temp_dir))

    results = await crawler.crawl()
    file_names = [r['name'] for r in results if 'error' not in r]

    # Should not find deep files
    assert 'deepest.txt' not in file_names
    assert 'deep.txt' not in file_names

    # Crawl with max_depth=4
    scope2 = CrawlerScope(resource_type='file', max_depth=4)
    config2 = CrawlerAgent(
        agent_id='test-crawler-2',
        name='Test Crawler 2',
        sentinel_id='test-sentinel',
        scope=scope2,
    )
    crawler2 = LocalFileSystemCrawler(config2, base_path=str(temp_dir))

    results2 = await crawler2.crawl()
    file_names2 = [r['name'] for r in results2 if 'error' not in r]

    # Should find files up to depth 4
    assert 'deep.txt' in file_names2
    assert 'deepest.txt' in file_names2
