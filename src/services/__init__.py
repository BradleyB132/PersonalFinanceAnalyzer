"""Service layer package for PersonalFinanceAnalyzer.

This package-level module ensures logging is configured when any service
module is imported. Importing `services` will load `logging_config` which
initializes the root logger handlers and formatters.
"""

# Initialize global logging configuration early so modules that import
# `services.*` will already have handlers/formatters attached.
try:
    import logging_config  # noqa: F401 - module side-effects only
except Exception:
    # Avoid raising during test discovery if logging config has issues; fall
    # back to the default logging configuration.
    import logging

    logging.basicConfig(level=logging.DEBUG)
