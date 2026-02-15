#!/usr/bin/env python3
"""Analyze URL matching between llms.txt and llms-full.txt"""

import re
from pathlib import Path

base_dir = Path(".claude/docs/anthropic")

# Extract all URLs from llms.txt and normalize them
llms_txt = (base_dir / "llms.txt").read_text()
llms_urls = {}  # normalized_url -> original_url

for match in re.finditer(r'\]\((https://[^)]+)\)', llms_txt):
    url = match.group(1)
    # Normalize
    normalized = url.rstrip('/').rstrip('.md')
    llms_urls[normalized] = url

# Extract all URLs from llms-full.txt
llms_full_txt = (base_dir / "llms-full.txt").read_text()
llms_full_urls = set()

for line in llms_full_txt.split('\n'):
    if line.startswith('URL:'):
        url = line.replace('URL:', '').strip().rstrip('/').rstrip('.md')
        llms_full_urls.add(url)

print(f"Unique normalized URLs in llms.txt: {len(llms_urls)}")
print(f"Unique URLs in llms-full.txt: {len(llms_full_urls)}")
print(f"Matches: {len(set(llms_urls.keys()) & llms_full_urls)}")

missing = set(llms_urls.keys()) - llms_full_urls

print(f"\nMissing in llms-full.txt: {len(missing)}")

# Group by section
dev_guide = []
resources = []
api_ref = []
other = []

for url in missing:
    if 'agent-sdk' in url or 'agents-and-tools' in url:
        dev_guide.append(url)
    elif '/resources/' in url or 'prompt-library' in url:
        resources.append(url)
    elif '/api/' in url:
        api_ref.append(url)
    else:
        other.append(url)

print(f"\nBy section:")
print(f"  Developer Guide (agent-sdk, agents-and-tools): {len(dev_guide)}")
if dev_guide:
    for url in dev_guide[:3]:
        print(f"    - {url}")
    if len(dev_guide) > 3:
        print(f"    ... and {len(dev_guide) - 3} more")

print(f"  API Reference: {len(api_ref)}")
if api_ref:
    for url in api_ref[:3]:
        print(f"    - {url}")
    if len(api_ref) > 3:
        print(f"    ... and {len(api_ref) - 3} more")

print(f"  Resources: {len(resources)}")
if resources:
    for url in resources[:3]:
        print(f"    - {url}")
    if len(resources) > 3:
        print(f"    ... and {len(resources) - 3} more")

print(f"  Other: {len(other)}")
if other:
    for url in other[:3]:
        print(f"    - {url}")
    if len(other) > 3:
        print(f"    ... and {len(other) - 3} more")
