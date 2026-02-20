import difflib
from bs4 import BeautifulSoup
from typing import Optional, Tuple

def get_dom_context(html: str, selector: str) -> str:
    """
    Extracts a snippet of the DOM around the selector.
    """
    soup = BeautifulSoup(html, 'lxml')
    element = soup.select_one(selector)
    if element:
        # Get parent to give context
        return str(element.parent)
    return "Element not found"

def generate_fix_prompt(
    old_html: str,
    new_html: str,
    broken_selector: str,
    field_name: str
) -> str:
    """
    Constructs the prompt for the LLM to repair the selector.
    """

    # In a real system, we'd use more sophisticated diffing to find where the element *moved* to.
    # For now, we just provide the old context (what it looked like) and the new context (the whole body or a relevant section).

    old_context = get_dom_context(old_html, broken_selector)

    # Truncate new_html to avoid token limits in a real scenario,
    # but for this demo we assume small snippets.
    new_context = new_html[:2000]

    prompt = f"""
You are an expert web scraping engineer. A CSS selector has broken due to a website update.
Your goal is to provide a fixed CSS selector.

Field Name: {field_name}
Old Selector: {broken_selector}

--- OLD DOM CONTEXT (When it worked) ---
{old_context}

--- NEW DOM (Current failure) ---
{new_context}

--- INSTRUCTIONS ---
1. Analyze the changes in the DOM.
2. Identify the element that corresponds to the data we want (based on the old context).
3. Generate a robust CSS selector for this element in the new DOM.
4. Return ONLY the new selector.
"""
    return prompt

def mock_llm_repair(prompt: str) -> str:
    """
    Simulates the LLM response.
    If the prompt contains our specific demo scenario, return the correct fix.
    """
    if 'class="price-v2"' in prompt:
        return ".price-v2"
    return "unable-to-fix"
