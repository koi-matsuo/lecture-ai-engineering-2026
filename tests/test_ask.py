from types import SimpleNamespace

from app import ask as ask_module


def test_ask_displays_input_and_output_token_counts(monkeypatch, capsys):
    response = SimpleNamespace(
        usage_metadata=SimpleNamespace(
            prompt_token_count=12,
            candidates_token_count=34,
        ),
        text="回答",
    )
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(
        ask_module.genai,
        "Client",
        lambda **_: SimpleNamespace(
            models=SimpleNamespace(generate_content=lambda **__: response)
        ),
    )

    assert ask_module.ask("質問") == "回答"
    output = capsys.readouterr().out
    assert "入力: 12" in output
    assert "出力: 34" in output


def test_ask_handles_missing_usage_metadata(monkeypatch, capsys):
    response = SimpleNamespace(usage_metadata=None, text="回答")
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(
        ask_module.genai,
        "Client",
        lambda **_: SimpleNamespace(
            models=SimpleNamespace(generate_content=lambda **__: response)
        ),
    )

    assert ask_module.ask("質問") == "回答"
    assert "利用状況を取得できませんでした" in capsys.readouterr().out