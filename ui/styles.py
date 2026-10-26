"""Design System and UI Styling for InternFlow AI.

Implements the high-converting Neo-Brutalist Playful SaaS aesthetic:
- Top pill capsule navigation bar with active purple pill and dark borders
- Neo-brutalist cards with 2.5px dark borders & crisp offset drop-shadows (4px 4px 0px #1E1E24)
- Signature color palette:
  - Purple capsule: #9B72CF
  - Neon Lime accent: #D4F074
  - Deep Midnight Navy section: #151D2A
  - Canvas background: #F4F3EF
- Side-by-side 'What is Good' vs 'What is Not Good' comparison cards
"""

import streamlit as st


def apply_custom_styles():
    """Inject Neo-Brutalist playful SaaS design into Streamlit."""
    custom_css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;700&display=swap');

    /* Global Neo-Brutalist Canvas Background */
    html, body, [class*="css"], .stApp {
        background-color: #F4F3EF !important;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        color: #151D2A;
    }

    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 3rem !important;
        max-width: 95% !important;
    }

    /* Left Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #FAF9F6 !important;
        border-right: 2.5px solid #1E1E24 !important;
    }

    /* Top Capsule Navigation Bar */
    .binke-nav-bar {
        background: #FFFFFF;
        border: 2.5px solid #1E1E24;
        border-radius: 9999px;
        padding: 12px 24px;
        margin-top: 4px;
        margin-bottom: 32px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 14px;
        box-shadow: 4px 4px 0px #1E1E24;
        width: 100%;
        box-sizing: border-box;
    }

    .binke-logo {
        font-size: 22px;
        font-weight: 900;
        letter-spacing: -0.04em;
        color: #1E1E24;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .binke-nav-links {
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .binke-pill {
        padding: 6px 18px;
        border-radius: 9999px;
        font-size: 13px;
        font-weight: 700;
        text-decoration: none;
        transition: all 0.15s ease;
    }

    .pill-purple {
        background: #9B72CF;
        color: #FFFFFF !important;
        border: 2px solid #1E1E24;
        box-shadow: 2px 2px 0px #1E1E24;
    }

    .pill-lime {
        background: #D4F074;
        color: #1E1E24 !important;
        border: 2px solid #1E1E24;
        font-weight: 800;
        box-shadow: 2px 2px 0px #1E1E24;
    }

    .pill-black {
        background: #1E1E24;
        color: #FFFFFF !important;
        border: 2px solid #1E1E24;
        border-radius: 9999px;
        padding: 7px 20px;
        font-weight: 800;
        box-shadow: 3px 3px 0px #9B72CF;
    }

    /* Hero Typography */
    .hero-title-neo {
        font-size: 44px;
        font-weight: 900;
        letter-spacing: -0.04em;
        color: #151D2A;
        line-height: 1.1;
        margin-bottom: 12px;
    }

    .hero-sub-neo {
        font-size: 15px;
        color: #475569;
        font-weight: 600;
        line-height: 1.5;
        max-width: 600px;
        margin-bottom: 22px;
    }

    /* Primary Purple Action Button with Drop Shadow */
    .btn-purple-neo {
        display: inline-block;
        background: #9B72CF;
        color: #FFFFFF !important;
        border: 2.5px solid #1E1E24;
        border-radius: 9999px;
        padding: 12px 32px;
        font-size: 15px;
        font-weight: 800;
        box-shadow: 4px 4px 0px #1E1E24;
        transition: transform 0.1s ease, box-shadow 0.1s ease;
        text-decoration: none;
    }

    .btn-purple-neo:hover {
        transform: translate(-1px, -1px);
        box-shadow: 5px 5px 0px #1E1E24;
    }

    /* Trust Pill Bar */
    .trust-bar {
        background: #FFFFFF;
        border: 2px solid #1E1E24;
        border-radius: 9999px;
        padding: 8px 24px;
        display: inline-flex;
        align-items: center;
        gap: 20px;
        box-shadow: 3px 3px 0px #1E1E24;
        margin-top: 18px;
        font-size: 13px;
        font-weight: 700;
    }

    /* Deep Midnight Navy Feature Container */
    .dark-section-card {
        background: #151D2A;
        border: 2.5px solid #1E1E24;
        border-radius: 28px;
        padding: 32px;
        color: #FFFFFF;
        box-shadow: 6px 6px 0px #1E1E24;
        margin: 28px 0;
        position: relative;
    }

    .dark-header-title {
        font-size: 30px;
        font-weight: 900;
        letter-spacing: -0.03em;
        text-align: center;
        color: #FFFFFF;
        margin-bottom: 12px;
    }

    /* Neo-Brutalist White Cards */
    .neo-card {
        background: #FFFFFF;
        border: 2.5px solid #1E1E24;
        border-radius: 22px;
        padding: 22px;
        box-shadow: 5px 5px 0px #1E1E24;
        margin-bottom: 20px;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }

    .neo-card:hover {
        transform: translate(-2px, -2px);
        box-shadow: 7px 7px 0px #1E1E24;
    }

    /* Side-by-side What is Good vs What is Not Good Comparison */
    .comp-good-neo {
        background: #EAF9F1;
        border: 2.5px solid #1E1E24;
        border-radius: 22px;
        padding: 24px;
        box-shadow: 5px 5px 0px #1E1E24;
    }

    .comp-not-good-neo {
        background: #FFF0EE;
        border: 2.5px solid #1E1E24;
        border-radius: 22px;
        padding: 24px;
        box-shadow: 5px 5px 0px #1E1E24;
    }

    .comp-header-title {
        font-size: 18px;
        font-weight: 900;
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 16px;
    }

    .comp-item-neo {
        background: #FFFFFF;
        border: 2px solid #1E1E24;
        border-radius: 12px;
        padding: 12px 16px;
        margin-bottom: 10px;
        font-size: 13px;
        font-weight: 700;
        display: flex;
        align-items: flex-start;
        gap: 10px;
        box-shadow: 3px 3px 0px #1E1E24;
    }

    /* Status Badges with Neo-Brutalist borders */
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 800;
        border: 2px solid #1E1E24;
        box-shadow: 2px 2px 0px #1E1E24;
    }
    .badge-approved { background-color: #D4F074; color: #1E1E24; }
    .badge-needs-changes { background-color: #FFA940; color: #1E1E24; }
    .badge-submitted { background-color: #9B72CF; color: #FFFFFF; }
    .badge-under-review { background-color: #74B9FF; color: #1E1E24; }
    .badge-not-submitted { background-color: #E2E8F0; color: #475569; }
    .badge-overdue { background-color: #FF7675; color: #FFFFFF; }

    /* Button Enhancements */
    .stButton>button {
        border: 2px solid #1E1E24 !important;
        border-radius: 9999px !important;
        font-weight: 800 !important;
        box-shadow: 3px 3px 0px #1E1E24 !important;
        transition: transform 0.1s ease, box-shadow 0.1s ease !important;
    }

    .stButton>button:hover {
        transform: translate(-1px, -1px) !important;
        box-shadow: 4px 4px 0px #1E1E24 !important;
    }

    div[data-testid="stSidebarNav"] {
        display: none;
    }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)


def render_badge(status: str) -> str:
    """Helper to return an HTML badge pill for a given status string."""
    s = (status or "").lower()
    if "approved" in s:
        cls = "badge-approved"
    elif "needs changes" in s:
        cls = "badge-needs-changes"
    elif "under review" in s:
        cls = "badge-under-review"
    elif "submitted" in s:
        cls = "badge-submitted"
    elif "overdue" in s or "rejected" in s:
        cls = "badge-overdue"
    else:
        cls = "badge-not-submitted"
    return f'<span class="badge {cls}">{status}</span>'
