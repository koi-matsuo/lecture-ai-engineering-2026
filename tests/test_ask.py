import builtins
import sys
from types import SimpleNamespace

from app import ask as ask_module


def test_chat_keeps_conversation_history(monkeypatch, capsys):
    responses = [
        SimpleNamespace(
            usage_metadata=SimpleNamespace(
                prompt_token_count=12,
                candidates_token_count=34,
            ),
            text="1つ目の回答",
        ),
        SimpleNamespace(
            usage_metadata=SimpleNamespace(
                prompt_token_count=40,
                candidates_token_count=56,
            ),
            text="前の質問を踏まえた回答",
        ),
    ]
    sent_messages = []

    def send_message(message):
        sent_messages.append(message)
        return responses[len(sent_messages) - 1]

    conversation = SimpleNamespace(send_message=send_message)
    created_chats = []

    def create_chat(**kwargs):
        created_chats.append(kwargs)
        return conversation

    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(
        ask_module.genai,
        "Client",
        lambda **_: SimpleNamespace(
            chats=SimpleNamespace(create=create_chat),
        ),
    )
    questions = iter(["最初の質問", "", "続きの質問", ":q"])
    monkeypatch.setattr(builtins, "input", lambda _: next(questions))
    elapsed_times = iter([10.0, 11.234, 20.0, 22.5])
    monkeypatch.setattr(ask_module.time, "perf_counter", lambda: next(elapsed_times))

    ask_module.chat()

    assert created_chats == [{"model": ask_module.MODEL}]
    assert sent_messages == ["最初の質問", "続きの質問"]
    output = capsys.readouterr().out
    assert "1つ目の回答" in output
    assert "前の質問を踏まえた回答" in output
    assert "入力: 12" in output
    assert "出力: 56" in output
    assert output.count("[応答時間]") == 2
    assert "[応答時間] 1.23秒" in output
    assert "[応答時間] 2.50秒" in output


def test_main_starts_chat_mode(monkeypatch):
    chat_started = []
    monkeypatch.setattr(sys, "argv", ["app.ask", "--chat"])
    monkeypatch.setattr(ask_module, "chat", lambda: chat_started.append(True))

    ask_module.main()

    assert chat_started == [True]


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
    elapsed_times = iter([10.0, 11.234])
    monkeypatch.setattr(ask_module.time, "perf_counter", lambda: next(elapsed_times))

    assert ask_module.ask("質問") == "回答"
    output = capsys.readouterr().out
    assert "入力: 12" in output
    assert "出力: 34" in output
    assert "[応答時間] 1.23秒" in output


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