"""The settle gate needs EVA's composer unlocked, not only a quiet node.

Origin 2026-10-02 (batch 4): EVA paused mid-answer for longer than the
STABLE_POLLS window. eva-adapter/1.1.0 called the answer finished, stored it
TRUNCATED (CWOPS2000 219), and the next ask() clicked a textarea that EVA keeps
disabled while it is still generating: a raw Playwright timeout ended the run
after 3 of 100 prompts. The disabled composer is the positive "still writing"
signal the adapter docstring said did not exist.
"""
import pytest

from modules.knowledge_acquisition import eva_adapter
from modules.knowledge_acquisition.eva_adapter import AdapterError, EvaAdapter


class FakeNode:
    """An assistant node whose text follows a scripted sequence, one step per poll."""

    def __init__(self, texts):
        self.texts, self.i = list(texts), 0

    def inner_text(self, timeout=None):
        t = self.texts[min(self.i, len(self.texts) - 1)]
        self.i += 1
        return t

    def inner_html(self, timeout=None):
        return "<p>" + self.texts[min(self.i - 1, len(self.texts) - 1)] + "</p>"


class FakeComposer:
    def __init__(self, enabled_after):
        self.enabled_after, self.calls = enabled_after, 0

    def count(self):
        return 1

    @property
    def first(self):
        return self

    def is_enabled(self, timeout=None):
        self.calls += 1
        return self.calls > self.enabled_after


class FakeFrame:
    def __init__(self, composer):
        self.composer = composer

    def locator(self, sel):
        assert sel == "textarea"
        return self.composer


def make_adapter(composer):
    a = EvaAdapter.__new__(EvaAdapter)
    a._frame = FakeFrame(composer)
    return a


@pytest.fixture(autouse=True)
def fast_clock(monkeypatch):
    monkeypatch.setattr(eva_adapter, "POLL_INTERVAL_S", 0)
    monkeypatch.setattr(eva_adapter.time, "sleep", lambda s: None)


def test_quiet_node_with_locked_composer_is_not_settled():
    # Arrange: text pauses at a partial answer for 8 polls (longer than STABLE_POLLS),
    # then resumes; the composer stays locked through the pause
    partial, full = "Primera parte de la respuesta, y", "Primera parte de la respuesta, y el final."
    node = FakeNode([partial] * 8 + [full] * 20)
    composer = FakeComposer(enabled_after=12)
    # Act
    text, _ = make_adapter(composer)._await_settle(node, eva_adapter.time.time())
    # Assert: the pause did not end the capture
    assert text == full


def test_quiet_node_with_unlocked_composer_settles():
    # Positive control: same quiet node, composer free -> settles on the stable text
    node = FakeNode(["Respuesta completa."] * 20)
    text, _ = make_adapter(FakeComposer(enabled_after=0))._await_settle(node, eva_adapter.time.time())
    assert text == "Respuesta completa."
    assert node.i == eva_adapter.STABLE_POLLS + 1


def test_await_composer_returns_once_unlocked():
    composer = FakeComposer(enabled_after=3)
    make_adapter(composer)._await_composer()
    assert composer.calls == 4


def test_composer_that_never_unlocks_is_an_adapter_error(monkeypatch):
    # A raw Playwright timeout escapes the runner and kills the run;
    # an AdapterError fails one job and the run continues.
    monkeypatch.setattr(eva_adapter, "APPEARANCE_TIMEOUT_S", 0.05)
    with pytest.raises(AdapterError, match="composer stayed disabled"):
        make_adapter(FakeComposer(enabled_after=10**9))._await_composer()


def test_version_records_the_new_gate():
    assert eva_adapter.ADAPTER_VERSION == "eva-adapter/1.2.0"
