from agno.agent import Agent

from agents.base import get_model
from models.outputs import BoardBrief, BoardCritique, ExecutiveBoardSummary
from orchestration.prompts import SUPERVISOR_SYSTEM_INSTRUCTIONS


def get_brief_agent() -> Agent:
    return Agent(
        model=get_model(temperature=0.2),
        description=SUPERVISOR_SYSTEM_INSTRUCTIONS,
        output_schema=BoardBrief,
        structured_outputs=True,
    )


def get_critique_agent() -> Agent:
    return Agent(
        model=get_model(temperature=0.2),
        description=SUPERVISOR_SYSTEM_INSTRUCTIONS,
        output_schema=BoardCritique,
        structured_outputs=True,
    )


def get_synthesis_agent() -> Agent:
    return Agent(
        model=get_model(temperature=0.2),
        description=SUPERVISOR_SYSTEM_INSTRUCTIONS,
        output_schema=ExecutiveBoardSummary,
        structured_outputs=True,
    )
