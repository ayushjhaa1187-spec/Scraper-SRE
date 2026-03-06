import pytest
from app.repair import get_dom_context

def test_get_dom_context_found():
    html = """
    <html>
        <body>
            <div class="container">
                <p class="target">Hello World</p>
                <span>Other text</span>
            </div>
        </body>
    </html>
    """
    selector = ".target"
    result = get_dom_context(html, selector)

    assert '<div class="container">' in result
    assert '<p class="target">Hello World</p>' in result
    assert '<span>Other text</span>' in result

def test_get_dom_context_not_found():
    html = "<html><body><p>Hello</p></body></html>"
    selector = ".nonexistent"
    result = get_dom_context(html, selector)

    assert result == "Element not found"

def test_get_dom_context_no_parent():
    html = "<html><body><p>Hello</p></body></html>"
    selector = "html"
    result = get_dom_context(html, selector)

    # BeautifulSoup wraps the whole document in [document], which is the parent of html
    # So html.parent is the whole document itself
    assert "<html><body><p>Hello</p></body></html>" in result

def test_get_dom_context_nested():
    html = """
    <div id="main">
        <ul class="list">
            <li>Item 1</li>
            <li class="active">Item 2</li>
            <li>Item 3</li>
        </ul>
    </div>
    """
    selector = ".active"
    result = get_dom_context(html, selector)

    assert '<ul class="list">' in result
    assert '<li class="active">Item 2</li>' in result
    assert '<li>Item 1</li>' in result
    assert '<li>Item 3</li>' in result
    assert '<div id="main">' not in result
