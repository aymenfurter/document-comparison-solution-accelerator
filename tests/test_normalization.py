import pytest
from bs4 import BeautifulSoup
from app.services.normalization import HTMLNormalizer, normalize_html, extract_text_blocks

@pytest.fixture
def normalizer():
    return HTMLNormalizer()

def test_remove_comments(normalizer):
    html = '''
    <div>Content</div>
    <!-- Comment to remove -->
    <p>More content</p>
    '''
    soup = BeautifulSoup(html, 'html.parser')
    normalizer._remove_comments(soup)
    assert '<!-- Comment to remove -->' not in str(soup)

def test_normalize_whitespace(normalizer):
    html = '''
    <p>Multiple    spaces    here</p>
    <p>New
    lines   too</p>
    '''
    soup = BeautifulSoup(html, 'html.parser')
    normalizer._normalize_whitespace(soup)
    assert 'Multiple spaces here' in str(soup)
    assert 'New lines too' in str(soup)

def test_normalize_headings(normalizer):
    html = '''
    <h1>1. First Heading</h1>
    <h2>1.1 Second Heading</h2>
    <h3>1.1.1. Third Heading</h3>
    '''
    soup = BeautifulSoup(html, 'html.parser')
    normalizer._normalize_headings(soup)
    result = str(soup)
    assert 'First Heading' in result
    assert 'Second Heading' in result
    assert 'Third Heading' in result
    assert '1.1.1.' not in result

def test_normalize_quotes_and_spaces(normalizer):
    html = '''
    <p>"Smart quotes" and 'single quotes'</p>
    <p>En–dash and em—dash</p>
    '''
    soup = BeautifulSoup(html, 'html.parser')
    normalizer._normalize_quotes_and_spaces(soup)
    result = str(soup)
    assert '"Smart quotes"' in result
    assert "'single quotes'" in result

def test_normalize_lists(normalizer):
    html = '''
    <ul>
        <li>• First item</li>
        <li>- Second item</li>
        <li>▪ Third item</li>
    </ul>
    '''
    soup = BeautifulSoup(html, 'html.parser')
    normalizer._normalize_lists(soup)
    result = str(soup)
    assert 'First item' in result
    assert 'Second item' in result
    assert 'Third item' in result
    assert '•' not in result
    assert '-' not in result
    assert '▪' not in result

def test_remove_style_attributes(normalizer):
    html = '''
    <div style="color: red;" class="test">Content</div>
    <p style="font-size: 12px">Text</p>
    '''
    soup = BeautifulSoup(html, 'html.parser')
    normalizer._remove_style_attributes(soup)
    result = str(soup)
    assert 'style=' not in result
    assert 'class=' not in result

def test_normalize_links(normalizer):
    html = '''
    <a href="http://example.com" style="color: blue" class="link" target="_blank">Link</a>
    '''
    soup = BeautifulSoup(html, 'html.parser')
    normalizer._normalize_links(soup)
    result = str(soup)
    assert 'href="http://example.com"' in result
    assert 'style=' not in result
    assert 'class=' not in result
    assert 'target=' not in result

def test_full_html_normalization():
    html = '''
    <!-- Comment -->
    <h1>1. Main Heading</h1>
    <p style="color: red">This is "quoted" text with   extra   spaces</p>
    <ul>
        <li>• First item</li>
        <li>Second item</li>
    </ul>
    <a href="http://example.com" style="color: blue">Link</a>
    '''
    result = normalize_html(html)
    assert '<!-- Comment -->' not in result
    assert 'Main Heading' in result
    assert 'style=' not in result
    assert '"quoted"' in result
    assert '  ' not in result
    assert '•' not in result
    assert 'href="http://example.com"' in result

def test_extract_text_blocks():
    html = '''
    <h1>Heading</h1>
    <p>Paragraph 1</p>
    <ul>
        <li>List item 1</li>
        <li>List item 2</li>
    </ul>
    <p>Paragraph 2</p>
    '''
    blocks = extract_text_blocks(html)
    assert len(blocks) == 5
    assert blocks[0] == 'Heading'
    assert blocks[1] == 'Paragraph 1'
    assert blocks[2] == 'List item 1'
    assert blocks[3] == 'List item 2'
    assert blocks[4] == 'Paragraph 2'

def test_empty_input():
    assert normalize_html("") == ""
    assert extract_text_blocks("") == []

def test_malformed_html():
    html = "<p>Unclosed paragraph <span>Unclosed span"
    result = normalize_html(html)
    assert "Unclosed paragraph" in result
    assert "Unclosed span" in result

