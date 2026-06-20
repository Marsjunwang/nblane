"""Shared Streamlit page shell setup."""

from __future__ import annotations

import streamlit as st


def ensure_wide_page_shell() -> None:
    """Keep direct page reloads aligned with the main app shell.

    Production normally enters through ``app.py``, which configures Streamlit
    for a wide layout. A browser refresh on a legacy ``pages/*.py`` route can
    execute that page directly, so repeat the non-content layout settings here.
    """

    try:
        st.set_page_config(
            layout="wide",
            initial_sidebar_state="expanded",
        )
    except Exception:
        # Some Streamlit contexts have already rendered content or configured
        # the page. In those cases the main app shell has either already won,
        # or there is nothing useful to show the user besides the page itself.
        return
