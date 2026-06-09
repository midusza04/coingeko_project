"""
Generates the academic report SPRAWOZDANIE.docx.
Content source: SPRAWOZDANIE.md + DOCUMENTATION.md + .docs/

Usage:
    uv run python generate_sprawozdanie.py
"""

import base64
import time
from pathlib import Path

import requests
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor, Cm, Inches

OUTPUT = "SPRAWOZDANIE.docx"
TMP_DIR = Path("_tmp_diagrams")


# ── helpers ───────────────────────────────────────────────────────────────────

def set_cell_bg(cell, hex_color: str) -> None:
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def add_heading(doc: Document, text: str, level: int, color: str = "1F3864") -> None:
    p = doc.add_heading(text, level=level)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    for run in p.runs:
        run.font.color.rgb = RGBColor.from_string(color)


def add_para(doc: Document, text: str, *, bold: bool = False, italic: bool = False,
             size: int = 11, space_before: int = 0, space_after: int = 6) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    run = p.add_run(text)
    run.bold = bold
    run.italic = italic
    run.font.size = Pt(size)


def add_bullet(doc: Document, text: str, bold_prefix: str = "") -> None:
    p = doc.add_paragraph(style="List Bullet")
    if bold_prefix:
        r = p.add_run(bold_prefix + " ")
        r.bold = True
        r.font.size = Pt(11)
    r2 = p.add_run(text)
    r2.font.size = Pt(11)


def add_numbered(doc: Document, text: str) -> None:
    p = doc.add_paragraph(style="List Number")
    p.add_run(text).font.size = Pt(11)


def add_code(doc: Document, code: str) -> None:
    for line in code.rstrip().split("\n"):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        pPr = p._p.get_or_add_pPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), "F3F4F6")
        pPr.append(shd)
        ind = OxmlElement("w:ind")
        ind.set(qn("w:left"), "360")
        pPr.append(ind)
        run = p.add_run(line if line else " ")
        run.font.name = "Courier New"
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor.from_string("1E1B4B")
    doc.add_paragraph().paragraph_format.space_after = Pt(6)


def add_table(doc: Document, headers: list, rows: list,
              col_widths: list | None = None,
              header_bg: str = "1F3864") -> None:
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.LEFT

    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        set_cell_bg(cell, header_bg)
        p = cell.paragraphs[0]
        run = p.add_run(h)
        run.bold = True
        run.font.size = Pt(10)
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    for r_idx, row_data in enumerate(rows):
        bg = "EEF2FF" if r_idx % 2 == 0 else "FFFFFF"
        for c_idx, val in enumerate(row_data):
            cell = table.rows[r_idx + 1].cells[c_idx]
            set_cell_bg(cell, bg)
            run = cell.paragraphs[0].add_run(str(val))
            run.font.size = Pt(10)

    if col_widths:
        for row in table.rows:
            for i, cell in enumerate(row.cells):
                if i < len(col_widths):
                    cell.width = Cm(col_widths[i])

    doc.add_paragraph()


def render_mermaid(code: str, name: str) -> Path | None:
    TMP_DIR.mkdir(exist_ok=True)
    encoded = base64.urlsafe_b64encode(code.encode()).decode()
    url = f"https://mermaid.ink/img/{encoded}?theme=default&bgColor=ffffff"
    print(f"  Rendering diagram: {name}...")
    try:
        resp = requests.get(url, timeout=25)
        resp.raise_for_status()
        path = TMP_DIR / f"{name}.png"
        path.write_bytes(resp.content)
        print(f"  OK: {name} ({len(resp.content) // 1024} KB)")
        return path
    except Exception as exc:
        print(f"  Error {name}: {exc}")
        return None


def add_diagram(doc: Document, path: Path | None, caption: str, width_cm: float = 15.0) -> None:
    if path and path.exists():
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(str(path), width=Cm(width_cm))
        cap = doc.add_paragraph(caption)
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in cap.runs:
            run.font.size = Pt(9)
            run.font.italic = True
            run.font.color.rgb = RGBColor(0x6B, 0x72, 0x80)
        doc.add_paragraph()
    else:
        add_para(doc, f"[Diagram unavailable: {caption}]", italic=True)


