import pytest
from backend.refinement.analyzer import RefinementAnalyzer, RefinementDecision

@pytest.fixture
def analyzer():
    return RefinementAnalyzer()

# Sample data for testing
TABLE_LIKE_TEXT = """
    Product    | Price | In Stock
    -----------|-------|---------
    Apples     | 1.50  | Yes
    Oranges    | 2.00  | No
    Grapes     | 3.25  | Yes
    Kiwis      | 2.75  | Yes
    Pineapples | 5.00  | Yes
"""

PROSE_TEXT = """
    This is a standard paragraph of text. It contains words and sentences, but it does not have the regular, columnar structure of a table. It is meant to simulate the kind of content that should not trigger the table detection heuristic. The lines have varying lengths and there is a low density of numerical characters.
"""

def test_analyzer_identifies_table_like_text(analyzer):
    """
    Tests that the heuristic correctly identifies a text block that is a table.
    """
    initial_result = {
        "key_sections": [
            {"title": "Sales Data", "content": TABLE_LIKE_TEXT * 10} # Multiply to meet length threshold
        ]
    }
    decision = analyzer.analyze_for_missed_tables(initial_result)
    assert decision.should_refine is True
    assert decision.target_section_id is not None
    assert decision.strategy == "TABLE_FOCUS"

def test_analyzer_ignores_prose_text(analyzer):
    """
    Tests that the heuristic correctly ignores a text block that is just prose.
    """

    initial_result = {
        "key_sections": [
            {"title": "Introduction", "content": PROSE_TEXT}
        ]
    }
    decision = analyzer.analyze_for_missed_tables(initial_result)
    assert decision.should_refine is False
    assert decision.target_section_id is None

def test_analyzer_handles_short_text(analyzer):
    """
    Tests that the analyzer ignores text that is too short to be a table.
    """
    initial_result = {
        "key_sections": [
            {"title": "Short Section", "content": "This is too short."}
        ]
    }
    decision = analyzer.analyze_for_missed_tables(initial_result)
    assert decision.should_refine is False

def test_analyzer_handles_no_key_sections(analyzer):
    """
    Tests that the analyzer handles input with no key_sections gracefully.
    """
    initial_result = {"tables": []}
    decision = analyzer.analyze_for_missed_tables(initial_result)
    assert decision.should_refine is False
