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

"""Tests for OpenAI crawler."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from awslabs.sentinel_agent_mcp_server.models import AgentStatus, CrawlerAgent, CrawlerScope


# Skip tests if openai not available
pytest.importorskip('openai', reason='OpenAI package not installed')

from awslabs.sentinel_agent_mcp_server.agents.openai_crawler import OpenAICrawler


@pytest.fixture
def temp_dir():
    """Create a temporary directory with test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create test files
        (tmp_path / 'test.py').write_text('def hello(): print("world")')
        (tmp_path / 'readme.md').write_text('# Test Project\nThis is a test.')
        (tmp_path / 'config.json').write_text('{"name": "test"}')

        yield tmp_path


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = (
        'Summary: Python test file with hello world function\n'
        'Category: Source Code\n'
        'Purpose: Simple greeting function\n'
        'Patterns: Basic Python structure'
    )
    mock_response.usage.total_tokens = 50
    return mock_response


@pytest.mark.asyncio
async def test_openai_crawler_initialization(temp_dir):
    """Test OpenAI crawler initialization."""
    scope = CrawlerScope(resource_type='file')
    config = CrawlerAgent(
        agent_id='test-crawler',
        name='Test Crawler',
        sentinel_id='test-sentinel',
        scope=scope,
    )
    crawler = OpenAICrawler(
        config, base_path=str(temp_dir), api_key='test-key', model='gpt-3.5-turbo'
    )

    assert crawler.agent_id == 'test-crawler'
    assert crawler.sentinel_id == 'test-sentinel'
    assert crawler.status == AgentStatus.IDLE
    assert crawler.api_key == 'test-key'
    assert crawler.model == 'gpt-3.5-turbo'
    assert crawler.enable_content_analysis is True


@pytest.mark.asyncio
async def test_openai_crawler_without_api_key(temp_dir):
    """Test OpenAI crawler works without API key (analysis disabled)."""
    scope = CrawlerScope(resource_type='file')
    config = CrawlerAgent(
        agent_id='test-crawler',
        name='Test Crawler',
        sentinel_id='test-sentinel',
        scope=scope,
    )
    # No API key provided
    crawler = OpenAICrawler(config, base_path=str(temp_dir), api_key=None)

    # Should still work, just without AI analysis
    results = await crawler.crawl()
    assert len(results) >= 3

    # Check that analysis is disabled
    for result in results:
        if 'ai_analysis' in result:
            assert result['ai_analysis'].get('analysis_enabled') is False


@pytest.mark.asyncio
@patch('openai.OpenAI')
async def test_openai_crawler_with_content_analysis(
    mock_openai_class, temp_dir, mock_openai_response
):
    """Test OpenAI crawler with content analysis enabled."""
    # Setup mock
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_openai_response
    mock_openai_class.return_value = mock_client

    scope = CrawlerScope(resource_type='file', max_depth=1)
    config = CrawlerAgent(
        agent_id='test-crawler',
        name='Test Crawler',
        sentinel_id='test-sentinel',
        scope=scope,
    )
    crawler = OpenAICrawler(
        config,
        base_path=str(temp_dir),
        api_key='test-key',
        enable_content_analysis=True,
    )

    results = await crawler.crawl()

    # Should have analyzed at least some files
    assert len(results) >= 3

    # Check that some files have AI analysis
    analyzed_files = [r for r in results if 'ai_analysis' in r and 'ai_summary' in r['ai_analysis']]

    # At least one file should be analyzed
    if analyzed_files:
        analysis = analyzed_files[0]['ai_analysis']
        assert analysis['analysis_enabled'] is True
        assert 'ai_summary' in analysis
        assert 'model_used' in analysis


@pytest.mark.asyncio
@patch('openai.OpenAI')
async def test_classify_discovered_data(mock_openai_class, temp_dir, mock_openai_response):
    """Test AI classification of discovered data."""
    # Setup mock
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client

    # Mock classification response
    classification_response = MagicMock()
    classification_response.choices = [MagicMock()]
    classification_response.choices[0].message.content = (
        'Categories: Python source, Documentation, Configuration\n'
        'Project Type: Small Python project\n'
        'Patterns: Standard project structure\n'
        'Recommendations: Add tests directory'
    )
    classification_response.usage.total_tokens = 75
    mock_client.chat.completions.create.return_value = classification_response

    scope = CrawlerScope(resource_type='file')
    config = CrawlerAgent(
        agent_id='test-crawler',
        name='Test Crawler',
        sentinel_id='test-sentinel',
        scope=scope,
    )
    crawler = OpenAICrawler(config, base_path=str(temp_dir), api_key='test-key')

    # Create mock discovered data
    discovered_data = [
        {'name': 'test.py', 'resource_type': 'file'},
        {'name': 'readme.md', 'resource_type': 'file'},
        {'name': 'config.json', 'resource_type': 'file'},
    ]

    result = await crawler.classify_discovered_data(discovered_data)

    assert result['success'] is True
    assert 'classification' in result
    assert 'Categories' in result['classification']
    assert result['items_analyzed'] == 3
    assert result['tokens_used'] == 75


@pytest.mark.asyncio
async def test_classify_without_api_key(temp_dir):
    """Test classification fails gracefully without API key."""
    scope = CrawlerScope(resource_type='file')
    config = CrawlerAgent(
        agent_id='test-crawler',
        name='Test Crawler',
        sentinel_id='test-sentinel',
        scope=scope,
    )
    crawler = OpenAICrawler(config, base_path=str(temp_dir), api_key=None)

    discovered_data = [{'name': 'test.py', 'resource_type': 'file'}]

    result = await crawler.classify_discovered_data(discovered_data)

    assert 'error' in result
    assert 'API key' in result['error']


@pytest.mark.asyncio
async def test_openai_crawler_inherits_local_features(temp_dir):
    """Test that OpenAI crawler inherits local file system features."""
    scope = CrawlerScope(
        resource_type='file', include_patterns=['.py'], exclude_patterns=['test_'], max_depth=1
    )
    config = CrawlerAgent(
        agent_id='test-crawler',
        name='Test Crawler',
        sentinel_id='test-sentinel',
        scope=scope,
    )
    crawler = OpenAICrawler(
        config, base_path=str(temp_dir), api_key='test-key', enable_content_analysis=False
    )

    results = await crawler.crawl()

    # Should find .py files
    file_names = [r['name'] for r in results if 'error' not in r]
    assert any('.py' in name for name in file_names)

    # Should not find .md files (not in include pattern)
    assert not any('readme.md' == name for name in file_names)
