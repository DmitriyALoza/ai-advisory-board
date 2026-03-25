from agno.agent import Agent

from agents.base import get_model
from models.outputs import InvestorReview
from orchestration.prompts import INVESTOR_PROFILES


def get_investor_agent(investor_id: str) -> Agent:
    if investor_id not in INVESTOR_PROFILES:
        raise ValueError(f"Unknown investor id: {investor_id}")

    profile = INVESTOR_PROFILES[investor_id]
    description = (
        f"You are {profile['name']}, the {profile['title']}. "
        f"Personality: {profile['personality']} "
        "Act like an experienced investor: concise, evidence-based, and specific."
    )

    return Agent(
        model=get_model(temperature=profile["temperature"]),
        description=description,
        output_schema=InvestorReview,
        structured_outputs=True,
    )