# ── diagram definitions ───────────────────────────────────────────────────────

DIAGRAMS = {
    "erd": """\
erDiagram
    cryptocurrencies {
        TEXT id PK
        TEXT symbol
        TEXT name
    }
    market_snapshots {
        INTEGER record_id PK
        TEXT crypto_id FK
        DATE snapshot_date
        REAL price_usd
        REAL market_cap
        REAL total_volume
    }
    market_current {
        INTEGER record_id PK
        TEXT crypto_id FK
        DATETIME collected_at
        REAL price_usd
        REAL market_cap
        REAL total_volume
        REAL high_24h
        REAL low_24h
        REAL price_change_percentage_24h
        REAL price_change_percentage_7d
        INTEGER market_cap_rank
        REAL ath
    }
    cryptocurrencies ||--o{ market_snapshots : has_snapshots
    cryptocurrencies ||--o{ market_current : has_live_snapshots
""",
    "architecture": """\
flowchart TD
    subgraph PRESENT["Presentation layer"]
        NB["Jupyter Notebook\\n11 stages"]
        APP["Streamlit app.py\\n6 pages"]
    end
    subgraph STORAGE["Storage layer"]
        DB[("SQLite\\ncrypto_market.db")]
    end
    subgraph COLLECT["Data acquisition layer"]
        F1["fetch_market_chart"]
        F2["fetch_markets_current"]
    end
    API["CoinGecko API v3"]
    API --> F1
    API --> F2
    F1 --> DB
    F2 --> DB
    DB --> NB
    DB --> APP
""",
    "sequence": """\
sequenceDiagram
    participant U as User
    participant S as Streamlit
    participant A as CoinGecko API
    participant D as SQLite
    U->>S: Fetch Historical Data
    loop 5 coins
        S->>A: GET /coins/id/market_chart
        A-->>S: JSON prices market_caps volumes
        S->>D: INSERT OR REPLACE market_snapshots
        S->>S: sleep 10s
    end
    S-->>U: 1826 rows saved
""",
}


# ── build document ────────────────────────────────────────────────────────────

