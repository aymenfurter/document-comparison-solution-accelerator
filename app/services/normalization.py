from bs4 import BeautifulSoup, Comment
import re
from typing import Dict, List
import logging
import unicodedata

logger = logging.getLogger(__name__)

class HTMLNormalizer:
    HEADING_PATTERN = re.compile(r'^\d+\.[\d\.]*\s+')
    WHITESPACE_PATTERN = re.compile(r'\s+')
    TOC_PAGE_PATTERN = re.compile(r'\.{2,}\d+$')  # Pattern for "....123" at end of line
    
    def __init__(self):
        self.style_mapping: Dict[str, str] = {}
        self.heading_counter: Dict[str, int] = {}

    def normalize_html(self, html_content: str) -> str:
        """
        Normalize HTML content for meaningful comparison
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            self._remove_comments(soup)
            self._normalize_whitespace(soup)
            self._normalize_toc(soup)  # Add TOC normalization before headings
            self._normalize_headings(soup)
            self._normalize_quotes_and_spaces(soup)
            self._normalize_lists(soup)
            self._remove_style_attributes(soup)
            self._normalize_links(soup)
            
            return str(soup)
        except Exception as e:
            logger.error(f"HTML normalization failed: {str(e)}")
            raise

    def _remove_comments(self, soup: BeautifulSoup) -> None:
        """Remove HTML comments"""
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

    def _normalize_whitespace(self, soup: BeautifulSoup) -> None:
        """Normalize whitespace in text nodes"""
        for text in soup.find_all(string=True):
            if text.parent.name not in ['script', 'style']:
                # Normalize the text while preserving single spaces
                normalized = ' '.join(text.strip().split())
                text.replace_with(normalized)

        # Handle nested elements by joining their text content
        for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']):
            parts = []
            for child in tag.children:
                if isinstance(child, str):
                    parts.append(child.strip())
                else:
                    parts.append(child.get_text().strip())
            tag.string = ' '.join(filter(None, parts))

    def _normalize_toc(self, soup: BeautifulSoup) -> None:
        """Normalize table of contents entries"""
        for entry in soup.find_all(class_='toc-entry'):
            text = entry.get_text().strip()
            # Remove page numbers and dots
            cleaned_text = self.TOC_PAGE_PATTERN.sub('', text)
            # Remove numbering from TOC entries
            cleaned_text = self.HEADING_PATTERN.sub('', cleaned_text)
            entry.string = cleaned_text.strip()

    def _normalize_headings(self, soup: BeautifulSoup) -> None:
        """Remove numbering from headings and normalize format"""
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            text = heading.get_text().strip()
            # Remove heading numbers (e.g., "1.2.3 Title" -> "Title")
            normalized_text = self.HEADING_PATTERN.sub('', text)
            heading.string = normalized_text

    def _normalize_quotes_and_spaces(self, soup: BeautifulSoup) -> None:
        """Normalize quotes and spaces to their basic forms"""
        for text in soup.find_all(string=True):
            if text.parent.name not in ['script', 'style']:
                normalized = text.string
                # Convert smart quotes to straight quotes
                normalized = normalized.replace('"', '"').replace('"', '"')
                normalized = normalized.replace('\'', "'").replace('\'', "'")
                normalized = unicodedata.normalize('NFKC', normalized)
                # Only replace multiple spaces with single space
                normalized = ' '.join(normalized.split())
                text.replace_with(normalized)

    def _normalize_lists(self, soup: BeautifulSoup) -> None:
        """Normalize list markers and spacing"""
        for list_item in soup.find_all('li'):
            text = list_item.get_text().strip()
            # Remove list markers if present
            text = re.sub(r'^[•⁃◦▪-]\s*', '', text)
            list_item.string = text

    def _remove_style_attributes(self, soup: BeautifulSoup) -> None:
        """Remove style attributes while preserving essential formatting"""
        for tag in soup.find_all(True):
            if 'style' in tag.attrs:
                del tag.attrs['style']
            if 'class' in tag.attrs:
                del tag.attrs['class']

    def _normalize_links(self, soup: BeautifulSoup) -> None:
        """Normalize links to preserve href but remove other attributes"""
        for link in soup.find_all('a'):
            href = link.get('href')
            link.attrs.clear()
            if href:
                link['href'] = href

def normalize_html(html_content: str) -> str:
    """Public interface for HTML normalization"""
    if not html_content:
        return ""
    normalizer = HTMLNormalizer()
    return normalizer.normalize_html(html_content)

def extract_text_blocks(normalized_html: str) -> List[str]:
    """Extract text blocks from normalized HTML"""
    if not normalized_html:
        return []
        
    soup = BeautifulSoup(normalized_html, 'html.parser')
    blocks = []
    
    for block in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li']):
        text = block.get_text().strip()
        if text:
            blocks.append(text)
    
    return blocks
