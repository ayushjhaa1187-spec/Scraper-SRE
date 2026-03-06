import pytest
import sys
import unittest.mock
from unittest.mock import patch, MagicMock

# Apply patch.dict at the top as requested, and stop it during module teardown
# This ensures we satisfy both the memory instruction to apply it at the top before import,
# and the reviewer's concern about test pollution globally.

_patcher = unittest.mock.patch.dict('sys.modules', {
    'bs4': MagicMock(),
    'lxml': MagicMock(),
    'fastapi': MagicMock(),
    'requests': MagicMock()
})
_patcher.start()

from app.repair import get_dom_context, generate_fix_prompt, mock_llm_repair

def teardown_module(module):
    """Teardown any module-level mock patches."""
    _patcher.stop()

def test_get_dom_context_found():
    html = '<html><body><div class="container"><p class="price-v2">$10.00</p></div></body></html>'
    selector = '.price-v2'

    with patch('app.repair.BeautifulSoup') as mock_bs:
        mock_soup = MagicMock()
        mock_bs.return_value = mock_soup

        mock_element = MagicMock()
        mock_element.parent = '<div class="container"><p class="price-v2">$10.00</p></div>'
        mock_soup.select_one.return_value = mock_element

        context = get_dom_context(html, selector)

        mock_bs.assert_called_once_with(html, 'lxml')
        mock_soup.select_one.assert_called_once_with(selector)

        assert '<div class="container">' in context
        assert '<p class="price-v2">$10.00</p>' in context

def test_get_dom_context_not_found():
    html = '<html><body><div class="container"></div></body></html>'
    selector = '.price-v2'

    with patch('app.repair.BeautifulSoup') as mock_bs:
        mock_soup = MagicMock()
        mock_bs.return_value = mock_soup
        mock_soup.select_one.return_value = None

        context = get_dom_context(html, selector)

        mock_bs.assert_called_once_with(html, 'lxml')
        mock_soup.select_one.assert_called_once_with(selector)
        assert context == "Element not found"

def test_generate_fix_prompt_truncates_new_html():
    old_html = '<html><body><div class="container"><p class="price">$10.00</p></div></body></html>'
    new_html = '<body>' + 'a' * 3000 + '</body>'
    broken_selector = '.price'
    field_name = 'price'

    with patch('app.repair.get_dom_context') as mock_get_context:
        mock_get_context.return_value = '<div class="container"><p class="price">$10.00</p></div>'

        prompt = generate_fix_prompt(old_html, new_html, broken_selector, field_name)

        mock_get_context.assert_called_once_with(old_html, broken_selector)

        assert old_html[:10] not in prompt # old html shouldn't be fully embedded except the context

        # It should include the old context which is the parent div
        assert '<div class="container">' in prompt
        assert '<p class="price">$10.00</p>' in prompt

        # Check prompt contains field name and selector
        assert 'Field Name: price' in prompt
        assert 'Old Selector: .price' in prompt

        # Verify new html is truncated
        assert len(prompt) < len(new_html)
        assert 'a' * 1900 in prompt

def test_mock_llm_repair():
    assert mock_llm_repair('Some prompt with class="price-v2" in it') == '.price-v2'
    assert mock_llm_repair('Some prompt without the specific class') == 'unable-to-fix'
