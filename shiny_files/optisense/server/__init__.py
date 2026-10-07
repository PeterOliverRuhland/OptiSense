"""Server of OptiSense. Each step of the page has its own module; they share one AppContext."""

from . import files, graph, guide, problem, results, solving, value_range
from .context import AppContext


def server(input, output, session):
    ctx = AppContext(input, session)
    for part in (problem, value_range, solving, graph, results, files, guide):
        part.register(ctx)