def build() -> None:
    print("Generating diagrams...")
    rendered = {k: render_mermaid(v, k) for k, v in DIAGRAMS.items()}
    time.sleep(0.3)

    doc = Document()
    for section in doc.sections:
        section.top_margin = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin = Cm(3.0)
        section.right_margin = Cm(2.0)

    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    # ══ TITLE PAGE ═══════════════════════════════════════════════════════════
    doc.add_paragraph()
    doc.add_paragraph()

    for text, size, bold, color in [
        ("UNIVERSITY OF TECHNOLOGY", 14, True, "1F3864"),
        ("Automation and Robotics — Master's Degree", 12, False, "404040"),
        ("Computer Science in Control and Management", 12, False, "404040"),
    ]:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(text)
        r.font.size = Pt(size)
        r.bold = bold
        r.font.color.rgb = RGBColor.from_string(color)

    doc.add_paragraph()
    doc.add_paragraph()

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Cryptocurrency Market Analysis System")
    r.bold = True
    r.font.size = Pt(24)
    r.font.color.rgb = RGBColor.from_string("1F3864")

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Project Report")
    r.font.size = Pt(14)
    r.italic = True
    r.font.color.rgb = RGBColor.from_string("555555")

    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Subject: Advanced Databases")
    r.bold = True
    r.font.size = Pt(13)

    doc.add_paragraph()
    doc.add_paragraph()

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Authors:\nMichał Dusza\nSzymon Bugajski\nMateusz Basiura")
    r.font.size = Pt(12)

    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("May 2026")
    r.font.size = Pt(12)
    r.font.color.rgb = RGBColor.from_string("555555")

    doc.add_page_break()

    # ══ TABLE OF CONTENTS ════════════════════════════════════════════════════
    add_heading(doc, "Table of Contents", 1)
    toc = [
        "1. Introduction and project objectives",
        "2. Functional scope",
        "3. Technologies used",
        "4. Repository structure",
        "5. Database design",
        "6. System architecture",
        "7. Implementation — data layer",
        "8. Implementation — presentation layer",
        "9. Analyses and visualisations",
        "10. Data collected in the project",
        "11. Running instructions",
        "12. Issues encountered and solutions",
        "13. Conclusions",
        "14. References",
    ]
    for item in toc:
        p = doc.add_paragraph(item)
        p.paragraph_format.space_after = Pt(3)
        for run in p.runs:
            run.font.size = Pt(11)

    doc.add_page_break()

    # ══ 1. INTRODUCTION ═════════════════════════════════════════════════════
    add_heading(doc, "1. Introduction and project objectives", 1)

    add_heading(doc, "1.1 Context", 2)
    add_para(doc,
        "The cryptocurrency market is characterised by exceptionally high volatility and generates "
        "vast amounts of data in real time. Monitoring and analysing this data requires reliable "
        "storage infrastructure and tools for interactive exploration. The project addresses this "
        "need by combining data retrieval via REST API, relational storage in SQLite, and "
        "interactive visualisations."
    )

    add_heading(doc, "1.2 Project objectives", 2)
    add_para(doc, "The aim of the project was to design and implement a system that:")
    for g in [
        "Automatically retrieves historical and current cryptocurrency market data from the public CoinGecko API.",
        "Stores data in a normalised relational SQLite database with keys, constraints, and indexes.",
        "Presents the collected data in interactive visualisations — in Jupyter and Streamlit.",
    ]:
        add_numbered(doc, g)

    add_heading(doc, "1.3 Motivation for the topic", 2)
    add_para(doc,
        "Cryptocurrencies are an excellent use case for time-series database systems: data is "
        "periodic, requires idempotent writes, and statistical analyses (correlations, volatility, "
        "distributions) are natural operations."
    )

    doc.add_page_break()

    # ══ 2. SCOPE ══════════════════════════════════════════════════════════════
    add_heading(doc, "2. Functional scope", 1)
    add_table(doc,
        ["Module", "Functionality"],
        [
            ["Data acquisition", "365-day history (price, market cap, volume) from CoinGecko API"],
            ["Data acquisition", "Current market snapshot (24h high/low, ATH, rank, supply)"],
            ["Database", "3 relational tables: FK, UNIQUE, indexes, 3NF normalisation"],
            ["Time series", "Line chart with MA, log scale, 6 filters"],
            ["Quantitative analysis", "Bar / Box / Violin with mean/max/min/std aggregations"],
            ["Market dashboard", "KPI, table, grouped bar, heatmap, treemap"],
            ["Correlation & volatility", "Correlation matrix, annualised volatility, BTC correlation"],
        ],
        col_widths=[4.5, 12.5],
    )

    # ══ 3. TECHNOLOGIES ═════════════════════════════════════════════════════
    add_heading(doc, "3. Technologies used", 1)
    add_table(doc,
        ["Component", "Technology", "Version", "Rationale"],
        [
            ["Language", "Python", "3.13", "Data-science ecosystem, SQLite in stdlib"],
            ["Package manager", "uv", "0.10.9+", "Deterministic uv.lock"],
            ["Database", "SQLite 3", "stdlib", "Zero-config, full SQL + FK"],
            ["Data source", "CoinGecko API v3", "public", "Free access, historical data"],
            ["Notebook", "JupyterLab", "4.x", "ipywidgets + interactive analyses"],
            ["Visualisation", "Plotly", "6.7", "Interactive charts"],
            ["Web application", "Streamlit", "1.57", "Rapid data-science UI"],
            ["Data", "pandas", "2.2+", "pd.read_sql as SQL↔Python layer"],
        ],
        col_widths=[4.0, 3.5, 2.5, 7.5],
    )

    doc.add_page_break()

    # ══ 4. REPO STRUCTURE ═════════════════════════════════════════════════════
    add_heading(doc, "4. Repository structure", 1)
    add_para(doc,
        "The project repository contains source code, the database, documentation, "
        "and the generated report. The role of each key file is described below."
    )
    add_table(doc,
        ["File / folder", "Role", "Status"],
        [
            ["app.py", "Main Streamlit application — ETL + 6 UI pages", "main"],
            ["crypto_market_analysis.ipynb", "Analytical notebook — 11 stages", "main"],
            ["crypto_market.db", "SQLite database (created automatically)", "main"],
            ["SPRAWOZDANIE.md", "Academic report (Markdown)", "documentation"],
            ["DOCUMENTATION.md", "Technical documentation", "documentation"],
            [".docs/", "Technical docs — architecture, model, API", "documentation"],
            ["main.py", "Simple JSON fetcher (3 coins, no DB)", "legacy"],
            ["generate_sprawozdanie.py", "Generator for this DOCX report", "tool"],
        ],
        col_widths=[5.5, 8.5, 3.5],
    )
    add_para(doc,
        "Data flow in the system:",
        bold=True, space_after=4,
    )
    add_code(doc,
        "CoinGecko API  -->  app.py / notebook  -->  crypto_market.db  -->  Plotly charts"
    )

    doc.add_page_break()

    # ══ 5. DATABASE ═══════════════════════════════════════════════════════════
    add_heading(doc, "5. Database design", 1)

    add_heading(doc, "5.1 Conceptual model (ERD)", 2)
    add_para(doc,
        "The database consists of three tables in a star schema: the cryptocurrencies dimension "
        "and two fact tables — market_snapshots (history) and market_current (live)."
    )
    add_diagram(doc, rendered.get("erd"), "Fig. 1. ERD — relational database schema")

    add_heading(doc, "5.2 DDL — table definitions", 2)
    add_code(doc, """\
CREATE TABLE IF NOT EXISTS cryptocurrencies (
    id     TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    name   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS market_snapshots (
    record_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    crypto_id     TEXT    NOT NULL,
    snapshot_date DATE    NOT NULL,
    price_usd     REAL,
    market_cap    REAL,
    total_volume  REAL,
    UNIQUE (crypto_id, snapshot_date),
    FOREIGN KEY (crypto_id) REFERENCES cryptocurrencies(id)
);

CREATE INDEX IF NOT EXISTS idx_snapshots_date
    ON market_snapshots(snapshot_date);

CREATE TABLE IF NOT EXISTS market_current (
    record_id                   INTEGER  PRIMARY KEY AUTOINCREMENT,
    crypto_id                   TEXT     NOT NULL,
    collected_at                DATETIME NOT NULL,
    price_usd                   REAL,  market_cap         REAL,
    total_volume                REAL,  high_24h           REAL,
    low_24h                     REAL,  price_change_24h   REAL,
    price_change_percentage_24h REAL,  price_change_percentage_7d REAL,
    market_cap_rank             INTEGER, circulating_supply REAL,
    total_supply                REAL,  max_supply         REAL,
    ath                         REAL,  ath_change_percentage REAL,
    FOREIGN KEY (crypto_id) REFERENCES cryptocurrencies(id)
);

CREATE INDEX IF NOT EXISTS idx_current_collected_at
    ON market_current(collected_at);""")

    add_heading(doc, "5.3 Table descriptions", 2)

    add_para(doc, "cryptocurrencies — coin dictionary", bold=True, space_after=2)
    add_table(doc,
        ["Column", "Type", "Constraints", "Description"],
        [
            ["id", "TEXT", "PRIMARY KEY", "CoinGecko identifier, e.g. bitcoin"],
            ["symbol", "TEXT", "NOT NULL", "Ticker, e.g. BTC"],
            ["name", "TEXT", "NOT NULL", "Full name, e.g. Bitcoin"],
        ],
        col_widths=[3.0, 2.0, 3.5, 8.0],
    )

    add_para(doc, "market_snapshots — daily history", bold=True, space_after=2)
    add_table(doc,
        ["Column", "Type", "Description"],
        [
            ["record_id", "INTEGER PK", "Surrogate key"],
            ["crypto_id", "TEXT FK", "→ cryptocurrencies.id"],
            ["snapshot_date", "DATE", "Date YYYY-MM-DD (UTC)"],
            ["price_usd", "REAL", "Closing price USD"],
            ["market_cap", "REAL", "Market capitalisation USD"],
            ["total_volume", "REAL", "24h volume USD"],
        ],
        col_widths=[3.5, 2.5, 10.5],
    )

    add_para(doc, "market_current — current snapshots (append-only)", bold=True, space_after=2)
    add_para(doc,
        "Stores rich live data from /coins/markets. Each fetch adds new rows "
        "with collected_at = UTC now — a history of successive fetches."
    )

    add_heading(doc, "5.4 Integrity constraints", 2)
    add_table(doc,
        ["Constraint", "Table", "Definition"],
        [
            ["PRIMARY KEY", "all", "id or record_id"],
            ["FOREIGN KEY", "market_snapshots, market_current", "crypto_id → cryptocurrencies.id"],
            ["UNIQUE", "market_snapshots", "(crypto_id, snapshot_date)"],
            ["NOT NULL", "market_snapshots", "crypto_id, snapshot_date"],
            ["NOT NULL", "market_current", "crypto_id, collected_at"],
        ],
        col_widths=[3.5, 5.0, 8.0],
    )

    add_heading(doc, "5.5 Indexes and normalisation", 2)
    add_bullet(doc, "PK autoindex on each table — lookup by record_id / id.", "")
    add_bullet(doc, "UNIQUE(crypto_id, snapshot_date) creates an implicit composite index.", "")
    add_bullet(doc, "idx_snapshots_date — filtering by date.", "")
    add_bullet(doc, "idx_current_collected_at — filtering by fetch time.", "")
    add_para(doc,
        "The schema satisfies 3NF: coin metadata only in cryptocurrencies; "
        "fact tables contain only crypto_id as FK."
    )

    doc.add_page_break()

    # ══ 6. ARCHITECTURE ═══════════════════════════════════════════════════════
    add_heading(doc, "6. System architecture", 1)
    add_para(doc, "The system is based on a three-layer architecture:")
    add_diagram(doc, rendered.get("architecture"),
                "Fig. 2. Three-layer system architecture", width_cm=14.0)
    add_diagram(doc, rendered.get("sequence"),
                "Fig. 3. Sequence diagram — historical data retrieval", width_cm=14.0)

    add_heading(doc, "6.1 Historical data flow", 2)
    for s in [
        "User initiates fetch (notebook Stage 5 or Streamlit Data Collection).",
        "For each of 5 coins: GET /coins/{id}/market_chart?days=365.",
        "Convert timestamp_ms → YYYY-MM-DD (UTC).",
        "INSERT OR REPLACE into market_snapshots (executemany).",
        "10 s delay between coins (API rate limit).",
    ]:
        add_numbered(doc, s)

    add_heading(doc, "6.2 Live data flow", 2)
    for s in [
        "GET /coins/markets?ids=bitcoin,ethereum,solana,binancecoin,ripple.",
        "INSERT do market_current z collected_at = UTC now.",
    ]:
        add_numbered(doc, s)

    doc.add_page_break()

    # ══ 7. DATA LAYER ═════════════════════════════════════════════════════════
    add_heading(doc, "7. Implementation — data layer", 1)

    add_heading(doc, "7.1 Database initialisation", 2)
    add_para(doc,
        "The create_database() function is called at app.py and notebook startup (Stage 3). "
        "The operation is idempotent thanks to CREATE TABLE IF NOT EXISTS."
    )

    add_heading(doc, "7.2 Idempotent writes", 2)
    add_code(doc, """\
conn.executemany(
    "INSERT OR REPLACE INTO market_snapshots "
    "(crypto_id, snapshot_date, price_usd, market_cap, total_volume) "
    "VALUES (?,?,?,?,?)",
    rows,
)
conn.commit()""")

    add_heading(doc, "7.3 Read into DataFrame", 2)
    add_code(doc,
        "@st.cache_data(ttl=60)\n"
        "def load_snapshots() -> pd.DataFrame:\n"
        "    df = pd.read_sql(\n"
        "        'SELECT s.snapshot_date, s.price_usd, s.market_cap,'\n"
        "        ' s.total_volume, c.name, c.symbol'\n"
        "        ' FROM market_snapshots s'\n"
        "        ' JOIN cryptocurrencies c ON s.crypto_id = c.id'\n"
        "        ' ORDER BY s.snapshot_date', conn)\n"
        "    return df"
    )

    doc.add_page_break()

    # ══ 8. PRESENTATION LAYER ═════════════════════════════════════════════════
    add_heading(doc, "8. Implementation — presentation layer", 1)

    add_heading(doc, "8.1 Jupyter notebook — 11 stages", 2)
    add_table(doc,
        ["Stage", "Description"],
        [
            ["1–2", "uv environment, imports, COINS / METRIC_MAP constants"],
            ["3–4", "DB DDL, coin list insertion"],
            ["5", "365-day history fetch + DB write (~1826 rows)"],
            ["6–7", "DB verification, load into pandas DataFrame"],
            ["8", "Time series — ipywidgets + Plotly"],
            ["9", "Quantitative analysis — bar/box/violin"],
            ["10", "Market dashboard — KPI, heatmap, treemap"],
            ["11", "Correlation & volatility — corr(), annualised volatility"],
        ],
        col_widths=[2.0, 15.5],
    )

    add_heading(doc, "8.2 Streamlit — 6 pages", 2)
    add_table(doc,
        ["Page", "Description"],
        [
            ["Overview", "DB statistics, date range, navigation"],
            ["Data Collection", "Historical and live fetch from CoinGecko"],
            ["Time Series", "Line chart — 6 sidebar filters"],
            ["Quantitative Analysis", "Bar / Box / Violin — 6 filters"],
            ["Market Dashboard", "KPI, table, grouped bar, heatmap, treemap"],
            ["Correlation & Volatility", "Correlation matrix, volatility, BTC correlation"],
        ],
        col_widths=[5.0, 12.5],
    )

    doc.add_page_break()

    # ══ 9. ANALYSES ═══════════════════════════════════════════════════════════
    add_heading(doc, "9. Analyses and visualisations", 1)

    add_heading(doc, "9.1 Time series", 2)
    add_para(doc,
        "Line chart with optional moving average (MA) and logarithmic scale. "
        "Enables comparison of coins at different price levels (BTC ~$90k vs XRP ~$2)."
    )

    add_heading(doc, "9.2 Quantitative analysis", 2)
    add_para(doc,
        "Bar chart — aggregation comparison. Box plot — median, quartiles, outliers. "
        "Violin plot — additionally estimated distribution density."
    )

    add_heading(doc, "9.3 Correlation and volatility", 2)
    add_code(doc, """\
returns = price_pivot.pct_change().dropna()
corr    = returns.corr()           # Pearson matrix
vol     = returns.std() * (365**0.5) * 100   # annualised volatility %""")

    doc.add_page_break()

    # ══ 10. DATA ══════════════════════════════════════════════════════════════
    add_heading(doc, "10. Data collected in the project", 1)
    add_table(doc,
        ["Table", "Rows", "Description"],
        [
            ["cryptocurrencies", "5", "BTC, ETH, SOL, BNB, XRP"],
            ["market_snapshots", "1,826", "366 days × 5 coins (2025-05-26 → 2026-05-26)"],
            ["market_current", "10", "2 live fetches × 5 coins"],
        ],
        col_widths=[5.0, 2.5, 10.0],
    )

    # ══ 11. RUNNING ═══════════════════════════════════════════════════════════
    add_heading(doc, "11. Running instructions", 1)
    add_code(doc, """\
# Installation
uv sync

# Web application (recommended)
uv run streamlit run app.py
# → http://localhost:8501

# Notebook
uv run jupyter lab crypto_market_analysis.ipynb""")
    add_para(doc,
        "On first run, go to Data Collection and fetch historical data."
    )

    doc.add_page_break()

    # ══ 12. ISSUES ════════════════════════════════════════════════════════════
    add_heading(doc, "12. Issues encountered and solutions", 1)
    add_table(doc,
        ["Issue", "Cause", "Solution"],
        [
            ["ModuleNotFoundError", "Required Python 3.14", "Changed to requires-python >= 3.13"],
            ["HTTP 429", "CoinGecko rate limit", "REQUEST_DELAY = 10 s + retry"],
            ["Empty dashboard", "market_current empty", "Computed from market_snapshots"],
            ["applymap deprecated", "pandas 2.1+", "Replaced with .map()"],
        ],
        col_widths=[4.5, 5.5, 7.5],
    )

    doc.add_page_break()

    # ══ 13. CONCLUSIONS ═══════════════════════════════════════════════════════
    add_heading(doc, "13. Conclusions", 1)

    add_heading(doc, "13.1 Achievements", 2)
    for title, desc in [
        ("End-to-end system", "API → SQLite → visualisations in Jupyter and Streamlit."),
        ("Correct DB schema", "3NF, FK, UNIQUE, indexes optimised for time-series queries."),
        ("Idempotent ETL", "INSERT OR REPLACE — safe re-fetching."),
        ("Reproducibility", "uv + uv.lock — identical environment on every machine."),
    ]:
        add_bullet(doc, desc, title + ":")

    add_heading(doc, "13.2 Possible extensions", 2)
    for e in [
        "More coins — extend the COINS list.",
        "Scheduling — APScheduler / cron.",
        "PostgreSQL — for larger scale and concurrency.",
        "CSV/Excel export — st.download_button in Streamlit.",
    ]:
        add_bullet(doc, e)

    add_heading(doc, "13.3 Final remarks", 2)
    add_para(doc,
        "SQLite is fully adequate for local analytical applications — 1,826 rows handled "
        "in under 50 ms thanks to properly designed indexes, including using "
        "UNIQUE as a composite index on (crypto_id, snapshot_date)."
    )

    doc.add_page_break()

    # ══ 14. REFERENCES ════════════════════════════════════════════════════════
    add_heading(doc, "14. References", 1)
    for i, item in enumerate([
        "CoinGecko API Documentation — https://www.coingecko.com/en/api/documentation",
        "SQLite Documentation — https://www.sqlite.org/docs.html",
        "pandas Documentation — https://pandas.pydata.org/docs/",
        "Plotly Python — https://plotly.com/python/",
        "Streamlit Documentation — https://docs.streamlit.io/",
        "uv Documentation — https://docs.astral.sh/uv/",
        "E. F. Codd, A Relational Model of Data for Large Shared Data Banks, CACM, 1970.",
        "C. J. Date, An Introduction to Database Systems, Addison-Wesley, 8th ed., 2003.",
        "W. McKinney, Python for Data Analysis, O'Reilly, 3rd ed., 2022.",
    ], 1):
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(1)
        p.paragraph_format.first_line_indent = Cm(-1)
        r = p.add_run(f"[{i}]  ")
        r.bold = True
        r.font.size = Pt(10)
        r = p.add_run(item)
        r.font.size = Pt(10)

    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(
        "Report prepared for the Advanced Databases course\n"
        "Michał Dusza · Szymon Bugajski · Mateusz Basiura · May 2026"
    )
    r.font.size = Pt(9)
    r.italic = True
    r.font.color.rgb = RGBColor(0x88, 0x88, 0x88)

    doc.save(OUTPUT)
    print(f"\nSaved: {OUTPUT}")

    for p in TMP_DIR.glob("*.png"):
        p.unlink()
    if TMP_DIR.exists() and not any(TMP_DIR.iterdir()):
        TMP_DIR.rmdir()


if __name__ == "__main__":
    build()
