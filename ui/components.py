import streamlit as st

from models.inputs import BoardMessage
from models.outputs import ExecutiveBoardSummary


def render_chat_messages(messages: list[BoardMessage]) -> None:
    if not messages:
        st.info("Board chat will appear here after you submit a request.")
        return

    for msg in messages:
        with st.chat_message(name=msg.speaker):
            st.markdown(f"**{msg.speaker}**")
            if msg.iteration:
                st.caption(f"Iteration {msg.iteration}")
            st.markdown(msg.content)


def render_executive_summary(summary: ExecutiveBoardSummary | None) -> None:
    st.subheader("Executive Summary")
    if summary is None:
        st.info("The supervisor summary appears here after the board finishes.")
        return

    st.metric("Funding Readiness", f"{summary.funding_readiness_score}/10")
    st.caption(f"Consensus: {summary.consensus_level}")

    st.markdown(summary.executive_summary)

    st.markdown("**Advantages**")
    if summary.advantages:
        for item in summary.advantages:
            st.markdown(f"- {item}")
    else:
        st.markdown("- None")

    st.markdown("**Disadvantages**")
    if summary.disadvantages:
        for item in summary.disadvantages:
            st.markdown(f"- {item}")
    else:
        st.markdown("- None")

    st.markdown(f"**Optimal Route: {summary.optimal_route.route_name}**")
    st.markdown(summary.optimal_route.why_this_route)

    if summary.optimal_route.expected_tradeoffs:
        st.markdown("**Expected Tradeoffs**")
        for item in summary.optimal_route.expected_tradeoffs:
            st.markdown(f"- {item}")

    if summary.alternative_route is not None:
        with st.expander(f"Alternative Route: {summary.alternative_route.route_name}"):
            st.markdown(summary.alternative_route.why_this_route)
            if summary.alternative_route.expected_tradeoffs:
                for item in summary.alternative_route.expected_tradeoffs:
                    st.markdown(f"- {item}")

    if summary.next_30_day_plan:
        st.markdown("**Next 30 Days**")
        for step in summary.next_30_day_plan:
            st.markdown(f"- {step}")


def render_status_log(status_log: list[str]) -> None:
    with st.expander("Workflow Status", expanded=False):
        if status_log:
            st.text("\n".join(status_log[-30:]))
        else:
            st.caption("No status messages yet.")
