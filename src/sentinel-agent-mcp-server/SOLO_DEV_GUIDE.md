# Quick Start Guide for Solo Developers

## TL;DR

**Use OpenAI, NOT AWS!** This guide is specifically for solo developers who want something maintainable.

## Installation (2 minutes)

```bash
# Install with OpenAI support (RECOMMENDED)
pip install awslabs.sentinel-agent-mcp-server[openai]

# Set your API key
export OPENAI_API_KEY='sk-your-key-here'
```

## Basic Usage

```python
from awslabs.sentinel_agent_mcp_server.server import (
    create_sentinel_agent,
    create_crawler_agent,
    run_crawler_agent,
    get_sentinel_reports,
    classify_crawler_data_with_ai
)

# 1. Create a sentinel
sentinel = await create_sentinel_agent(name="MySentinel")

# 2. Create AI-powered crawler
crawler = await create_crawler_agent(
    name="SmartCrawler",
    sentinel_id="sentinel-123",
    resource_type="file",
    crawler_type="openai",  # AI-powered!
    base_path="/your/project",
    include_patterns=[".py", ".js"],
    exclude_patterns=["__pycache__"]
)

# 3. Run and get AI insights
await run_crawler_agent(crawler_id="crawler-456")
reports = await get_sentinel_reports(sentinel_id="sentinel-123")
insights = await classify_crawler_data_with_ai(
    crawler_id="crawler-456",
    sentinel_id="sentinel-123"
)
```

## Why This is Better Than AWS

### AWS Problems (for solo devs)
- ❌ 1 hour setup (IAM, credentials, policies)
- ❌ $5-50+ monthly costs
- ❌ Complex infrastructure
- ❌ High maintenance
- ❌ No AI features

### OpenAI Benefits
- ✅ 2 minute setup (just API key)
- ✅ $0-10 monthly costs (pay-per-use)
- ✅ No infrastructure
- ✅ Zero maintenance
- ✅ AI-powered analysis

## Cost Comparison

**Example: Analyzing 1000 files**

| Provider | Setup | Runtime | Monthly |
|----------|-------|---------|---------|
| AWS | 1 hour | 10 min | $10-30 |
| OpenAI | 2 min | 5 min | $2-5 |

## What You Get

### With OpenAI Crawler:
1. **File discovery** (like local crawler)
2. **AI summarization** (what each file does)
3. **Classification** (automatically categorize files)
4. **Insights** (patterns, recommendations)
5. **Key info extraction** (important details)

### With Local Crawler:
1. **File discovery** (just finds files)
2. That's it!

### With AWS Glue:
1. **Data catalog** (if you have Glue setup)
2. **Metadata** (basic info)
3. **High cost** (ongoing charges)
4. **High complexity** (IAM, credentials)

## Recommendation

**Solo developer?** → Use OpenAI crawler 🚀

**Need it free?** → Use local crawler 💚

**Have AWS already?** → Maybe keep using it, but consider migrating

**Starting fresh?** → **DO NOT USE AWS!** Use OpenAI instead.

## Demo

```bash
# Run the demo (no API key needed to see basic functionality)
python demo_openai_crawler.py

# Or with API key for full AI features
export OPENAI_API_KEY='your-key'
python demo_openai_crawler.py
```

## Support

This is designed for **one person** to maintain easily:
- Simple code structure
- Clear documentation
- Minimal dependencies
- No infrastructure
- Perfect for solo developers!
