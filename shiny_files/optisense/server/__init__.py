"""Server of OptiSense: one AppContext per session (context.py), shared by the three pages."""

from ..pages.guide import server as guide
from ..pages.learn import server as learn
from ..pages.work import server as work
from .context import AppContext


def server(input, output, session):
    ctx = AppContext(input, session)
    for page in (work, guide, learn):
        page.register(ctx)
