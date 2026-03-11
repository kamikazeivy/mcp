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

"""OpenAI-enhanced crawler for intelligent data analysis."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from awslabs.sentinel_agent_mcp_server.agents.local_fs_crawler import LocalFileSystemCrawler
from awslabs.sentinel_agent_mcp_server.models import AgentStatus, CrawlerAgent


class OpenAICrawler(LocalFileSystemCrawler):
    """AI-enhanced crawler using OpenAI for content analysis and classification.

    This crawler extends the local file system crawler with OpenAI capabilities:
    - Content summarization
    - Automatic classification
    - Sentiment analysis
    - Key information extraction
    - Pattern recognition

    More maintainable for single developers than AWS infrastructure!
    """

    def __init__(
        self,
        config: CrawlerAgent,
        base_path: str = '.',
        api_key: Optional[str] = None,
        model: str = 'gpt-3.5-turbo',
        enable_content_analysis: bool = True,
    ):
        """Initialize the OpenAI-enhanced crawler.

        Args:
            config: Configuration for the crawler agent
            base_path: Base directory path to crawl
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: OpenAI model to use (default: gpt-3.5-turbo)
            enable_content_analysis: Whether to analyze file contents with AI
        """
        super().__init__(config, base_path)
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        self.model = model
        self.enable_content_analysis = enable_content_analysis
        self._client = None

    def _get_client(self):
        """Get or create OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI

                self._client = OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    'OpenAI package not installed. Install with: pip install awslabs.sentinel-agent-mcp-server[openai]'
                )
        return self._client

    async def _analyze_content(self, content: str, file_path: str) -> Dict[str, Any]:
        """Analyze file content using OpenAI.

        Args:
            content: File content to analyze
            file_path: Path to the file

        Returns:
            Analysis results including summary, classification, and key points
        """
        if not self.enable_content_analysis or not self.api_key:
            return {'analysis_enabled': False}

        try:
            client = self._get_client()

            # Create analysis prompt
            prompt = f"""Analyze this file and provide:
1. A brief summary (1-2 sentences)
2. File type/category classification
3. Key information or purpose
4. Any notable patterns or concerns

File: {file_path}
Content (first 1000 chars):
{content[:1000]}
"""

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are a helpful assistant that analyzes files and provides structured insights.',
                    },
                    {'role': 'user', 'content': prompt},
                ],
                temperature=0.3,
                max_tokens=200,
            )

            analysis = response.choices[0].message.content

            return {
                'analysis_enabled': True,
                'ai_summary': analysis,
                'model_used': self.model,
                'tokens_used': response.usage.total_tokens if response.usage else 0,
            }

        except Exception as e:
            return {'analysis_enabled': True, 'error': str(e)}

    async def _get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """Get information about a specific file with AI analysis.

        Args:
            file_path: Path to the file

        Returns:
            Dictionary with file information and AI analysis
        """
        # Get basic file info from parent class
        file_info = await super()._get_file_info(file_path)

        # Add AI analysis if enabled
        if self.enable_content_analysis and 'error' not in file_info:
            try:
                # Read file content for analysis (limit size)
                if file_info.get('size_bytes', 0) < 100000:  # Only analyze files < 100KB
                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        analysis = await self._analyze_content(content, str(file_path))
                        file_info['ai_analysis'] = analysis
                    except Exception as e:
                        file_info['ai_analysis'] = {
                            'analysis_enabled': True,
                            'error': f'Could not read file: {e}',
                        }
                else:
                    file_info['ai_analysis'] = {
                        'analysis_enabled': True,
                        'skipped': 'File too large for analysis',
                    }
            except Exception as e:
                file_info['ai_analysis'] = {'error': str(e)}

        return file_info

    async def classify_discovered_data(
        self, discovered_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Use OpenAI to classify and categorize discovered data.

        Args:
            discovered_data: List of discovered items

        Returns:
            Classification results with categories and insights
        """
        if not self.api_key:
            return {'error': 'OpenAI API key not configured'}

        try:
            client = self._get_client()

            # Create classification prompt
            data_summary = '\n'.join(
                [
                    f"- {item.get('name', 'unknown')}: {item.get('resource_type', 'unknown')}"
                    for item in discovered_data[:50]  # Limit to first 50 items
                ]
            )

            prompt = f"""Analyze this list of discovered files/directories and provide:
1. Main categories found
2. Overall purpose or project type
3. Notable patterns
4. Recommendations for organization

Discovered items:
{data_summary}
"""

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are a helpful assistant that analyzes file structures and provides insights.',
                    },
                    {'role': 'user', 'content': prompt},
                ],
                temperature=0.3,
                max_tokens=300,
            )

            return {
                'success': True,
                'classification': response.choices[0].message.content,
                'items_analyzed': min(len(discovered_data), 50),
                'model_used': self.model,
                'tokens_used': response.usage.total_tokens if response.usage else 0,
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}
