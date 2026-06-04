"""Tests for the feature search wrappers (web/news/videos/images), offline.

Parametrized across every feature so adding one is a single row, mirroring the way the
agent registry adds a feature with a single entry. Verifies each wrapper hits the right
SDK namespace, scopes the query with `site:`, and passes content_format/max_length only
for the text features (web, news) and not for videos/images.
"""

import types

import pytest

from webiq_playground.web import search_web
from webiq_playground.news import search_news
from webiq_playground.videos import search_videos
from webiq_playground.images import search_images


class _Recorder:
    def __init__(self):
        self.args = None
        self.kwargs = None

    def search(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        return "resp"


def _fake_client():
    return types.SimpleNamespace(
        web=_Recorder(),
        news=_Recorder(),
        videos=_Recorder(),
        images=_Recorder(),
    )


# (wrapper, sdk namespace attribute, passes content_format/max_length)
CASES = [
    (search_web, "web", True),
    (search_news, "news", True),
    (search_videos, "videos", False),
    (search_images, "images", False),
]


@pytest.mark.parametrize("search_fn,namespace,has_content_format", CASES)
def test_wrapper_calls_right_namespace(search_fn, namespace, has_content_format):
    client = _fake_client()

    out = search_fn(
        client,
        "deadline",
        site="sars.gov.za",
        max_results=3,
        language="en",
        region="ZA",
    )

    recorder = getattr(client, namespace)
    assert out == "resp"
    assert recorder.args == ("deadline site:sars.gov.za",)
    assert recorder.kwargs["max_results"] == 3
    assert recorder.kwargs["language"] == "en"
    assert recorder.kwargs["region"] == "ZA"

    if has_content_format:
        assert "content_format" in recorder.kwargs
        assert "max_length" in recorder.kwargs
    else:
        assert "content_format" not in recorder.kwargs
        assert "max_length" not in recorder.kwargs
