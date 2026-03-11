# Sentinel Agent MCP Server

A Model Context Protocol (MCP) server that provides scoped crawler agents with sentinel agent reporting capabilities. This server enables the creation of specialized crawler agents that discover and report data to assigned sentinel agents for centralized data transfer and management.

**💡 PERFECT FOR SOLO DEVELOPERS!** Use OpenAI for AI-enhanced crawling or go completely free with local crawling. No AWS infrastructure needed!

## Overview

The Sentinel Agent MCP Server implements a hierarchical agent architecture:

- **Sentinel Agents**: Coordinator agents that receive and manage data reports from assigned crawler agents
- **Scoped Crawler Agents**: Specialized agents that discover data within configured scopes and report back to their assigned sentinels

This architecture enables:
- Distributed data discovery with centralized coordination
- Scoped crawling with configurable filters and patterns
- Buffered data transfer for efficient processing
- **AI-enhanced analysis with OpenAI (recommended for solo devs!)**
- **Local file system crawling (FREE - no costs at all)**
- ~~AWS Glue integration~~ (not recommended - too costly and complex)

## Features

### Sentinel Agents

- Create and manage sentinel agents
- Receive and buffer data reports from crawlers
- Query reports with filtering by crawler ID and data type
- Manage crawler assignments
- Configurable buffer sizes

### Scoped Crawler Agents

**🚀 OpenAI Crawler (Recommended for Solo Developers)**
- AI-powered content analysis and summarization
- Automatic file classification and categorization
- Key information extraction
- Pattern recognition and insights
- Simple API key setup (much easier than AWS!)
- Pay-as-you-go pricing (more predictable than AWS)
- Install with: `pip install awslabs.sentinel-agent-mcp-server[openai]`

**Local File System Crawler (Cost-Free)**
- Crawl local directories and files
- No AI features, no cloud costs
- Configurable include/exclude patterns
- Hierarchical crawling with max depth control
- Works on any operating system
- Perfect for basic file discovery

**~~AWS Glue Crawler~~** (Not Recommended - Too Costly)
- AWS Glue integration (crawlers, databases, tables)
- Requires AWS credentials, IAM setup, ongoing costs
- Complex infrastructure management
- Only use if you already have AWS Glue infrastructure

## Prerequisites

* [Install Python 3.10+](https://www.python.org/downloads/release/python-3100/)

**For OpenAI crawler (recommended for solo developers):**
* OpenAI API key from [platform.openai.com](https://platform.openai.com/)

**For AWS Glue crawler (not recommended):**
* [Install the `uv` package manager](https://docs.astral.sh/uv/getting-started/installation/)
* [Install and configure the AWS CLI with credentials](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html)

## Setup

### OpenAI API Key (Recommended for Solo Developers)

For AI-enhanced crawling, set your OpenAI API key:

```bash
export OPENAI_API_KEY='your-api-key-here'
```

Or pass it directly when creating crawlers.

### AWS Permissions (Not Recommended - Too Costly)

For AWS Glue crawler integration (if you really need it), add these IAM policies:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "glue:GetCrawler",
        "glue:GetCrawlers",
        "glue:ListCrawlers",
        "glue:GetDatabase",
        "glue:GetDatabases",
        "glue:GetTable",
        "glue:GetTables"
      ],
      "Resource": "*"
    }
  ]
}
```

## Installation

### 🚀 Recommended: With OpenAI Support (For Solo Developers)

```bash
pip install awslabs.sentinel-agent-mcp-server[openai]
```

### Basic Installation (Local Crawler Only - Free)

```bash
pip install awslabs.sentinel-agent-mcp-server
```

### With AWS Glue Support (Not Recommended)

```bash
pip install awslabs.sentinel-agent-mcp-server[aws]
```

### All Features

```bash
pip install awslabs.sentinel-agent-mcp-server[all]
```

### Via uvx (Recommended)

```bash
uvx awslabs.sentinel-agent-mcp-server
```

### From Source

```bash
cd src/sentinel-agent-mcp-server
pip install -e .[openai]  # Recommended: with OpenAI
pip install -e .  # Basic installation (local only)
pip install -e .[aws]  # With AWS support (not recommended)
```

## Usage Examples

### 1. Create a Sentinel Agent

```python
# Create a sentinel to coordinate crawler agents
create_sentinel_agent(
    name="DataDiscoverySentinel",
    max_buffer_size=1000
)
```

### 2. Create Scoped Crawler Agents

**🚀 OpenAI Crawler (RECOMMENDED for Solo Developers)**

```python
# AI-enhanced crawler with content analysis
create_crawler_agent(
    name="IntelligentCodeCrawler",
    sentinel_id="sentinel-123456",
    resource_type="file",
    crawler_type="openai",  # AI-powered!
    base_path="/path/to/project",
    include_patterns=[".py", ".js", ".md"],
    exclude_patterns=["__pycache__", "node_modules"],
    max_depth=3,
    openai_api_key="sk-...",  # or use OPENAI_API_KEY env var
    openai_model="gpt-3.5-turbo",  # or gpt-4 for better analysis
    enable_content_analysis=True
)

