from types import SimpleNamespace

from app import ask as ask_module


class FakeChat:
    def __init__(self):
        self.messages = []

    def send_message(self, message):
        self.messages.append(message)
        return SimpleNamespace(
            text=f"回答: {message}",
            usage_metadata=SimpleNamespace(
                prompt_token_count=10,
                candidates_token_count=5,
            ),
        )


def test_interactive_chat_reuses_chat_history(monkeypatch, capsys):
    chat = FakeChat()
    client = SimpleNamespace(chats=SimpleNamespace(create=lambda **kwargs: chat))
    questions = iter(["最初の質問", "続きの質問", "quit"])
    monkeypatch.setattr(ask_module.genai, "Client", lambda **kwargs: client)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr("builtins.input", lambda _: next(questions))
    monkeypatch.setattr("sys.argv", ["app.ask", "--interactive"])

    ask_module.main()

    assert chat.messages == ["最初の質問", "続きの質問"]
    output = capsys.readouterr().out
    assert "回答: 最初の質問" in output
    assert "回答: 続きの質問" in output
    assert output.count("[トークン数]") == 2


def test_ask_still_sends_a_single_question(monkeypatch, capsys):
    response = SimpleNamespace(
        text="単発の回答",
        usage_metadata=SimpleNamespace(
            prompt_token_count=3,
            candidates_token_count=4,
        ),
    )
    client = SimpleNamespace(
        models=SimpleNamespace(
            generate_content=lambda **kwargs: response,
        )
    )
    monkeypatch.setattr(ask_module.genai, "Client", lambda **kwargs: client)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")

    assert ask_module.ask("質問") == "単発の回答"
    assert "[トークン数] 入力: 3, 出力: 4" in capsys.readouterr().out
