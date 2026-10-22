"""ccfb: Claude Code free-LLM fallback gateway.

A small, dependency-free local gateway that sits between Claude Code and the
Anthropic API. It passes Claude traffic through unchanged and, only when a
subscription usage limit is reported, serves requests from free providers
until Claude is available again. See fallback/README.md and fallback/DESIGN.md.
"""

__version__ = "0.1.0"
