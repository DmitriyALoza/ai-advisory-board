import os
import sys
import threading
import time

import streamlit as st
from dotenv import load_dotenv

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)

from models.inputs import BoardMessage, FounderRequest
from orchestration.workflow import run_board_cycle
from services.document_service import extract_documents
from services.session_service import (
    list_recent_sessions,
    load_session_snapshot,
    persist_session_snapshot,
)
from ui.components import render_chat_messages, render_executive_summary, render_status_log
from ui.state import init_state, reset_state

load_dotenv()

st.set_page_config(
    page_title="Board Chat",
    layout="wide",
)

init_state()


def _snapshot_from_session_state() -> dict:
    return {
        "phase": st.session_state.phase,
        "founder_request": st.session_state.founder_request,
        "documents": st.session_state.documents,
        "document_warnings": st.session_state.document_warnings,
        "messages": st.session_state.messages,
        "latest_reviews": st.session_state.latest_reviews,
        "critique_history": st.session_state.critique_history,
        "revision_map": st.session_state.revision_map,
        "board_brief": st.session_state.board_brief,
        "executive_summary": st.session_state.executive_summary,
        "status_log": st.session_state.status_log,
        "error_message": st.session_state.error_message,
    }


def _hydrate_session_state(session_id: str, snapshot: dict) -> None:
    st.session_state.session_id = session_id
    st.session_state.phase = snapshot["phase"]
    st.session_state.founder_request = snapshot["founder_request"]
    st.session_state.documents = snapshot["documents"]
    st.session_state.document_warnings = snapshot["document_warnings"]
    st.session_state.messages = snapshot["messages"]
    st.session_state.latest_reviews = snapshot["latest_reviews"]
    st.session_state.critique_history = snapshot["critique_history"]
    st.session_state.revision_map = snapshot["revision_map"]
    st.session_state.board_brief = snapshot["board_brief"]
    st.session_state.executive_summary = snapshot["executive_summary"]
    st.session_state.status_log = snapshot["status_log"]
    st.session_state.error_message = snapshot["error_message"]
    st.session_state.workflow_thread = None
    if "_workflow_state" in st.session_state:
        del st.session_state["_workflow_state"]


with st.sidebar:
    st.title("Investor Board")
    st.caption("Group chat with 4 investor agents + supervisor")
    st.markdown(f"**Session:** `{st.session_state.session_id}`")

    uploaded_files = st.file_uploader(
        "Upload startup materials",
        type=["pdf", "ppt", "pptx", "docx", "txt", "md"],
        accept_multiple_files=True,
    )
    founder_context = st.text_area(
        "Optional context",
        placeholder="e.g. We are raising a $2.5M seed, 14 months runway, fintech compliance constraints...",
        height=140,
    )

    recent_sessions = list_recent_sessions(limit=25)
    if recent_sessions:
        options = [row["session_id"] for row in recent_sessions]
        labels = {
            row["session_id"]: (
                f"{row['session_id']} | {row['updated_at'][:19]} | {row['phase']} | "
                f"{(row['ask_preview'] or 'No ask')[:50]}"
            )
            for row in recent_sessions
        }
        selected_id = st.selectbox(
            "Recent sessions",
            options=options,
            format_func=lambda sid: labels.get(sid, sid),
        )
        if st.button("Load Selected Session", use_container_width=True):
            loaded = load_session_snapshot(selected_id)
            if loaded is None:
                st.error("Could not load selected session.")
            else:
                _hydrate_session_state(selected_id, loaded)
                st.rerun()

    if st.button("New Session", use_container_width=True):
        reset_state()
        st.rerun()

st.title("Board Chat")
st.caption("Submit your ask and let the board run an iterative investment review loop.")

left_col, right_col = st.columns([2, 1], gap="large")

