"""Style helpers for the dashboard page."""

from __future__ import annotations


def build_dashboard_styles(t: dict[str, str]) -> str:
    return f"""
        <style>
            :root {{
                --pf-edge: {t["edge"]};
                --pf-text: {t["text"]};
                --pf-muted: {t["muted"]};
                --pf-shadow: {t["shadow"]};
                --pf-chip-bg: {t["chip_bg"]};
                --pf-chip-border: {t["chip_border"]};
                --pf-pos: {t["pos"]};
                --pf-neg: {t["neg"]};
            }}

            [data-testid="stAppViewContainer"] {{
                background: {t["bg"]};
            }}

            [data-testid="stAppViewContainer"] .main .block-container {{
                color: var(--pf-text) !important;
                max-width: 100% !important;
                width: 100% !important;
                padding-top: 1.05rem;
                padding-left: 1.2rem;
                padding-right: 1.2rem;
            }}

            [data-testid="stSidebarCollapsedControl"] {{
                background: transparent !important;
                border: none !important;
                box-shadow: none !important;
            }}

            [data-testid="collapsedControl"] {{
                background: transparent !important;
                border: none !important;
                box-shadow: none !important;
            }}

            [data-testid="stHeader"] {{
                background: transparent !important;
            }}

            [data-testid="stMarkdownContainer"] p,
            [data-testid="stMarkdownContainer"] span,
            [data-testid="stMarkdownContainer"] div,
            [data-testid="stMarkdownContainer"] li,
            [data-testid="stHeading"] h1,
            [data-testid="stHeading"] h2,
            [data-testid="stHeading"] h3,
            [data-testid="stHeadingWithActionElements"] h1,
            [data-testid="stHeadingWithActionElements"] h2,
            [data-testid="stHeadingWithActionElements"] h3,
            .stTextInput label,
            .stNumberInput label,
            .stDateInput label,
            .stSelectbox label,
            .stMultiSelect label,
            .stRadio label,
            .stCaption {{
                color: var(--pf-text) !important;
                font-family: "Trebuchet MS", "Franklin Gothic Medium", "Segoe UI", sans-serif !important;
            }}

            [data-testid="stSidebar"] {{
                background: {t["sidebar"]};
                border-right: 1px solid rgba(140, 162, 201, 0.2);
            }}

            [data-testid="stSidebar"] .st-key-sidebar_logout {{
                margin-top: 0.15rem;
                margin-bottom: 0.68rem;
            }}

            [data-testid="stSidebar"] div[class*="st-key-sidebar_nav_"] {{
                margin-top: 0.14rem;
            }}

            [data-testid="stSidebar"] .pf-sidebar-sep {{
                height: 1px;
                width: 100%;
                margin: 0.55rem 0 0.65rem 0;
                background: transparent;
            }}

            [data-testid="stSidebar"] .pf-nav-title {{
                color: var(--pf-muted) !important;
                font-size: 0.78rem;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                margin: 0 0 0.38rem 0.08rem;
                font-weight: 700;
            }}

            [data-testid="stSidebar"] h1,
            [data-testid="stSidebar"] h2,
            [data-testid="stSidebar"] h3,
            [data-testid="stSidebar"] p,
            [data-testid="stSidebar"] span,
            [data-testid="stSidebar"] label {{
                color: var(--pf-text) !important;
            }}

            .stButton > button,
            .stDownloadButton > button,
            .stFormSubmitButton > button {{
                background: linear-gradient(120deg, #ef4444, #b91c1c) !important;
                color: #ffffff !important;
                border: none !important;
                border-radius: 10px !important;
                font-weight: 700 !important;
                box-shadow: 0 8px 22px rgba(185, 28, 28, 0.34) !important;
            }}

            .pf-compact-download .stDownloadButton > button {{
                padding: 0.28rem 0.65rem !important;
                min-height: 2.1rem !important;
                font-size: 0.85rem !important;
            }}

            .pf-compact-download {{
                display: flex;
                justify-content: flex-end;
                margin-top: 0.48rem;
                padding-right: 0.9rem;
                width: 100%;
            }}

            [data-testid="stSidebar"] .stButton button[kind="secondary"] {{
                background: transparent !important;
                color: var(--pf-text) !important;
                border: 1px solid transparent !important;
                border-bottom: none !important;
                text-decoration: none !important;
                border-radius: 12px !important;
                box-shadow: none !important;
                justify-content: flex-start !important;
                padding: 0.62rem 0.82rem !important;
                min-height: 2.9rem !important;
                font-weight: 650 !important;
                font-size: 0.98rem !important;
                line-height: 1.2 !important;
                transition: background-color 140ms ease, border-color 140ms ease, transform 140ms ease !important;
            }}

            [data-testid="stSidebar"] .stButton button[kind="secondary"]:hover {{
                background: rgba(14, 22, 40, 0.62) !important;
                color: var(--pf-text) !important;
                border-color: rgba(125, 145, 255, 0.22) !important;
                transform: translateX(2px);
            }}

            [data-testid="stSidebar"] .stButton button[kind="primary"] {{
                background: linear-gradient(130deg, rgba(24, 42, 74, 0.98), rgba(15, 29, 55, 0.98)) !important;
                color: #eaf0ff !important;
                border: 1px solid rgba(122, 162, 255, 0.24) !important;
                border-bottom: none !important;
                text-decoration: none !important;
                border-radius: 12px !important;
                box-shadow: inset 0 0 0 1px rgba(125, 145, 255, 0.18) !important;
                justify-content: flex-start !important;
                padding: 0.62rem 0.82rem !important;
                min-height: 2.9rem !important;
                font-weight: 700 !important;
                font-size: 1rem !important;
                line-height: 1.2 !important;
            }}

            [data-testid="stSidebar"] .st-key-sidebar_logout .stButton > button {{
                background: linear-gradient(120deg, #ef4444, #b91c1c) !important;
                color: #ffffff !important;
                border: none !important;
                box-shadow: 0 8px 22px rgba(185, 28, 28, 0.34) !important;
            }}

            .pf-hero {{
                padding: 1rem 1.15rem;
                border-radius: 16px;
                background: {t["hero"]};
                border: 1px solid var(--pf-edge);
                box-shadow: var(--pf-shadow);
                margin-bottom: 0.8rem;
            }}

            .pf-hero h1 {{
                margin: 0;
                font-size: clamp(1.45rem, 2.3vw, 2.45rem);
                letter-spacing: 0.02em;
            }}

            .pf-hero p {{
                color: var(--pf-muted) !important;
                margin: 0.3rem 0 0;
                font-size: 0.96rem;
            }}

            .pf-card {{
                border: 1px solid var(--pf-edge);
                background: {t["panel"]};
                border-radius: 14px;
                padding: 0.9rem;
                box-shadow: var(--pf-shadow);
            }}

            .pf-kpi-title {{
                color: var(--pf-muted) !important;
                font-size: 0.84rem;
                text-transform: uppercase;
                letter-spacing: 0.06em;
            }}

            .pf-kpi-value {{
                color: var(--pf-text) !important;
                font-size: 1.35rem;
                margin-top: 0.2rem;
                font-weight: 700;
            }}

            .pf-kpi-note {{
                color: #44d2ff !important;
                font-size: 0.78rem;
                margin-top: 0.26rem;
            }}

            .pf-txn-card {{
                border: 1px solid var(--pf-edge);
                background: {t["txn_panel"]};
                border-radius: 12px;
                padding: 0.72rem 0.85rem;
                margin-bottom: 0.55rem;
            }}

            .pf-txn-row {{
                display: flex;
                justify-content: space-between;
                gap: 0.8rem;
                align-items: center;
            }}

            .pf-chip {{
                display: inline-block;
                padding: 0.12rem 0.5rem;
                border-radius: 999px;
                font-size: 0.73rem;
                color: var(--pf-text);
                border: 1px solid var(--pf-chip-border);
                background: var(--pf-chip-bg);
            }}

            .pf-upload-card {{
                border: 1px solid var(--pf-edge);
                background: {t["panel"]};
                border-radius: 14px;
                padding: 1rem 1.05rem;
                box-shadow: var(--pf-shadow);
                margin-top: 0.35rem;
            }}

            .pf-upload-subtitle {{
                color: var(--pf-muted) !important;
                margin: 0.2rem 0 0.85rem 0;
                font-size: 0.95rem;
            }}

            .pf-upload-chip {{
                display: inline-block;
                margin: 0.2rem 0.32rem 0.35rem 0;
                padding: 0.2rem 0.55rem;
                border-radius: 999px;
                font-size: 0.78rem;
                color: var(--pf-text);
                border: 1px solid var(--pf-chip-border);
                background: var(--pf-chip-bg);
            }}

            .stFileUploader > div {{
                border-radius: 12px !important;
                border: 1px solid var(--pf-edge) !important;
                background: rgba(17, 24, 39, 0.58) !important;
            }}

            .stFileUploader section {{
                padding: 0.75rem 0.85rem !important;
            }}

            .pf-upload-note {{
                color: var(--pf-muted) !important;
                font-size: 0.84rem;
                margin-top: 0.45rem;
            }}

            .pf-amount-pos {{
                color: var(--pf-pos);
                font-weight: 700;
            }}

            .pf-amount-neg {{
                color: var(--pf-neg);
                font-weight: 700;
            }}

            @keyframes pfFadeIn {{
                from {{ opacity: 0; transform: translateY(6px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
        </style>
    """
