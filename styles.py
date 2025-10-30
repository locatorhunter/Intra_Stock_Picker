"""
styles.py - All CSS styling for the Stock Hunter Dashboard
"""

APP_STYLE = """
<style>
/* ===== CSS Variables ===== */
:root {
    /* Colors */
    --primary-gradient-start: #0b1120;
    --primary-gradient-end: #101b3a;
    --sidebar-gradient-start: #111827;
    --sidebar-gradient-end: #1e293b;
    --accent-color: #6366f1;
    --accent-color-hover: #818cf8;
    --text-primary: #e6eef8;
    --text-secondary: #dbeafe;
    --text-header: #93c5fd;
    --border-color: rgba(255,255,255,0.08);
    
    /* Shadows */
    --shadow-sm: 0 2px 8px rgba(0,0,0,0.25);
    --shadow-md: 0 4px 14px rgba(0,0,0,0.35);
    --shadow-lg: 0 6px 20px rgba(0,0,0,0.45);
    
    /* Spacing */
    --spacing-sm: 8px;
    --spacing-md: 16px;
    --spacing-lg: 24px;
}

/* ===== Base App Styling ===== */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(180deg, var(--primary-gradient-start) 0%, var(--primary-gradient-end) 100%);
    color: var(--text-primary);
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, var(--sidebar-gradient-start) 0%, var(--sidebar-gradient-end) 100%);
    color: var(--text-primary);
    border-right: 1px solid var(--border-color);
    box-shadow: var(--shadow-lg);
}
[data-testid="stSidebar"] * {
    color: var(--text-secondary) !important;
}
[data-testid="stSidebar"] h1, 
[data-testid="stSidebar"] h2, 
[data-testid="stSidebar"] h3 {
    color: var(--text-header) !important;
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
    padding: 14px var(--spacing-md);
    margin-bottom: var(--spacing-sm);
    border: 1px solid var(--border-color);
    box-shadow: var(--shadow-sm);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
    -webkit-backface-visibility: hidden;
    backface-visibility: hidden;
}
.card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
}

/* ===== Responsive Tables ===== */
.watchlist-container { 
    font-size: 14px; 
    margin-top: var(--spacing-sm);
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
}
table {
    border-collapse: collapse;
    width: 100%;
    min-width: 600px; /* Ensure table doesn't get too narrow */
}
thead tr {
    background-color: rgba(255,255,255,0.08);
    font-weight: 600;
    position: sticky;
    top: 0;
    z-index: 1;
}
tbody tr:hover {
    background-color: rgba(255,255,255,0.07);
    transition: background 0.2s ease-in-out;
}
td, th {
    border-bottom: 1px solid var(--border-color);
    padding: var(--spacing-sm) 12px;
    white-space: nowrap;
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

/* ===== Enhanced Scrollbar ===== */
::-webkit-scrollbar {
    width: 8px;
    height: 8px; /* For horizontal scrolling */
}
::-webkit-scrollbar-track {
    background: rgba(255,255,255,0.05);
}
::-webkit-scrollbar-thumb {
    background: rgba(255,255,255,0.15);
    border-radius: 6px;
}
::-webkit-scrollbar-thumb:hover {
    background: rgba(255,255,255,0.25);
}

/* ===== Media Queries ===== */
@media screen and (max-width: 768px) {
    .header-banner h1 {
        font-size: 24px;
    }
    .header-banner p {
        font-size: 14px;
    }
    .card {
        padding: 12px;
    }
    .watchlist-container {
        margin: 0 -12px; /* Negative margin to allow full-width scrolling */
    }
    .section-title {
        font-size: 18px;
    }
    td, th {
        padding: 6px 10px;
    }
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
