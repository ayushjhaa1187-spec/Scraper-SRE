import pytest
from backend.app.repair import get_dom_context, generate_fix_prompt, mock_llm_repair

def test_get_dom_context_found():
    html = '<html><body><div class="container"><span class="price">$10</span></div></body></html>'
    selector = '.price'
    context = get_dom_context(html, selector)
    assert '<div class="container">' in context
    assert '<span class="price">$10</span>' in context

def test_get_dom_context_not_found():
    html = '<html><body><div class="container"><span class="title">Item</span></div></body></html>'
    selector = '.price'
    context = get_dom_context(html, selector)
    assert context == "Element not found"

def test_generate_fix_prompt():
    old_html = '<html><body><div class="item"><span class="price">$10</span></div></body></html>'
    new_html = '<html><body><div class="item"><span class="price-v2">$10</span></div></body></html>'
    prompt = generate_fix_prompt(old_html, new_html, ".price", "price")

    assert "Field Name: price" in prompt
    assert "Old Selector: .price" in prompt
    assert '<span class="price">$10</span>' in prompt
    assert '<span class="price-v2">$10</span>' in prompt

def test_mock_llm_repair_success():
    prompt = 'We need to fix the selector, the new one has class="price-v2".'
    fix = mock_llm_repair(prompt)
    assert fix == ".price-v2"

def test_mock_llm_repair_failure():
    prompt = 'We need to fix the selector, the new one is completely different.'
    fix = mock_llm_repair(prompt)
    assert fix == "unable-to-fix"
