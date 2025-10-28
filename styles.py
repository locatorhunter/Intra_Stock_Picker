"""
styles.py - All CSS styling for the Stock Hunter Dashboard
"""

APP_STYLE = """
<style>
/* ===== Base App Styling ===== */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(180deg, #0b1120 0%, #101b3a 100%);
    color: #e6eef8;
    font-family: 'Inter', sans-serif;
}

/* Sidebar background and text */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #111827 0%, #1e293b 100%);
    color: #f3f4f6;
    border-right: 1px solid rgba(255,255,255,0.05);
    box-shadow: 4px 0 16px rgba(0,0,0,0.4);
}
[data-testid="stSidebar"] * {
    color: #dbeafe !important;
}
[data-testid="stSidebar"] h1, 
[data-testid="stSidebar"] h2, 
[data-testid="stSidebar"] h3 {
    color: #93c5fd !important;
}

/* ===== Header Banner ===== */
.header-banner {
    background: linear-gradient(90deg, rgba(99,102,241,0.95), rgba(168,85,247,0.9));
    padding: 18px 28px;
    border-radius: 12px;
    color: white;
    box-shadow: 0 6px 20px rgba(0,0,0,0.45);
    margin-bottom: 18px;
    text-align: center;
    border: 1px solid rgba(255,255,255,0.15);
}
.header-banner h1 {
    font-size: 28px;
    margin: 0;
    font-weight: 700;
    letter-spacing: 0.5px;
}
.header-banner p {
    font-size: 15px;
    opacity: 0.9;
    margin-top: 4px;
}

/* ===== Cards ===== */
.card {
    background: rgba(255,255,255,0.04);
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 12px;
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 2px 8px rgba(0,0,0,0.25);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 14px rgba(0,0,0,0.35);
}

/* ===== Watchlist Table ===== */
.watchlist-container { font-size: 14px; margin-top: 8px; }
table {
    border-collapse: collapse;
    width: 100%;
}
thead tr {
    background-color: rgba(255,255,255,0.08);
    font-weight: 600;
}
tbody tr:hover {
    background-color: rgba(255,255,255,0.07);
    transition: background 0.2s ease-in-out;
}
td, th {
    border-bottom: 1px solid rgba(255,255,255,0.08);
    padding: 8px 12px;
}

/* ===== Badges & Tags ===== */
.badge {
    display:inline-block;
    padding:6px 10px;
    border-radius:14px;
    color:white;
    font-weight:600;
    margin-right:8px;
    margin-bottom:8px;
}
.badge-green { background: #10b981; }
.badge-red { background: #ef4444; }
.badge-yellow { background: #f59e0b; }
.badge-blue { background: #3b82f6; }

/* ===== Buttons ===== */
div.stButton > button {
    background: linear-gradient(90deg, #6366f1, #8b5cf6);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 8px 20px;
    font-weight: 600;
    transition: all 0.2s ease;
    box-shadow: 0 2px 6px rgba(0,0,0,0.25);
}
div.stButton > button:hover {
    background: linear-gradient(90deg, #818cf8, #a78bfa);
    transform: translateY(-1px);
}

/* ===== Section Titles ===== */
.section-title {
    font-size: 20px;
    font-weight: 700;
    margin-top: 16px;
    margin-bottom: 8px;
    color: #a5b4fc;
    border-left: 4px solid #6366f1;
    padding-left: 10px;
}

/* ===== Scrollbar ===== */
::-webkit-scrollbar {
    width: 8px;
}
::-webkit-scrollbar-thumb {
    background: rgba(255,255,255,0.15);
    border-radius: 6px;
}
::-webkit-scrollbar-thumb:hover {
    background: rgba(255,255,255,0.25);
}
</style>
"""

COMPACT_HEADER_STYLE = """
<style>
div.block-container {
    padding-top: 0rem;
}
section[data-testid="stSidebar"] > div:first-child {
    padding-top: 0.5rem !important;
}
</style>
"""
