"""
Test für automatische Quick-Reply-Generierung aus Enums.
"""

import pytest
from src.services.llm_extractor import _to_camel_case, _get_enum_quick_replies
from src.posts.models import ImpactAreaDto, Award, Intent, OfferCategory


class TestCamelCaseConversion:
    """Tests für SNAKE_CASE → camelCase Konvertierung."""

    def test_simple_word(self):
        assert _to_camel_case("LOCAL") == "local"
        assert _to_camel_case("WORLD") == "world"

    def test_two_words(self):
        assert _to_camel_case("IMPACT_AREA") == "impactArea"
        assert _to_camel_case("OFFER_CATEGORY") == "offerCategory"

    def test_three_plus_words(self):
        assert _to_camel_case("SUSTAINABLE_FINANCE") == "sustainableFinance"
        assert _to_camel_case("SUSTAINABLE_GOVERNANCE") == "sustainableGovernance"
        assert _to_camel_case("BEST_PRACTISE_CATEGORY") == "bestPractiseCategory"

    def test_already_lowercase(self):
        assert _to_camel_case("local") == "local"
        assert _to_camel_case("impact_area") == "impactArea"

    def test_empty_string(self):
        assert _to_camel_case("") == ""

    def test_single_char(self):
        assert _to_camel_case("A") == "a"


class TestEnumQuickReplies:
    """Tests für Enum-basierte Quick-Reply-Generierung."""

    def test_impact_area_generates_replies(self):
        """IMPACT_AREA sollte Quick Replies generieren."""
        result = _get_enum_quick_replies("IMPACT_AREA")
        assert isinstance(result, list)
        assert len(result) == 2  # default sample_size
        # Alle sollten das richtige Format haben
        assert all(r.startswith("impactArea.") for r in result)
        # Alle sollten valid enum values sein
        valid_values = ["local", "regional", "state", "country", "continent", "world"]
        assert all(any(v in r for v in valid_values) for r in result)

    def test_impact_area_sample_size_respected(self):
        """sample_size sollte respektiert werden."""
        result_1 = _get_enum_quick_replies("IMPACT_AREA", sample_size=1)
        assert len(result_1) == 1

        result_3 = _get_enum_quick_replies("IMPACT_AREA", sample_size=3)
        assert len(result_3) == 3

    def test_impact_area_capped_at_available(self):
        """Wenn sample_size > verfügbare Optionen, sollten alle zurückgegeben werden."""
        # ImpactAreaDto hat 6 Optionen
        result = _get_enum_quick_replies("IMPACT_AREA", sample_size=10)
        assert len(result) == 6  # capped

    def test_awards_only_two_options(self):
        """Award-Enum hat nur 2 Optionen."""
        result = _get_enum_quick_replies("AWARDS", sample_size=5)
        assert len(result) == 2
        assert "awards.initiator" in result
        assert "awards.award" in result

    def test_offer_category_generates_replies(self):
        """OFFER_CATEGORY sollte Quick Replies generieren."""
        result = _get_enum_quick_replies("OFFER_CATEGORY", sample_size=2)
        assert len(result) == 2
        assert all(r.startswith("offerCategory.") for r in result)

    def test_intent_generates_replies(self):
        """INTENT sollte Quick Replies generieren."""
        result = _get_enum_quick_replies("INTENT", sample_size=2)
        assert len(result) >= 1  # mindestens 1
        assert all(r.startswith("intent.") for r in result)

    def test_unsupported_field_returns_empty(self):
        """Unsupported Felder sollten leere Liste zurückgeben."""
        assert _get_enum_quick_replies("LOCATION") == []
        assert _get_enum_quick_replies("ONLINE") == []
        assert _get_enum_quick_replies("PERIOD") == []
        assert _get_enum_quick_replies("SDGS") == []

    def test_invalid_field_returns_empty(self):
        """Ungültige Feldnamen sollten leere Liste zurückgeben."""
        assert _get_enum_quick_replies("NONEXISTENT_FIELD") == []
        assert _get_enum_quick_replies("") == []

    def test_case_insensitive_field_matching(self):
        """Field-Namen sollten case-insensitive gemappt werden."""
        result_upper = _get_enum_quick_replies("IMPACT_AREA", sample_size=1)
        result_lower = _get_enum_quick_replies("impact_area", sample_size=1)
        # Beide sollten gültige Replies generieren
        assert len(result_upper) == 1
        assert len(result_lower) == 1

    def test_randomness(self):
        """Mehrfache Calls sollten unterschiedliche Kombinationen geben."""
        results = [_get_enum_quick_replies("IMPACT_AREA", sample_size=3) for _ in range(5)]
        # Nicht alle sollten identisch sein (bei ausreichend Optionen)
        unique_results = set(tuple(sorted(r)) for r in results)
        assert len(unique_results) > 1  # mindestens 2 verschiedene Kombinationen


class TestIntegration:
    """Integrationstests."""

    def test_format_consistency(self):
        """Alle Generated Replies sollten Format <field>.<option> haben."""
        for field in ["IMPACT_AREA", "AWARDS", "OFFER_CATEGORY", "INTENT"]:
            result = _get_enum_quick_replies(field, sample_size=2)
            for reply in result:
                elements = reply.split(".")
                assert len(elements) == 2, f"Invalid format: {reply}"
                field_part, option_part = elements
                assert field_part.islower(), f"Field should be camelCase: {field_part}"
                assert option_part.islower(), f"Option should be camelCase: {option_part}"

    def test_no_special_characters(self):
        """Generated Strings sollten keine Sonderzeichen enthalten."""
        result = _get_enum_quick_replies("IMPACT_AREA", sample_size=3)
        for reply in result:
            # Nur alphanumeric, lowercase und punkt
            assert all(c.isalnum() or c == '.' for c in reply), f"Invalid chars in: {reply}"

    def test_sample_size_zero(self):
        """sample_size=0 sollte leere Liste geben."""
        result = _get_enum_quick_replies("IMPACT_AREA", sample_size=0)
        assert result == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

