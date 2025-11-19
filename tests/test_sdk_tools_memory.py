from ai_agents import sdk_tools


def test_append_and_read_memory(tmp_path):
    # append a test entry
    entry = {"test_key": "test_value"}
    ok = sdk_tools.append_memory(entry)
    assert ok is True

    mem = sdk_tools.read_memory(limit=5)
    assert any((isinstance(e, dict) and e.get('test_key') == 'test_value') or (isinstance(e, dict) and e.get('content') == entry) for e in mem)