# After running the crawler, get AI-powered classification
classify_crawler_data_with_ai(
    crawler_id="crawler-abc123",
    sentinel_id="sentinel-123456"
)
```

**Local File System Crawler (Free, No AI)**

```python
# Crawl local directories (no AWS, no AI, completely free!)
create_crawler_agent(
    name="ProjectDirectoriesCrawler",
    sentinel_id="sentinel-123456",
    resource_type="directory",
    crawler_type="local",  # Free, no costs
    base_path="/path/to/project",
    include_patterns=["src", "lib"],
    exclude_patterns=["node_modules", ".git"]
)

# Crawl local files with pattern matching
create_crawler_agent(
    name="PythonFilesCrawler",
    sentinel_id="sentinel-123456",
    resource_type="file",
    crawler_type="local",  # Free, no costs
    base_path="/path/to/code",
    include_patterns=[".py"],
    exclude_patterns=["__pycache__", "test_"],
    max_depth=3
)
```

**~~AWS Glue Crawler~~ (Not Recommended - Too Costly)**

```python
# NOT RECOMMENDED FOR SOLO DEVELOPERS
# Only use if you already have AWS Glue infrastructure
# Requires AWS account, credentials, IAM setup, and ongoing costs
create_crawler_agent(
    name="ProductionDatabasesCrawler",
    sentinel_id="sentinel-123456",
    resource_type="glue-database",
    crawler_type="aws-glue",  # Requires AWS
    include_patterns=["prod_", "production_"],
    exclude_patterns=["test_", "dev_"]
)

# Create a crawler for Glue tables (requires AWS)
create_crawler_agent(
    name="SalesTablesCrawler",
    sentinel_id="sentinel-123456",
    resource_type="glue-table",
    crawler_type="aws-glue",  # Requires AWS
    include_patterns=["sales_"],
    max_depth=2
)
```

### 3. Run Crawlers and Collect Reports

```python
# Run a crawler - it will discover data and report to its sentinel
run_crawler_agent(crawler_id="crawler-789012")

# Get reports from the sentinel
get_sentinel_reports(
    sentinel_id="sentinel-123456",
    crawler_id="crawler-789012",  # Optional filter
    limit=50
)
```

### 4. Manage Agents

```python
# List all agents
list_agents()

# Get sentinel status
get_sentinel_status(sentinel_id="sentinel-123456")

# Clear old reports
clear_sentinel_reports(
    sentinel_id="sentinel-123456",
    crawler_id="crawler-789012"  # Optional - clear all if omitted
)
```

## MCP Tools

### Agent Management

- `create_sentinel_agent`: Create a new sentinel agent
- `create_crawler_agent`: Create a new scoped crawler agent
- `list_agents`: List all agents (sentinels and crawlers)
- `get_sentinel_status`: Get status of a sentinel agent

### Crawler Operations

- `run_crawler_agent`: Execute a crawler to discover and report data
- `get_sentinel_reports`: Retrieve reports from a sentinel
- `clear_sentinel_reports`: Clear reports from a sentinel's buffer

## Architecture

```
┌─────────────────┐
│ Sentinel Agent  │ ◄─── Coordinates multiple crawlers
│  (Coordinator)  │      Buffers and manages reports
└────────┬────────┘
         │ assigns
         ├───────────────┐
         │               │
    ┌────▼─────┐   ┌────▼─────┐
    │ Crawler  │   │ Crawler  │
    │  Agent   │   │  Agent   │
    │ (Scoped) │   │ (Scoped) │
    └────┬─────┘   └────┬─────┘
         │               │
         │ crawls        │ crawls
         │               │
    ┌────▼─────┐   ┌────▼─────┐
    │  Local   │   │  AWS     │
    │   File   │   │  Glue    │
    │  System  │   │Resources │
    └──────────┘   └──────────┘
       (FREE)      (Optional - AWS costs)
```

## Configuration

### Crawler Scope Configuration

**Local File System Crawler**

```python
scope = {
    "resource_type": "file",  # or "directory", "all"
    "include_patterns": [".py", ".js"],  # Match these patterns
    "exclude_patterns": ["test_", "__pycache__"],  # Exclude these patterns
    "max_depth": 3  # Maximum directory depth to crawl
}
```

**AWS Glue Crawler (Optional)**

```python
scope = {
    "resource_type": "glue-database",  # or "glue-crawler", "glue-table"
    "scope_filters": {"catalog_id": "12345"},  # Optional AWS-specific filters
    "include_patterns": ["prod_", "production_"],  # Match these patterns
    "exclude_patterns": ["test_", "dev_"],  # Exclude these patterns
    "max_depth": 2  # For hierarchical resources
}
```

### Supported Resource Types

**Local Crawler (Free)**
- `file`: Local files
- `directory`: Local directories
- `all`: Both files and directories

**AWS Glue Crawler (Requires AWS)**
- `glue-crawler`: AWS Glue Crawlers
- `glue-database`: AWS Glue Data Catalog Databases
- `glue-table`: AWS Glue Data Catalog Tables

## Development

### Running Tests

```bash
cd src/sentinel-agent-mcp-server
uv pip install -e ".[dev]"
pytest
```

### Code Quality

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type checking
pyright
```

## License

This project is licensed under the Apache-2.0 License. See the LICENSE file for details.

## Contributing

See the [CONTRIBUTING.md](../../CONTRIBUTING.md) file for information on how to contribute.

## Support

For issues and questions, please open an issue in the [GitHub repository](https://github.com/awslabs/mcp).
