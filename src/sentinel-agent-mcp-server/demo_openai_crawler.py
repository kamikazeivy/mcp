#!/usr/bin/env python
"""
Demo script showing OpenAI-enhanced crawler usage.

This demonstrates AI-powered content analysis perfect for solo developers!
Much more maintainable than AWS infrastructure.
"""

import asyncio
import json
import os
from awslabs.sentinel_agent_mcp_server.server import (
    classify_crawler_data_with_ai,
    create_crawler_agent,
    create_sentinel_agent,
    get_sentinel_reports,
    list_agents,
    run_crawler_agent,
)


async def main():
    """Run a demo of the OpenAI-enhanced crawler."""
    print('=' * 70)
    print('Sentinel Agent MCP Server - OpenAI-Enhanced Crawler Demo')
    print('AI-Powered Analysis - Perfect for Solo Developers!')
    print('=' * 70)
    print()

    # Check for API key
    if not os.environ.get('OPENAI_API_KEY'):
        print('⚠️  Warning: OPENAI_API_KEY not set. AI analysis will be disabled.')
        print('   Set it with: export OPENAI_API_KEY="your-key-here"')
        print()

    # Step 1: Create a sentinel agent
    print('Step 1: Creating a sentinel agent...')
    sentinel_result = await create_sentinel_agent(
        name='AIEnhancedSentinel', max_buffer_size=500
    )
    sentinel_data = json.loads(sentinel_result)
    sentinel_id = sentinel_data['sentinel']['agent_id']
    print(f'✓ Created sentinel: {sentinel_id}')
    print(f'  Name: {sentinel_data["sentinel"]["name"]}')
    print()

    # Step 2: Create an OpenAI-enhanced crawler
    print('Step 2: Creating an AI-enhanced crawler with OpenAI...')
    crawler_result = await create_crawler_agent(
        name='IntelligentPythonCrawler',
        sentinel_id=sentinel_id,
        resource_type='file',
        crawler_type='openai',  # AI-enhanced!
        base_path='.',
        include_patterns=['.py'],
        exclude_patterns=['__pycache__', '.venv', 'test_'],
        max_depth=2,
        openai_model='gpt-3.5-turbo',
        enable_content_analysis=True,
    )
    crawler_data = json.loads(crawler_result)
    if not crawler_data['success']:
        print(f'✗ Error creating crawler: {crawler_data.get("error")}')
        print()
        print('💡 To use AI features, install with:')
        print('   pip install awslabs.sentinel-agent-mcp-server[openai]')
        print()
        print('Or try the free local crawler (demo_local_crawler.py)')
        return

    crawler_id = crawler_data['crawler']['agent_id']
    print(f'✓ Created AI-enhanced crawler: {crawler_id}')
    print(f'  Name: {crawler_data["crawler"]["name"]}')
    print(f'  Type: {crawler_data["crawler"]["crawler_type"]} (AI-POWERED!)')
    print(f'  Resource: {crawler_data["crawler"]["resource_type"]}')
    print()

    # Step 3: Run the crawler with AI analysis
    print('Step 3: Running AI-enhanced crawler...')
    print('  (This will analyze files using OpenAI)')
    run_result = await run_crawler_agent(crawler_id=crawler_id)
    run_data = json.loads(run_result)
    print(f'✓ Crawler completed')
    print(f'  Items discovered: {run_data.get("items_discovered", 0)}')
    print(f'  Reports sent: {run_data.get("reports_sent", 0)}')
    print()

    # Step 4: Get reports with AI analysis
    print('Step 4: Retrieving AI-analyzed reports...')
    reports_result = await get_sentinel_reports(sentinel_id=sentinel_id, limit=5)
    reports_data = json.loads(reports_result)
    reports = reports_data.get('reports', [])

    print(f'✓ Retrieved {len(reports)} reports')
    print('\nSample AI-analyzed files:')
    for i, report in enumerate(reports[:3], 1):
        data = report['data']
        if 'error' not in data:
            print(f"\n  {i}. {data.get('name', 'unknown')}")
            print(f"     Path: {data.get('path', 'unknown')}")
            print(f"     Size: {data.get('size_bytes', 0)} bytes")

            # Show AI analysis if available
            ai_analysis = data.get('ai_analysis', {})
            if ai_analysis.get('analysis_enabled'):
                if 'ai_summary' in ai_analysis:
                    print(f"     🤖 AI Analysis:")
                    summary = ai_analysis['ai_summary']
                    # Truncate long summaries
                    if len(summary) > 200:
                        summary = summary[:200] + '...'
                    print(f"        {summary}")
                    print(f"        Model: {ai_analysis.get('model_used', 'unknown')}")
                    print(
                        f"        Tokens: {ai_analysis.get('tokens_used', 0)}"
                    )
                elif 'error' in ai_analysis:
                    print(f"     ⚠️  AI Analysis Error: {ai_analysis['error']}")
            else:
                print('     (AI analysis not enabled)')
    print()

    # Step 5: Get AI classification of all discovered data
    print('Step 5: Getting AI-powered classification of all data...')
    classification_result = await classify_crawler_data_with_ai(
        crawler_id=crawler_id, sentinel_id=sentinel_id
    )
    classification_data = json.loads(classification_result)

    if classification_data.get('success'):
        print('✓ AI Classification complete!')
        print(f'  Items analyzed: {classification_data.get("items_analyzed", 0)}')
        print(f'  Model used: {classification_data.get("model_used", "unknown")}')
        print(
            f'  Tokens used: {classification_data.get("tokens_used", 0)}'
        )
        print('\n  📊 AI Insights:')
        classification = classification_data.get('classification', '')
        # Format the classification nicely
        for line in classification.split('\n')[:10]:  # First 10 lines
            if line.strip():
                print(f'     {line}')
    else:
        print(f'✗ Classification failed: {classification_data.get("error")}')
    print()

    # Step 6: List all agents
    print('Step 6: Listing all agents...')
    list_result = await list_agents()
    list_data = json.loads(list_result)

    sentinels = list_data.get('sentinels', [])
    crawlers_list = list_data.get('crawlers', [])

    print(f'✓ Total sentinels: {len(sentinels)}')
    print(f'✓ Total crawlers: {len(crawlers_list)}')
    for crawler in crawlers_list:
        print(f'  - {crawler["name"]} ({crawler["crawler_type"]})')
    print()

    print('=' * 70)
    print('Demo completed successfully!')
    print('AI-Enhanced Crawling - Much Better Than AWS for Solo Devs!')
    print('=' * 70)
    print()
    print('💡 Why OpenAI is better than AWS for solo developers:')
    print('   ✓ Simple API key setup (vs complex AWS IAM)')
    print('   ✓ Pay-as-you-go pricing (vs unpredictable AWS costs)')
    print('   ✓ No infrastructure to manage')
    print('   ✓ AI-powered insights and analysis')
    print('   ✓ Perfect for single developer workflows')


if __name__ == '__main__':
    asyncio.run(main())
