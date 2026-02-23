# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-02-23

### Added
- **Local File System Crawler**: Cost-free alternative to AWS Glue crawler
  - Crawl local directories and files without AWS account
  - No AWS costs - completely free to use
  - Supports file, directory, and combined crawling
  - Pattern-based filtering (include/exclude)
  - Configurable max depth for hierarchical crawling
- Made boto3 an optional dependency
- Added `crawler_type` parameter to `create_crawler_agent` tool
- Added comprehensive tests for local file system crawler (9 new tests)

### Changed
- boto3 is now optional - install with `pip install awslabs.sentinel-agent-mcp-server[aws]`
- Updated documentation with local crawler examples
- Enhanced architecture diagram to show both local and AWS options
- `create_crawler_agent` now defaults to `crawler_type="local"` (free option)

### Fixed
- Graceful handling when AWS Glue crawler requested but boto3 not installed

## [0.1.0] - 2026-02-13

### Added
- Initial release of Sentinel Agent MCP Server
- Sentinel agent base class for coordinating crawler agents
- Scoped crawler agent base class with reporting mechanism
- AWS Glue Crawler integration (crawlers, databases, tables)
- Data transfer protocol between crawlers and sentinels
- Configurable scope filters with include/exclude patterns
- Buffered data collection in sentinels
- MCP tools for agent management and operations
- Comprehensive documentation and usage examples
