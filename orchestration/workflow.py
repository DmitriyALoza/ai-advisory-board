import json
from typing import Any

from agents.investor_agents import get_investor_agent
from agents.supervisor_agent import get_brief_agent, get_critique_agent, get_synthesis_agent
from models.inputs import BoardMessage, FounderRequest
from models.outputs import BoardBrief, BoardCritique, ExecutiveBoardSummary, InvestorReview
from orchestration.prompts import (
    BRIEF_PROMPT,
    CRITIQUE_PROMPT,
    INVESTOR_PROFILES,
    INVESTOR_REVIEW_PROMPT,
    SYNTHESIS_PROMPT,
)
from services.document_service import build_document_digest

MAX_CRITIQUE_ITERATIONS = 3
INVESTOR_ORDER = ["market_maven", "finance_hawk", "product_operator", "risk_guardian"]


def _to_json(data: Any) -> str:
    if data is None:
        return "None"
    if isinstance(data, list):
        if not data:
            return "[]"
        return "\n\n".join(_to_json(item) for item in data)
    if hasattr(data, "model_dump_json"):
        return data.model_dump_json(indent=2)
    return json.dumps(data, indent=2, default=str)


def _append_message(state: dict, role: str, speaker: str, content: str, iteration: int | None = None) -> None:
    state["messages"].append(
        BoardMessage(
            role=role,
            speaker=speaker,
            content=content,
            iteration=iteration,
        )
    )


def _run_with_schema_retry(agent: Any, prompt: str, schema_name: str, status_log: list[str]) -> Any:
    try:
        return agent.run(prompt).content
    except Exception as exc:
        status_log.append(f"{schema_name} generation error: {exc}. Retrying with strict schema instruction.")
        retry_prompt = (
            prompt
            + "\n\nIMPORTANT: Respond ONLY with valid JSON matching the expected schema."
            + f" Target schema: {schema_name}."
        )
        return agent.run(retry_prompt).content


def _format_investor_chat(review: InvestorReview) -> str:
    strengths = "\n".join(f"- {item}" for item in review.key_strengths) or "- None"
    concerns = "\n".join(f"- {item}" for item in review.key_concerns) or "- None"
    questions = "\n".join(f"- {item}" for item in review.diligence_questions) or "- None"
    actions = "\n".join(f"- {item}" for item in review.actionable_advice) or "- None"

    return (
        f"**Stance:** {review.stance}  \n"
        f"**Conviction:** {review.conviction_score}/10\n\n"
        f"**Investment Thesis**\n{review.investment_thesis}\n\n"
        f"**Key Strengths**\n{strengths}\n\n"
        f"**Key Concerns**\n{concerns}\n\n"
        f"**Diligence Questions**\n{questions}\n\n"
        f"**Actionable Advice**\n{actions}"
    )


def _format_critique_chat(report: BoardCritique) -> str:
    disagreements = "\n".join(f"- {item}" for item in report.disagreements) or "- None"
    missing = "\n".join(f"- {item}" for item in report.missing_evidence) or "- None"

    instructions = []
    for item in report.revision_instructions:
        instructions.append(f"- {item.investor_name}: {item.instruction}")
    instructions_text = "\n".join(instructions) or "- None"

    status = "Converged" if report.should_stop else "Continue"
    return (
        f"**Iteration {report.iteration} Critique: {status}**\n\n"
        f"**Convergence Assessment**\n{report.convergence_assessment}\n\n"
        f"**Key Disagreements**\n{disagreements}\n\n"
        f"**Missing Evidence**\n{missing}\n\n"
        f"**Revision Instructions**\n{instructions_text}"
    )


def _format_executive_chat(summary: ExecutiveBoardSummary) -> str:
    advantages = "\n".join(f"- {item}" for item in summary.advantages) or "- None"
    disadvantages = "\n".join(f"- {item}" for item in summary.disadvantages) or "- None"
    plan = "\n".join(f"- {item}" for item in summary.next_30_day_plan) or "- None"

    return (
        f"**Funding Readiness Score:** {summary.funding_readiness_score}/10  \n"
        f"**Consensus:** {summary.consensus_level}\n\n"
        f"{summary.executive_summary}\n\n"
        f"**Advantages**\n{advantages}\n\n"
        f"**Disadvantages**\n{disadvantages}\n\n"
        f"**Optimal Route: {summary.optimal_route.route_name}**\n"
        f"{summary.optimal_route.why_this_route}\n\n"
        f"**Next 30 Days**\n{plan}"
    )


