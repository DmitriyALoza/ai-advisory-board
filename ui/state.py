import uuid

import streamlit as st


def generate_session_id() -> str:
    return str(uuid.uuid4())[:8]


def init_state() -> None:
    defaults = {
        "session_id": generate_session_id(),
        "phase": "idle",
        "founder_request": None,
        "documents": [],
        "document_warnings": [],
        "messages": [],
        "latest_reviews": {},
        "critique_history": [],
        "revision_map": {},
        "board_brief": None,
        "executive_summary": None,
        "status_log": [],
        "error_message": None,
        "workflow_thread": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_state() -> None:
    keys = [
        "session_id",
        "phase",
        "founder_request",
        "documents",
        "document_warnings",
        "messages",
        "latest_reviews",
        "critique_history",
        "revision_map",
        "board_brief",
        "executive_summary",
        "status_log",
        "error_message",
        "workflow_thread",
        "_workflow_state",
    ]
    for key in keys:
        if key in st.session_state:
            del st.session_state[key]
    init_state()
