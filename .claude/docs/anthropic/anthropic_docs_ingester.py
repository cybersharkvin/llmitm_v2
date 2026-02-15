"""
Deterministic Python script to ingest Anthropic documentation.
Fetches llms.txt and llms-full.txt, creates organized markdown files.

Three phases:
1. Parse llms.txt, create empty .md files with snake_case names
2. Parse llms-full.txt, populate files with content
3. Generate CLAUDE.md index files with cross-links
"""

import re
import sys
from pathlib import Path
from typing import Optional, Literal, Callable, Any
from urllib.request import urlopen, Request
from urllib.error import URLError
from functools import wraps

from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# Section Extraction Decorators (Pluggable Section-Specific Logic)
# ============================================================================

def section_extractor(section_name: str) -> Callable:
    """
    Decorator for section-specific extraction logic.
    Allows pluggable customization per section without modifying core logic.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(ingester: Any, section_content: str) -> list:
            return func(ingester, section_content)
        wrapper.section = section_name
        return wrapper
    return decorator


# ============================================================================
# Data Models (Pydantic)
# ============================================================================

class Bullet(BaseModel):
    """Represents a single bullet from llms.txt"""
    link_text: str
    url: str
    description: str = ""
    section: Literal["api_reference", "developer_guide", "resources"]


class FileMetadata(BaseModel):
    """Metadata for a generated .md file"""
    filename: str
    link_text: str
    description: str = ""
    url: str
    section: Literal["api_reference", "developer_guide", "resources"]


class DocumentationState(BaseModel):
    """State storage across all three phases"""
    bullets_by_section: dict[str, list[Bullet]] = Field(default_factory=dict)
    metadata_by_file: dict[str, FileMetadata] = Field(default_factory=dict)
    content_map: dict[str, str] = Field(default_factory=dict)  # description → content
    missing_urls: dict[str, list[str]] = Field(default_factory=dict)  # section → [urls]
    found_urls: set[str] = Field(default_factory=set)  # URLs that had content


class DocumentationIngester(BaseModel):
    """Main orchestrator for all three phases with pluggable section extractors"""

    base_dir: Path = Path(".claude/docs/anthropic")
    llms_txt_url: str = "https://platform.claude.com/llms.txt"
    llms_full_txt_url: str = "https://platform.claude.com/llms-full.txt"

    # State storage across phases
    state: DocumentationState = Field(default_factory=DocumentationState)

    # Section extractors (pluggable per section)
    section_extractors: dict[str, Callable] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(self, **kwargs: Any) -> None:
        """Initialize with default section extractors"""
        super().__init__(**kwargs)
        # Register default extractors (all sections use same logic by default)
        # Each lambda captures the section_name for the bullet parser
        self.section_extractors = {
            "api_reference": lambda content: self._extract_bullets_from_section_default(content, "api_reference"),
            "developer_guide": lambda content: self._extract_bullets_from_section_default(content, "developer_guide"),
            "resources": lambda content: self._extract_bullets_from_section_default(content, "resources"),
        }

    def register_section_extractor(self, section_name: str, extractor: Callable) -> None:
        """
        Register a custom extractor for a specific section.
        Useful for section-specific parsing logic.

        Example:
            def custom_api_ref_extractor(content: str) -> list[Bullet]:
                # Custom parsing logic for API Reference
                return [...]

            ingester.register_section_extractor("api_reference", custom_api_ref_extractor)
        """
        self.section_extractors[section_name] = extractor

    def run(self) -> bool:
        """Execute all three phases"""
        print("[*] Starting Anthropic documentation ingestion...")

        try:
            print("\n[PHASE 1] Parsing llms.txt and creating empty files...")
            self.phase_1_create_files()

            print("\n[PHASE 2] Parsing llms-full.txt and populating files...")
            self.phase_2_populate_files()

            print("\n[PHASE 2.5] Consolidating language-specific variants...")
            self.phase_2_5_consolidate_variants()

            print("\n[PHASE 3] Generating CLAUDE.md index files...")
            self.phase_3_generate_indexes()

            print("\n[✓] All phases completed successfully!")
            self.validate_output()  # Prints validation results and summary
            return True

        except Exception as e:
            print(f"\n[✗] Error: {e}", file=sys.stderr)
            return False

    # ========================================================================
    # PHASE 1: Parse llms.txt, Create Empty Files
    # ========================================================================

    def phase_1_create_files(self) -> None:
        """
        Phase 1: Load local llms.txt, parse sections, extract bullets,
        generate filenames, create empty .md files.
        """
        llms_path = self.base_dir / "llms.txt"
        if not llms_path.exists():
            raise FileNotFoundError(f"Local copy not found: {llms_path}. Download with: curl -H 'User-Agent: Mozilla/5.0' https://platform.claude.com/llms.txt > {llms_path}")

        llms_txt = llms_path.read_text(encoding='utf-8')
        self._parse_llms_txt(llms_txt)
        self._create_empty_files()

    def _fetch_url(self, url: str) -> str:
        """Fetch URL content, return as string"""
        try:
            req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urlopen(req) as response:
                return response.read().decode('utf-8')
        except URLError as e:
            raise URLError(f"Failed to fetch {url}: {e}") from e

    def _parse_llms_txt(self, content: str) -> None:
        """
        Parse llms.txt into sections and bullets.
        Uses pluggable section extractors for section-specific logic.
        Populates self.state.bullets_by_section and self.state.metadata_by_file.
        """
        sections = self._split_into_sections(content)

        for section_key, section_content in sections.items():
            # Use registered extractor for this section (or default)
            extractor = self.section_extractors.get(
                section_key,
                self._extract_bullets_from_section_default
            )
            bullets = extractor(section_content)
            self.state.bullets_by_section[section_key] = bullets

    def _split_into_sections(self, content: str) -> dict[str, str]:
        """Split llms.txt content into three sections"""
        sections = {}
        section_headers = {
            "### API Reference": "api_reference",
            "### Developer Guide": "developer_guide",
            "### Resources": "resources"
        }

        for header, section_key in section_headers.items():
            pattern = re.escape(header) + r"\n(.*?)(?=\n### |\Z)"
            match = re.search(pattern, content, re.DOTALL)
            if match:
                sections[section_key] = match.group(1).strip()

        return sections

    def _extract_bullets_from_section_default(self, section_content: str, section_name: str = "api_reference") -> list[Bullet]:
        """
        Default bullet extraction logic for any section.
        Can be overridden by custom extractors registered via section_extractors dict.
        """
        bullets = []
        for line in section_content.split('\n'):
            bullet = self._parse_bullet_line(line, section_name)
            if bullet:
                bullets.append(bullet)
        return bullets

    def _parse_bullet_line(self, line: str, section: str) -> Optional[Bullet]:
        """Parse a single bullet line into Bullet object"""
        line = line.strip()
        if not line.startswith("- ["):
            return None

        # Pattern: - [link_text](url) or - [link_text](url) - description
        pattern = r"^-\s+\[(.*?)\]\((.*?)\)(?:\s+-\s+(.*))?$"
        match = re.match(pattern, line)

        if not match:
            return None

        link_text = match.group(1)
        url = match.group(2)
        description = match.group(3) or ""

        # Normalize URL: remove trailing .md and query params
        url = url.rstrip('/')
        if url.endswith('.md'):
            url = url[:-3]

        return Bullet(
            link_text=link_text,
            url=url,
            description=description.strip(),
            section=section  # type: ignore
        )

    def _to_snake_case(self, text: str) -> str:
        """Convert text to deterministic snake_case"""
        # Replace spaces, hyphens with underscores
        text = re.sub(r'[\s\-]+', '_', text)
        # Remove special characters (keep only alphanumeric and underscore)
        text = re.sub(r'[^a-zA-Z0-9_]', '', text)
        # Convert to lowercase
        text = text.lower()
        # Remove leading/trailing underscores
        text = text.strip('_')
        # Collapse multiple underscores
        text = re.sub(r'_+', '_', text)
        return text

    def _generate_filename(self, link_text: str, description: str) -> str:
        """Generate deterministic filename from link_text and description"""
        link_snake = self._to_snake_case(link_text)
        desc_snake = self._to_snake_case(description) if description else ""

        if desc_snake:
            filename = f"{link_snake}_{desc_snake}.md"
        else:
            filename = f"{link_snake}.md"

        return filename

    def _create_empty_files(self) -> None:
        """Create empty .md files in appropriate section folders"""
        for section_key, bullets in self.state.bullets_by_section.items():
            section_path = self._ensure_section_folder(section_key)

            for bullet in bullets:
                filename = self._generate_filename(bullet.link_text, bullet.description)
                filepath = section_path / filename

                # Create empty file
                filepath.touch()

                # Store metadata
                metadata = FileMetadata(
                    filename=filename,
                    link_text=bullet.link_text,
                    description=bullet.description,
                    url=bullet.url,
                    section=bullet.section  # type: ignore
                )
                self.state.metadata_by_file[filename] = metadata

    def _ensure_section_folder(self, section: str) -> Path:
        """Ensure section folder exists"""
        section_path = self.base_dir / section
        section_path.mkdir(parents=True, exist_ok=True)
        return section_path

    # ========================================================================
    # PHASE 2: Parse llms-full.txt, Populate Files
    # ========================================================================

    def phase_2_populate_files(self) -> None:
        """
        Phase 2: Load llms-full.txt from local file, build content map,
        populate all created .md files with content.
        """
        llms_full_path = self.base_dir / "llms-full.txt"
        if not llms_full_path.exists():
            raise FileNotFoundError(f"Local copy not found: {llms_full_path}. Download with: curl -H 'User-Agent: Mozilla/5.0' https://platform.claude.com/llms-full.txt > {llms_full_path}")

        llms_full_txt = llms_full_path.read_text(encoding='utf-8')
        self._build_content_map(llms_full_txt)
        self._populate_all_files()

    def _build_content_map(self, content: str) -> None:
        """
        Build map of description → content_block from llms-full.txt.
        Content blocks are delimited by '# Header' lines.
        Populates self.state.content_map.
        """
        self.state.content_map = self._extract_content_blocks(content)

    def _extract_content_blocks(self, content: str) -> dict[str, str]:
        """
        Extract all content blocks from llms-full.txt using URLs as keys.
        Each page has: URL: https://... line followed by content.
        Content ends at the next URL: line (or end of file).

        Note: Headers (#, ##, etc) that appear after the URL line are PART of the content,
        not boundaries.
        """
        blocks = {}
        lines = content.split('\n')

        # Find all URL: line positions
        url_positions = []
        for i, line in enumerate(lines):
            if line.startswith('URL:'):
                url_positions.append(i)

        # Extract content for each URL
        for idx, url_line_num in enumerate(url_positions):
            # Parse the URL
            url_line = lines[url_line_num].strip()
            url = url_line.replace('URL:', '').strip()

            # Normalize: remove trailing .md and query params
            url = url.rstrip('/')
            if url.endswith('.md'):
                url = url[:-3]

            # Content ends at next URL: line (or end of file)
            if idx + 1 < len(url_positions):
                content_end = url_positions[idx + 1]
            else:
                content_end = len(lines)

            # Content is between URL line and content_end (skip the URL line itself)
            content_lines = lines[url_line_num + 1:content_end]

            # Join and store with URL as key
            block_content = '\n'.join(content_lines).strip()
            blocks[url] = block_content

        return blocks

    def _populate_all_files(self) -> None:
        """
        Iterate self.state.metadata_by_file, match by URL to content_map,
        write content to each .md file. Only write if content found.
        Track missing URLs for reporting.
        """
        for filename, metadata in self.state.metadata_by_file.items():
            # Match by URL (most reliable method)
            content = self.state.content_map.get(metadata.url)

            if content:
                section_path = self.base_dir / metadata.section
                filepath = section_path / filename
                self._write_file_content(filepath, content)
                self.state.found_urls.add(metadata.url)
            else:
                # Track missing URL
                if metadata.section not in self.state.missing_urls:
                    self.state.missing_urls[metadata.section] = []
                self.state.missing_urls[metadata.section].append(metadata.url)

    def _write_file_content(self, filepath: Path, content: str) -> None:
        """Write content to file"""
        filepath.write_text(content, encoding='utf-8')

    def _match_description_to_content(self, description: str) -> Optional[str]:
        """Look up description in content_map, return content or None"""
        content = self.state.content_map.get(description)
        if not content:
            print(f"[⚠] Warning: No matching content for description: '{description}'")
        return content

    # ========================================================================
    # PHASE 3: Generate CLAUDE.md Index Files
    # ========================================================================

    def phase_2_5_consolidate_variants(self) -> None:
        """
        Phase 2.5: Consolidate language-specific API variants into single files.
        Merges cli, csharp, go, java, kotlin, php, python, ruby, terraform, typescript variants.
        Then deletes any remaining empty files.
        """
        api_ref = self.base_dir / "api_reference"
        if not api_ref.exists():
            return

        file_groups = {}
        for md_file in api_ref.glob('*.md'):
            if md_file.name == 'CLAUDE.md':
                continue

            name = md_file.name[:-3]
            base = re.sub(r'_(beta|cli|csharp|go|java|kotlin|php|python|ruby|terraform|typescript)$', '', name)

            if base not in file_groups:
                file_groups[base] = []
            file_groups[base].append(md_file)

        # Consolidate groups with multiple files
        for base, files in file_groups.items():
            if len(files) <= 1:
                continue

            # Use base filename
            base_file = api_ref / f'{base}.md'

            # Collect content from all files (skip empty ones)
            all_content = []
            files_sorted = sorted(files)

            # Start with base file if it exists and has content
            if base_file in files_sorted:
                base_content = base_file.read_text(encoding='utf-8')
                if base_content.strip():
                    all_content.append(base_content)
                other_files = [f for f in files_sorted if f != base_file]
            else:
                # Find first non-empty file to use as base
                other_files = []
                for f in files_sorted:
                    content = f.read_text(encoding='utf-8')
                    if content.strip():
                        if not all_content:
                            all_content.append(content)
                        else:
                            other_files.append(f)
                    else:
                        other_files.append(f)

            # Append variant content (skip empty)
            for variant_file in sorted([f for f in other_files if f not in (other_files if 'other_files' in locals() else [])]):
                content = variant_file.read_text(encoding='utf-8')
                if content.strip():
                    variant_name = variant_file.stem
                    lang = variant_name.split('_')[-1]
                    all_content.append(f"\n\n---\n## {lang.upper()}\n\n{content}")

            # Write consolidated if we have content
            if all_content:
                base_file.write_text('\n'.join(all_content), encoding='utf-8')

            # Delete all variants
            for variant_file in other_files:
                variant_file.unlink()

        # Delete any remaining empty files in all sections
        for section in ["api_reference", "developer_guide", "resources"]:
            section_path = self.base_dir / section
            if not section_path.exists():
                continue
            for md_file in section_path.glob('*.md'):
                if md_file.name == 'CLAUDE.md':
                    continue
                if md_file.stat().st_size == 0:
                    md_file.unlink()

    def phase_3_generate_indexes(self) -> None:
        """
        Phase 3: For each section, generate CLAUDE.md with cross-links
        to all .md files in that section.
        """
        sections = ["api_reference", "developer_guide", "resources"]

        for section in sections:
            self._generate_index_for_section(section)

    def _generate_index_for_section(self, section: str) -> None:
        """Generate CLAUDE.md index for a single section"""
        files = self._collect_files_in_section(section)
        index_content = self._build_index_content(section, files)
        self._write_index_file(section, index_content)

    def _collect_files_in_section(self, section: str) -> list[tuple[str, FileMetadata]]:
        """
        Scan filesystem for .md files in section folder (excluding CLAUDE.md and empty files),
        lookup metadata from self.state.metadata_by_file, return sorted list.
        """
        section_path = self.base_dir / section
        if not section_path.exists():
            return []

        files = []
        for md_file in sorted(section_path.glob('*.md')):
            if md_file.name == 'CLAUDE.md':
                continue

            # Skip empty files (they have no content from llms-full.txt)
            if md_file.stat().st_size == 0:
                continue

            filename = md_file.name
            if filename in self.state.metadata_by_file:
                metadata = self.state.metadata_by_file[filename]
                files.append((filename, metadata))

        return files

    def _build_index_content(self, section: str, files: list[tuple[str, FileMetadata]]) -> str:
        """Build markdown content for CLAUDE.md"""
        section_display = section.replace('_', ' ').title()
        lines = [
            f"# {section_display} Documentation Index\n",
            "This index provides cross-links to all documentation files in this section.\n"
        ]

        for filename, metadata in files:
            crosslink = self._build_crosslink(metadata, filename)
            lines.append(crosslink)

        return '\n'.join(lines)

    def _build_crosslink(self, metadata: FileMetadata, filename: str) -> str:
        """Build a single cross-link line for CLAUDE.md"""
        title_parts = [metadata.link_text]
        if metadata.description:
            title_parts.append(metadata.description)
        title = " - ".join(title_parts)

        # Extract first real paragraph as preview
        section_path = self.base_dir / metadata.section
        filepath = section_path / filename
        preview = ""

        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

                # Skip past headers, hr rules, and any JSX/HTML blocks
                in_tag_block = False
                content_lines = []

                for line in lines:
                    stripped = line.strip()

                    # Track if we're in a <Tag> block
                    if stripped.startswith('<') and not stripped.startswith('</'):
                        in_tag_block = True
                    if in_tag_block and stripped.startswith('</'):
                        in_tag_block = False
                        continue

                    # Skip if in tag block, empty, header, hr rule
                    if (in_tag_block or
                        not stripped or
                        stripped.startswith('#') or
                        all(c in '-*_' for c in stripped if c not in ' ')):
                        continue

                    # Collect actual paragraph content
                    content_lines.append(stripped)

                # Join first few lines into preview, limit to 80 chars
                if content_lines:
                    preview = ' '.join(content_lines[:5])[:80]

        if preview:
            return f"- [{title}](./{filename}) - {preview}"
        else:
            return f"- [{title}](./{filename})"

    def _write_index_file(self, section: str, content: str) -> None:
        """Write CLAUDE.md to section folder"""
        section_path = self.base_dir / section
        index_filepath = section_path / "CLAUDE.md"
        self._write_file_content(index_filepath, content)

    # ========================================================================
    # Validation
    # ========================================================================

    def validate_output(self) -> None:
        """
        Validate that all phases completed correctly.
        Calls all _check_* methods and prints summary.
        """
        self._print_summary()

    def _check_files_created(self) -> bool:
        """
        Verify .md files exist in each section (excluding CLAUDE.md and empty files).
        """
        sections = ["api_reference", "developer_guide", "resources"]
        total_files = 0
        for section in sections:
            section_path = self.base_dir / section
            if not section_path.exists():
                continue
            md_files = [f for f in section_path.glob('*.md')
                       if f.name != 'CLAUDE.md' and f.stat().st_size > 0]
            total_files += len(md_files)

        if total_files == 0:
            print("[✗] No files created")
            return False
        return True

    def _check_no_empty_files(self) -> bool:
        """
        Verify no .md files are empty (size > 0).
        Scans all .md files in all sections. Returns True if all have content.
        """
        for section in ["api_reference", "developer_guide", "resources"]:
            section_path = self.base_dir / section
            if not section_path.exists():
                continue

            for md_file in section_path.glob('*.md'):
                if md_file.name == 'CLAUDE.md':
                    continue

                if md_file.stat().st_size == 0:
                    print(f"[✗] Empty file: {md_file}")
                    return False

        return True

    def _check_indexes_exist(self) -> bool:
        """
        Verify CLAUDE.md exists in all three sections.
        Returns True if all exist.
        """
        for section in ["api_reference", "developer_guide", "resources"]:
            index_path = self.base_dir / section / "CLAUDE.md"
            if not index_path.exists():
                print(f"[✗] Missing index: {index_path}")
                return False
        return True

    def _print_summary(self) -> None:
        """Print execution summary with file counts per section and validation status"""
        files_ok = self._check_files_created()
        no_empty = self._check_no_empty_files()
        indexes_ok = self._check_indexes_exist()

        # Count files per section (created) vs expected (from llms.txt)
        created = {"api_reference": 0, "developer_guide": 0, "resources": 0}
        expected = {"api_reference": 0, "developer_guide": 0, "resources": 0}
        for metadata in self.state.metadata_by_file.values():
            expected[metadata.section] += 1

        # Count actual files on disk
        for section in ["api_reference", "developer_guide", "resources"]:
            section_path = self.base_dir / section
            if section_path.exists():
                created[section] = len([f for f in section_path.glob('*.md') if f.name != 'CLAUDE.md'])

        print("\n[✓] Validation Results:")
        if files_ok:
            total = sum(created.values())
            print(f"  ✓ {total} files created with content")
        else:
            print("  ✗ Some files missing")

        if no_empty:
            print("  ✓ No empty files detected")
        else:
            print("  ✗ Some files are empty")

        if indexes_ok:
            print("  ✓ All index files generated")
        else:
            print("  ✗ Some index files missing")

        print("\nFile Summary (Created vs Expected from llms.txt):")
        for section in ["api_reference", "developer_guide", "resources"]:
            exp = expected[section]
            crt = created[section]
            missing = exp - crt
            if missing > 0:
                print(f"  - {section}: {crt}/{exp} files ({missing} missing from llms-full.txt)")
            else:
                print(f"  - {section}: {crt}/{exp} files ✓")

        # Report missing URLs by section
        if self.state.missing_urls:
            print("\nMissing URLs (in llms.txt but not in llms-full.txt):")
            for section in ["api_reference", "developer_guide", "resources"]:
                if section in self.state.missing_urls and self.state.missing_urls[section]:
                    urls = self.state.missing_urls[section]
                    print(f"  {section}: {len(urls)} missing")
                    for url in sorted(urls)[:5]:  # Show first 5
                        print(f"    - {url}")
                    if len(urls) > 5:
                        print(f"    ... and {len(urls) - 5} more")

        if files_ok and no_empty and indexes_ok:
            print("\n[✓] All checks passed!")


# ============================================================================
# Main Entry Point
# ============================================================================

def main() -> int:
    """Main entry point"""
    ingester = DocumentationIngester()
    success = ingester.run()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