def test_nested_elements():
    html = '''
    <div>
        <h1>Heading <span>with inline</span> element</h1>
        <p>Paragraph <strong>with</strong> formatting</p>
    </div>
    '''
    result = normalize_html(html)
    assert "Heading with inline element" in result
    assert "Paragraph with formatting" in result

def test_table_normalization():
    html = '''
    <table>
        <tr>
            <th>Header 1</th>
            <th>Header 2</th>
        </tr>
        <tr>
            <td>Data 1</td>
            <td>Data 2</td>
        </tr>
    </table>
    '''
    result = normalize_html(html)
    assert "Header 1" in result
    assert "Header 2" in result
    assert "Data 1" in result
    assert "Data 2" in result

def test_image_handling():
    html = '''
    <p>Text before image</p>
    <img src="image.jpg" alt="Test image" style="width: 100px;" />
    <p>Text after image</p>
    '''
    result = normalize_html(html)
    assert "Text before image" in result
    assert "Text after image" in result
    assert 'alt="Test image"' in result
    assert 'style="width: 100px;"' not in result

def test_complex_formatting():
    html = '''
    <div class="section">
        <h2>2.1 Section Title</h2>
        <p>Text with <em>emphasis</em> and <strong>strong</strong> formatting</p>
        <p>Text with <sup>superscript</sup> and <sub>subscript</sub></p>
        <p>Text with <mark>highlighting</mark> and <u>underlining</u></p>
    </div>
    '''
    result = normalize_html(html)
    assert "Section Title" in result
    assert "Text with emphasis and strong formatting" in result
    assert "Text with superscript and subscript" in result
    assert "Text with highlighting and underlining" in result

def test_footnotes_and_endnotes():
    html = '''
    <p>Main text<sup class="footnote">1</sup></p>
    <div class="footnotes">
        <p id="fn1">1. This is a footnote</p>
    </div>
    '''
    result = normalize_html(html)
    assert "Main text" in result
    assert "This is a footnote" in result
    assert 'class="footnote"' not in result

def test_document_structure():
    html = '''
    <div class="header">Header content</div>
    <div class="main">
        <h1>1. Document Title</h1>
        <div class="section">
            <h2>1.1 First Section</h2>
            <p>First paragraph</p>
        </div>
    </div>
    <div class="footer">Footer content</div>
    '''
    result = normalize_html(html)
    assert "Header content" in result
    assert "Document Title" in result
    assert "First Section" in result
    assert "Footer content" in result
    assert "1.1" not in result

def test_list_variations():
    html = '''
    <ol type="1">
        <li>Numbered item 1</li>
        <li>Numbered item 2</li>
    </ol>
    <ul style="list-style-type: square;">
        <li>• Bullet point 1</li>
        <li>◦ Bullet point 2</li>
    </ul>
    <ol type="a">
        <li>Alphabetical item a</li>
        <li>Alphabetical item b</li>
    </ol>
    '''
    result = normalize_html(html)
    assert "Numbered item 1" in result
    assert "Bullet point 1" in result
    assert "Alphabetical item a" in result
    assert "•" not in result
    assert "◦" not in result

def test_table_of_contents():
    html = '''
    <div class="toc">
        <p class="toc-entry">1. Introduction....1</p>
        <p class="toc-entry">2. Methods....5</p>
        <p class="toc-entry">3. Results....10</p>
    </div>
    '''
    result = normalize_html(html)
    assert "Introduction" in result
    assert "Methods" in result
    assert "Results" in result
    assert "....1" not in result
    assert "....5" not in result
    assert "....10" not in result

def test_special_characters():
    html = '''
    <p>Text with special characters: © ® ™ € £ ¥</p>
    <p>Mathematical symbols: ± ∑ ∏ ≠ ≤ ≥</p>
    <p>Arrows and bullets: → ← ↑ ↓ • ◦ ▪</p>
    '''
    result = normalize_html(html)
    assert "Text with special characters" in result
    assert "Mathematical symbols" in result
    assert "Arrows and bullets" in result
    # Special characters should be preserved
    assert "©" in result
    assert "€" in result
    assert "→" in result

def test_mixed_content_block():
    html = '''
    <div class="section">
        <h2>Results Analysis</h2>
        <p>Key findings:</p>
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Accuracy</td><td>95%</td></tr>
        </table>
        <img src="graph.png" alt="Results graph" />
        <ul>
            <li>Finding 1</li>
            <li>Finding 2</li>
        </ul>
        <p>Footnote<sup>1</sup></p>
    </div>
    '''
    result = normalize_html(html)
    assert "Results Analysis" in result
    assert "Key findings" in result
    assert "Accuracy" in result
    assert "95%" in result
    assert "Finding 1" in result
    assert "Finding 2" in result
    assert "Footnote" in result

if __name__ == "__main__":
    pytest.main([__file__])