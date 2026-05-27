"""Data models for papers, references, and citations."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Reference:
    """A single bibliographic reference."""
    index: int
    bib_key: Optional[str] = None
    raw_text: str = ""
    entry_type: Optional[str] = None
    title: str = ""
    authors: str = ""
    year: Optional[str] = None
    venue: str = ""
    doi: Optional[str] = None
    volume: Optional[str] = None
    number: Optional[str] = None
    pages: Optional[str] = None
    url: Optional[str] = None
    issues: List[str] = field(default_factory=list)


@dataclass
class Citation:
    """An in-text citation with its context."""
    ref_indices: List[int]
    context_before: str = ""
    context_after: str = ""
    raw_marker: str = ""
    bib_keys: List[str] = field(default_factory=list)


@dataclass
class Paper:
    """Parsed paper content."""
    title: str = ""
    abstract: str = ""
    keywords: str = ""
    references: List[Reference] = field(default_factory=list)
    citations: List[Citation] = field(default_factory=list)
    body_text: str = ""
    source_type: str = ""  # "latex" or "pdf"
