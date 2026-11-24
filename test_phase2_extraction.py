import pytest
from unittest.mock import MagicMock
from backend.extraction.ai_extractor import (
    repair_and_parse_json,
    separate_amount_and_currency,
    normalize_field_casing,
    _extract_batch_chunk
)

def test_json_repair_cases():
    # Markdown fence
    res1 = repair_and_parse_json("```json\n{\"data_type\": \"records\", \"records\": [{\"id\": \"C-01\"}]}\n```")
    assert res1 is not None
    assert res1["records"][0]["id"] == "C-01"

    # Trailing commas
    res2 = repair_and_parse_json('{"data_type": "records", "records": [{"id": "C-02",},],}')
    assert res2 is not None
    assert res2["records"][0]["id"] == "C-02"

    # Unclosed brackets/braces (truncated stream)
    res3 = repair_and_parse_json('{"data_type": "records", "records": [{"id": "C-03", "name": "Test"}')
    assert res3 is not None
    assert res3["records"][0]["id"] == "C-03"


def test_amount_and_currency_separation():
    amt, curr = separate_amount_and_currency("$1,250.75")
    assert amt == 1250.75
    assert curr == "USD"

    amt, curr = separate_amount_and_currency("8,037.75 SAR")
    assert amt == 8037.75
    assert curr == "SAR"

    amt, curr = separate_amount_and_currency("₹ 45,000")
    assert amt == 45000.0
    assert curr == "INR"


def test_casing_rules():
    # ID and codes must NOT be Title Cased
    assert normalize_field_casing("store_id", "STR_BLR_001") == "STR_BLR_001"
    assert normalize_field_casing("sku", "sku-apple-iphone-13") == "sku-apple-iphone-13"
    assert normalize_field_casing("vin", "1HGCR2F83HA000000") == "1HGCR2F83HA000000"
    
    # Emails should be normalized to lowercase
    assert normalize_field_casing("email", "John.Doe@Enterprise.Org") == "john.doe@enterprise.org"

    # Acronyms preserved
    assert normalize_field_casing("country", "USA") == "USA"


def test_extract_batch_chunk_reconciliation():
    mock_client = MagicMock()
    mock_completion = MagicMock()
    # Mock LLM returning 2 records when 3 were expected
    mock_completion.choices = [
        MagicMock(message=MagicMock(content='{"data_type": "records", "records": [{"id": "A1"}, {"id": "A2"}]}'))
    ]
    mock_client.chat.completions.create.return_value = mock_completion

    result = _extract_batch_chunk(
        client=mock_client,
        batch_text="item 1\nitem 2\nitem 3",
        batch_index=0,
        expected_count=3,
        models=["test-model"]
    )

    assert result["expected_count"] == 3
    assert result["extracted_count"] == 2
    assert result["status"] == "partial"
    assert result["skipped_count"] == 1
    assert len(result["records"]) == 2
    assert result["records"][0]["_source_batch"] == 0