with left_col:
    with st.form("founder_request_form", clear_on_submit=False):
        startup_name = st.text_input("Startup name (optional)")
        ask = st.text_area(
            "What should the board evaluate?",
            placeholder="Review our pitch deck + forecast and tell us whether to raise now, reposition, or de-risk first.",
            height=140,
        )
        submitted = st.form_submit_button("Send To Board", type="primary")

    if submitted:
        if not ask.strip():
            st.error("Enter a request before sending to the board.")
        else:
            docs, warnings = extract_documents(uploaded_files or [])

            st.session_state.founder_request = FounderRequest(
                startup_name=startup_name.strip() or None,
                ask=ask.strip(),
                context=founder_context.strip() or None,
            )
            st.session_state.documents = docs
            st.session_state.document_warnings = warnings
            if not st.session_state.messages:
                st.session_state.messages = []
            st.session_state.messages.append(
                BoardMessage(
                    role="user",
                    speaker="Founder",
                    content=ask.strip(),
                )
            )
            st.session_state.latest_reviews = {}
            st.session_state.critique_history = []
            st.session_state.revision_map = {}
            st.session_state.board_brief = None
            st.session_state.executive_summary = None
            if not st.session_state.status_log:
                st.session_state.status_log = []
            st.session_state.status_log.append("Board run started.")
            st.session_state.error_message = None
            st.session_state.phase = "running"
            persist_session_snapshot(st.session_state.session_id, _snapshot_from_session_state())

            workflow_state = {
                "founder_request": st.session_state.founder_request,
                "documents": st.session_state.documents,
                "document_warnings": st.session_state.document_warnings,
                "messages": st.session_state.messages,
                "latest_reviews": st.session_state.latest_reviews,
                "critique_history": st.session_state.critique_history,
                "revision_map": st.session_state.revision_map,
                "board_brief": st.session_state.board_brief,
                "executive_summary": st.session_state.executive_summary,
                "status_log": st.session_state.status_log,
                "error_message": None,
                "phase": "running",
            }
            st.session_state["_workflow_state"] = workflow_state

            thread = threading.Thread(target=run_board_cycle, args=(workflow_state,), daemon=True)
            thread.start()
            st.session_state.workflow_thread = thread
            st.rerun()

    if st.session_state.phase == "running":
        workflow_state = st.session_state.get("_workflow_state")
        if workflow_state:
            st.session_state.messages = workflow_state["messages"]
            st.session_state.status_log = workflow_state["status_log"]
            st.session_state.executive_summary = workflow_state.get("executive_summary")
            st.session_state.critique_history = workflow_state["critique_history"]
            st.session_state.board_brief = workflow_state.get("board_brief")
            st.session_state.phase = workflow_state["phase"]
            st.session_state.error_message = workflow_state.get("error_message")
            persist_session_snapshot(st.session_state.session_id, _snapshot_from_session_state())

        render_chat_messages(st.session_state.messages)
        render_status_log(st.session_state.status_log)

        thread = st.session_state.workflow_thread
        if thread and thread.is_alive():
            time.sleep(1.5)
            st.rerun()
        elif workflow_state is not None:
            st.rerun()
        else:
            st.info("Loaded snapshot was mid-run. Submit a new request to start a fresh board cycle.")

    elif st.session_state.phase == "error":
        persist_session_snapshot(st.session_state.session_id, _snapshot_from_session_state())
        render_chat_messages(st.session_state.messages)
        st.error(f"Board run failed: {st.session_state.error_message}")
        render_status_log(st.session_state.status_log)

    else:
        if st.session_state.messages or st.session_state.executive_summary:
            persist_session_snapshot(st.session_state.session_id, _snapshot_from_session_state())
        render_chat_messages(st.session_state.messages)
        render_status_log(st.session_state.status_log)

    if st.session_state.document_warnings:
        with st.expander("Document Parsing Notes", expanded=False):
            for warning in st.session_state.document_warnings:
                st.markdown(f"- {warning}")

with right_col:
    render_executive_summary(st.session_state.executive_summary)
