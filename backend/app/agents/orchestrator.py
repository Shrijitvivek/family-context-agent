"""Primary Family Context Agent orchestrator.

TODO:
- Gather relevant household and conversation context.
- Ask the NVIDIA model for structured intent and tool requests.
- Detect missing or ambiguous information before any state change.
- Validate and dispatch only registered tools.
- Record observable agent events without storing hidden chain-of-thought.
"""
