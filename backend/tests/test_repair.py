import sys
from unittest.mock import MagicMock, patch

# Mocking missing dependencies globally to allow importing the module under test.
# This is necessary because 'backend.app.repair' has top-level imports of 'bs4'.
# We use patch.dict to ensure we're modifying sys.modules in a way that can be tracked,
# though since this is at the top level of the test module, it persists for the module's duration.
mock_bs4 = MagicMock()
mock_lxml = MagicMock()

with patch.dict('sys.modules', {'bs4': mock_bs4, 'lxml': mock_lxml}):
    from backend.app.repair import get_dom_context, generate_fix_prompt, mock_llm_repair

def test_get_dom_context_exists():
    mock_soup = MagicMock()
    mock_bs4.BeautifulSoup.return_value = mock_soup
    mock_element = MagicMock()
    mock_soup.select_one.return_value = mock_element
    mock_element.parent = MagicMock()
    mock_element.parent.__str__.return_value = "<div id='parent'><span id='target'>Hello</span></div>"

    html = "<html><body><div id='parent'><span id='target'>Hello</span></div></body></html>"
    selector = "#target"
    context = get_dom_context(html, selector)

    assert "<div id='parent'><span id='target'>Hello</span></div>" in context
    mock_bs4.BeautifulSoup.assert_called_with(html, 'lxml')
    mock_soup.select_one.assert_called_with(selector)

def test_get_dom_context_not_found():
    mock_soup = MagicMock()
    mock_bs4.BeautifulSoup.return_value = mock_soup
    mock_soup.select_one.return_value = None

    html = "<html><body><div id='parent'><span>Hello</span></div></body></html>"
    selector = "#missing"
    context = get_dom_context(html, selector)
    assert context == "Element not found"

def test_generate_fix_prompt_structure():
    mock_soup = MagicMock()
    mock_bs4.BeautifulSoup.return_value = mock_soup
    mock_element = MagicMock()
    mock_soup.select_one.return_value = mock_element
    mock_element.parent = MagicMock()
    mock_element.parent.__str__.return_value = "<div class=\"price\">$10</div>"

    old_html = "<html><body><div class='price'>$10</div></body></html>"
    new_html = "<html><body><div class='new-price'>$10</div></body></html>"
    broken_selector = ".price"
    field_name = "price"

    prompt = generate_fix_prompt(old_html, new_html, broken_selector, field_name)

    assert f"Field Name: {field_name}" in prompt
    assert f"Old Selector: {broken_selector}" in prompt
    assert "<div class=\"price\">$10</div>" in prompt
    assert new_html in prompt

def test_generate_fix_prompt_truncation():
    mock_soup = MagicMock()
    mock_bs4.BeautifulSoup.return_value = mock_soup
    mock_element = MagicMock()
    mock_soup.select_one.return_value = mock_element
    mock_element.parent = MagicMock()
    mock_element.parent.__str__.return_value = "context"

    old_html = "old"
    new_html = "A" * 3000
    broken_selector = ".selector"
    field_name = "field"

    prompt = generate_fix_prompt(old_html, new_html, broken_selector, field_name)

    # Check for truncation (default is 2000)
    assert "A" * 2000 in prompt
    assert "A" * 2001 not in prompt

def test_generate_fix_prompt_no_selector():
    mock_soup = MagicMock()
    mock_bs4.BeautifulSoup.return_value = mock_soup
    mock_soup.select_one.return_value = None

    old_html = "old"
    new_html = "new"
    broken_selector = ".missing"
    field_name = "field"

    prompt = generate_fix_prompt(old_html, new_html, broken_selector, field_name)

    assert "Element not found" in prompt

def test_mock_llm_repair_with_price_v2():
    prompt = 'some text class="price-v2" more text'
    result = mock_llm_repair(prompt)
    assert result == ".price-v2"

def test_mock_llm_repair_default():
    prompt = "generic prompt"
    result = mock_llm_repair(prompt)
    assert result == "unable-to-fix"
