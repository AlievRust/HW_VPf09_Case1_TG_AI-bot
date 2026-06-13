from __future__ import annotations

from tg_ai_bot.state import JsonStateStore


def test_state_store_trims_history_and_persists(tmp_path) -> None:
    path = tmp_path / ".bot_state.json"
    store = JsonStateStore(path, max_context_messages=3)

    store.append_message(42, "user", "one", "assistant")
    store.append_message(42, "assistant", "two", "assistant")
    store.append_message(42, "user", "three", "assistant")
    store.append_message(42, "assistant", "four", "assistant")

    messages = store.get_messages(42)
    assert [message.content for message in messages] == ["two", "three", "four"]

    reloaded = JsonStateStore(path, max_context_messages=3)
    assert [message.content for message in reloaded.get_messages(42)] == [
        "two",
        "three",
        "four",
    ]


def test_state_store_reset_sets_default_role(tmp_path) -> None:
    path = tmp_path / ".bot_state.json"
    store = JsonStateStore(path, max_context_messages=5)

    store.set_role(7, "teacher", "assistant")
    store.append_message(7, "user", "hello", "assistant")
    store.reset_user(7, "assistant")

    assert store.get_role(7, "assistant") == "assistant"
    assert store.get_messages(7) == []
