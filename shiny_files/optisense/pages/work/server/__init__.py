"""Server part of “Model & solution”: one module per part of the page, all sharing the AppContext."""

from . import files, graph, help_dialog, problem, results, solving, value_range


def register(ctx):
    for part in (problem, value_range, solving, graph, results, files, help_dialog):
        part.register(ctx)
