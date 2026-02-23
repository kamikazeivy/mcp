# Sentinel Agent MCP Server

A Model Context Protocol (MCP) server that provides scoped crawler agents with sentinel agent reporting capabilities. This server enables the creation of specialized crawler agents that discover and report data to assigned sentinel agents for centralized data transfer and management.

**NEW: Now supports cost-free local file system crawling!** No AWS required for basic functionality.

## Overview

The Sentinel Agent MCP Server implements a hierarchical agent architecture:

- **Sentinel Agents**: Coordinator agents that receive and manage data reports from assigned crawler agents
- **Scoped Crawler Agents**: Specialized agents that discover data within configured scopes and report back to their assigned sentinels

This architecture enables:
- Distributed data discovery with centralized coordination
- Scoped crawling with configurable filters and patterns
- Buffered data transfer for efficient processing
- **Local file system crawling (FREE - no AWS costs)**
- Optional AWS Glue integration for data catalog exploration

## Features

### Sentinel Agents

- Create and manage sentinel agents
- Receive and buffer data reports from crawlers
- Query reports with filtering by crawler ID and data type
- Manage crawler assignments
- Configurable buffer sizes

### Scoped Crawler Agents

**Local File System Crawler (Cost-Free)**
- Crawl local directories and files
- No AWS account or credentials required
- Configurable include/exclude patterns
- Hierarchical crawling with max depth control
- Works on any operating system

**AWS Glue Crawler (Optional)**
- AWS Glue integration (crawlers, databases, tables)
- Requires AWS credentials and boto3
- Install with: `pip install awslabs.sentinel-agent-mcp-server[aws]`

## Prerequisites

* [Install Python 3.10+](https://www.python.org/downloads/release/python-3100/)

**For AWS Glue crawler (optional):**
* [Install the `uv` package manager](https://docs.astral.sh/uv/getting-started/installation/)
* [Install and configure the AWS CLI with credentials](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html)

## Setup

### AWS Permissions (Optional - Only for AWS Glue crawler)

For AWS Glue crawler integration, add these IAM policies:

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

### Basic Installation (Local Crawler Only - No AWS)

```bash
pip install awslabs.sentinel-agent-mcp-server
```

### With AWS Glue Support

```bash
pip install awslabs.sentinel-agent-mcp-server[aws]
```

### Via uvx (Recommended)

```bash
uvx awslabs.sentinel-agent-mcp-server
```

### From Source

```bash
cd src/sentinel-agent-mcp-server
pip install -e .  # Basic installation
pip install -e .[aws]  # With AWS support
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

**Local File System Crawler (Cost-Free)**

```python
# Crawl local directories (no AWS required!)
create_crawler_agent(
    name="ProjectDirectoriesCrawler",
    sentinel_id="sentinel-123456",
    resource_type="directory",
    crawler_type="local",  # Free, no AWS costs
    base_path="/path/to/project",
    include_patterns=["src", "lib"],
    exclude_patterns=["node_modules", ".git"]
)

# Crawl local files with pattern matching
create_crawler_agent(
    name="PythonFilesCrawler",
    sentinel_id="sentinel-123456",
    resource_type="file",
    crawler_type="local",  # Free, no AWS costs
    base_path="/path/to/code",
    include_patterns=[".py"],
    exclude_patterns=["__pycache__", "test_"],
    max_depth=3
)

# Crawl all items (files and directories)
create_crawler_agent(
    name="AllItemsCrawler",
    sentinel_id="sentinel-123456",
    resource_type="all",
    crawler_type="local",  # Free, no AWS costs
    base_path=".",  # Current directory
    max_depth=2
)
```

**AWS Glue Crawler (Requires AWS - Optional)**

```python
# Create a crawler for Glue databases (requires AWS)
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
