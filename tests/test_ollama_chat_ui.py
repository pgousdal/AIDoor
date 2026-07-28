from __future__ import annotations

import pytest

from aidoor.ollama.chat_ui import _sort_and_dedupe_models, show_model_selection
from aidoor.ollama.models import ModelInfo, ModelSelectionResult
from aidoor.terminal import FakeTerminal


def _model(name: str) -> ModelInfo:
    return ModelInfo(name=name, modified_at="", size=0)


class TestSortAndDedupeModels:
    def test_sorts_alphabetically(self) -> None:
        models = [_model("zebra"), _model("alpha"), _model("beta")]
        sorted_m, _ = _sort_and_dedupe_models(models, "llama3.1")
        assert [m.name for m in sorted_m] == ["alpha", "beta", "zebra"]

    def test_case_insensitive_sorting(self) -> None:
        models = [_model("BRAVO"), _model("alpha"), _model("Charlie")]
        sorted_m, _ = _sort_and_dedupe_models(models, "llama3.1")
        assert [m.name for m in sorted_m] == ["alpha", "BRAVO", "Charlie"]

    def test_removes_duplicates(self) -> None:
        models = [_model("llama3.1"), _model("mistral"), _model("llama3.1")]
        sorted_m, _ = _sort_and_dedupe_models(models, "llama3.1")
        assert [m.name for m in sorted_m] == ["llama3.1", "mistral"]

    def test_removes_case_insensitive_duplicates(self) -> None:
        models = [_model("llama3.1"), _model("Llama3.1"), _model("LLAMA3.1")]
        sorted_m, _ = _sort_and_dedupe_models(models, "mistral")
        assert len(sorted_m) == 1
        assert sorted_m[0].name == "llama3.1"

    def test_keeps_first_occurrence_on_duplicate(self) -> None:
        models = [_model("AAA"), _model("aaa"), _model("BBB")]
        sorted_m, _ = _sort_and_dedupe_models(models, "mistral")
        assert len(sorted_m) == 2
        assert sorted_m[0].name == "AAA"
        assert sorted_m[1].name == "BBB"

    def test_highlights_default_model(self) -> None:
        models = [_model("mistral"), _model("llama3.1"), _model("deepseek")]
        _, default_index = _sort_and_dedupe_models(models, "llama3.1")
        assert default_index == 1

    def test_default_index_none_when_not_installed(self) -> None:
        models = [_model("mistral"), _model("deepseek")]
        _, default_index = _sort_and_dedupe_models(models, "llama3.1")
        assert default_index is None

    def test_case_insensitive_default_match(self) -> None:
        models = [_model("LLAMA3.1"), _model("mistral")]
        _, default_index = _sort_and_dedupe_models(models, "llama3.1")
        assert default_index == 0

    def test_empty_model_list(self) -> None:
        sorted_m, default_index = _sort_and_dedupe_models([], "llama3.1")
        assert sorted_m == []
        assert default_index is None


class TestModelSelectionResult:
    def test_successful_selection(self) -> None:
        r = ModelSelectionResult(model="llama3.1")
        assert r.model == "llama3.1"
        assert not r.cancelled

    def test_cancelled(self) -> None:
        r = ModelSelectionResult(cancelled=True)
        assert r.cancelled
        assert r.model is None

    def test_cancelled_with_model_raises(self) -> None:
        with pytest.raises(ValueError, match="cancelled"):
            ModelSelectionResult(model="mistral", cancelled=True)

    def test_non_cancelled_without_model_raises(self) -> None:
        with pytest.raises(ValueError, match="non-cancelled"):
            ModelSelectionResult()

    def test_empty_model_raises(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            ModelSelectionResult(model="")


class TestShowModelSelection:
    def test_select_first_model(self) -> None:
        models = [_model("deepseek"), _model("llama3.1"), _model("mistral")]
        term = FakeTerminal(keys=["1"])
        result = show_model_selection(term, models, "llama3.1")
        assert result.model == "deepseek"
        assert not result.cancelled

    def test_select_second_model(self) -> None:
        models = [_model("deepseek"), _model("llama3.1"), _model("mistral")]
        term = FakeTerminal(keys=["2"])
        result = show_model_selection(term, models, "llama3.1")
        assert result.model == "llama3.1"
        assert not result.cancelled

    def test_cancel(self) -> None:
        models = [_model("deepseek"), _model("llama3.1"), _model("mistral")]
        term = FakeTerminal(keys=["q"])
        result = show_model_selection(term, models, "llama3.1")
        assert result.cancelled
        assert result.model is None

    def test_cancel_uppercase(self) -> None:
        models = [_model("deepseek"), _model("llama3.1")]
        term = FakeTerminal(keys=["Q"])
        result = show_model_selection(term, models, "llama3.1")
        assert result.cancelled
        assert result.model is None

    def test_invalid_selection_retries(self) -> None:
        models = [_model("llama3.1"), _model("mistral")]
        term = FakeTerminal(keys=["x", "1"])
        result = show_model_selection(term, models, "llama3.1")
        assert result.model == "llama3.1"
        assert not result.cancelled

    def test_out_of_range_retries(self) -> None:
        models = [_model("llama3.1")]
        term = FakeTerminal(keys=["5", "1"])
        result = show_model_selection(term, models, "llama3.1")
        assert result.model == "llama3.1"
        assert not result.cancelled

    def test_default_not_installed_shows_note(self) -> None:
        models = [_model("mistral"), _model("deepseek")]
        term = FakeTerminal(keys=["1"])
        show_model_selection(term, models, "llama3.1")
        output = term.output
        assert "not installed" in output
        assert "choose any" in output

    def test_default_installed_shows_label(self) -> None:
        models = [_model("llama3.1"), _model("mistral")]
        term = FakeTerminal(keys=["1"])
        show_model_selection(term, models, "llama3.1")
        output = term.output
        assert "(default)" in output
        assert "not installed" not in output

    def test_alphabetical_order_in_output(self) -> None:
        models = [_model("zebra"), _model("alpha"), _model("beta")]
        term = FakeTerminal(keys=["q"])
        show_model_selection(term, models, "llama3.1")
        output = term.output
        alpha_pos = output.index("alpha")
        beta_pos = output.index("beta")
        zebra_pos = output.index("zebra")
        assert alpha_pos < beta_pos < zebra_pos

    def test_empty_model_list_returns_none(self) -> None:
        sorted_m, _ = _sort_and_dedupe_models([], "llama3.1")
        assert sorted_m == []

    def test_no_sentinel_values_in_output(self) -> None:
        models = [_model("deepseek"), _model("llama3.1")]
        term = FakeTerminal(keys=["1"])
        result = show_model_selection(term, models, "llama3.1")
        assert isinstance(result, ModelSelectionResult)
        assert not isinstance(result, str)
        assert result.model is not None