def run_board_cycle(state: dict) -> None:
    """
    Expected keys in state:
      founder_request: FounderRequest
      documents: list[DocumentInput]
      status_log: list[str]
      messages: list[BoardMessage]
      latest_reviews: dict[str, InvestorReview]
      critique_history: list[BoardCritique]
      revision_map: dict[str, str]
    """
    try:
        founder_request: FounderRequest = state["founder_request"]
        digest = build_document_digest(state.get("documents", []))

        state["status_log"].append("Supervisor is preparing board brief...")
        brief_prompt = BRIEF_PROMPT.format(
            founder_ask=founder_request.ask,
            founder_context=founder_request.context or "None provided",
            document_digest=digest,
        )

        brief_agent = get_brief_agent()
        board_brief: BoardBrief = _run_with_schema_retry(
            brief_agent,
            brief_prompt,
            "BoardBrief",
            state["status_log"],
        )
        state["board_brief"] = board_brief

        _append_message(
            state,
            role="supervisor",
            speaker="Lead Partner",
            content=(
                "Board brief prepared.\n\n"
                f"**Startup Summary:** {board_brief.startup_summary}\n\n"
                f"**Current Stage:** {board_brief.current_stage}\n\n"
                f"**Fundraising Goal:** {board_brief.fundraising_goal}"
            ),
        )

        for iteration in range(1, MAX_CRITIQUE_ITERATIONS + 1):
            state["status_log"].append(f"Running investor iteration {iteration}/{MAX_CRITIQUE_ITERATIONS}...")

            current_reviews: list[InvestorReview] = []
            for investor_id in INVESTOR_ORDER:
                profile = INVESTOR_PROFILES[investor_id]
                state["status_log"].append(f"{profile['name']} is reviewing materials...")

                previous_review = state["latest_reviews"].get(investor_id)
                revision_instruction = state["revision_map"].get(investor_id, "No revision instruction.")

                prompt = INVESTOR_REVIEW_PROMPT.format(
                    investor_profile=json.dumps(profile, indent=2),
                    board_brief=_to_json(board_brief),
                    founder_ask=founder_request.ask,
                    document_digest=digest,
                    previous_review=_to_json(previous_review),
                    revision_instruction=revision_instruction,
                )

                investor_agent = get_investor_agent(investor_id)
                review: InvestorReview = _run_with_schema_retry(
                    investor_agent,
                    prompt,
                    "InvestorReview",
                    state["status_log"],
                )

                review.investor_id = investor_id
                review.investor_name = profile["name"]
                review.personality = profile["personality"]

                state["latest_reviews"][investor_id] = review
                current_reviews.append(review)

                _append_message(
                    state,
                    role="investor",
                    speaker=f"{profile['name']} ({profile['title']})",
                    content=_format_investor_chat(review),
                    iteration=iteration,
                )

            state["status_log"].append("Supervisor is critiquing board responses...")
            critique_prompt = CRITIQUE_PROMPT.format(
                iteration=iteration,
                board_brief=_to_json(board_brief),
                reviews=_to_json(current_reviews),
                critique_history=_to_json(state["critique_history"]),
            )

            critique_agent = get_critique_agent()
            critique: BoardCritique = _run_with_schema_retry(
                critique_agent,
                critique_prompt,
                "BoardCritique",
                state["status_log"],
            )
            critique.iteration = iteration
            state["critique_history"].append(critique)

            revision_map: dict[str, str] = {}
            for item in critique.revision_instructions:
                revision_map[item.investor_id] = item.instruction
            state["revision_map"] = revision_map

            _append_message(
                state,
                role="supervisor",
                speaker="Lead Partner",
                content=_format_critique_chat(critique),
                iteration=iteration,
            )

            if critique.should_stop:
                state["status_log"].append("Board has converged. Moving to final synthesis.")
                break

        state["status_log"].append("Generating executive summary...")
        synthesis_prompt = SYNTHESIS_PROMPT.format(
            board_brief=_to_json(state["board_brief"]),
            reviews=_to_json(list(state["latest_reviews"].values())),
            critique_history=_to_json(state["critique_history"]),
        )

        synthesis_agent = get_synthesis_agent()
        summary: ExecutiveBoardSummary = _run_with_schema_retry(
            synthesis_agent,
            synthesis_prompt,
            "ExecutiveBoardSummary",
            state["status_log"],
        )

        state["executive_summary"] = summary
        _append_message(
            state,
            role="supervisor",
            speaker="Lead Partner",
            content=_format_executive_chat(summary),
        )

        state["phase"] = "complete"
        state["status_log"].append("Board cycle complete.")

    except Exception as exc:
        state["error_message"] = str(exc)
        state["phase"] = "error"
        state["status_log"].append(f"Workflow error: {exc}")
