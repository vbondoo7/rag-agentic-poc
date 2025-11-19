from crew.crew_manager import create_agent


def test_create_agent_with_callable_handler():
    a = create_agent("TestAgent", handler=lambda q, c: f"ok:{q}:{c}")
    assert a.run("q1", "ctx1") == "ok:q1:ctx1"


class DummyHandler:
    def analyze(self, q, c):
        return f"analyzed:{q}:{c}"


def test_create_agent_with_object_handler():
    h = DummyHandler()
    a = create_agent("TestAgentObj", handler=h)
    assert a.run("q2", "ctx2") == "analyzed:q2:ctx2"
