"""
Generates SPRAWOZDANIE.docx from the project report content.
Run: uv run python generate_sprawozdanie.py
"""

from docx import Document
from docx.shared import Pt, RGBColor, Cm, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import copy

# ── Helpers ────────────────────────────────────────────────────────────────────

def set_cell_bg(cell, hex_color: str):
    """Set table cell background colour."""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def set_cell_border(cell, **kwargs):
    """Set borders on a table cell."""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = OxmlElement("w:tcBorders")
    for edge, attrs in kwargs.items():
        el = OxmlElement(f"w:{edge}")
        for k, v in attrs.items():
            el.set(qn(f"w:{k}"), v)
        tcBorders.append(el)
    tcPr.append(tcBorders)


def add_heading(doc: Document, text: str, level: int, color_hex="1F3864"):
    p = doc.add_heading(text, level=level)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    for run in p.runs:
        run.font.color.rgb = RGBColor.from_string(color_hex)
    return p


def add_para(doc: Document, text: str, bold=False, italic=False,
             size=11, space_before=0, space_after=6, color=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    run = p.add_run(text)
    run.bold = bold
    run.italic = italic
    run.font.size = Pt(size)
    if color:
        run.font.color.rgb = RGBColor.from_string(color)
    return p


def add_code(doc: Document, code: str):
    """Add a code block with monospace font and light grey background."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(8)
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), "F0F0F0")
    pPr.append(shd)
    # left indent
    ind = OxmlElement("w:ind")
    ind.set(qn("w:left"), "360")
    pPr.append(ind)
    run = p.add_run(code)
    run.font.name = "Courier New"
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor.from_string("2B2B2B")
    return p


def add_table(doc: Document, headers: list, rows: list,
              header_bg="1F3864", header_fg="FFFFFF",
              alt_bg="EEF2FF", col_widths=None):
    """Add a formatted table."""
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.LEFT

    # Header row
    hdr_cells = table.rows[0].cells
    for i, h in enumerate(headers):
        cell = hdr_cells[i]
        set_cell_bg(cell, header_bg)
        p = cell.paragraphs[0]
        run = p.add_run(h)
        run.bold = True
        run.font.size = Pt(10)
        run.font.color.rgb = RGBColor.from_string(header_fg)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Data rows
    for r_idx, row_data in enumerate(rows):
        row_cells = table.rows[r_idx + 1].cells
        bg = alt_bg if r_idx % 2 == 0 else "FFFFFF"
        for c_idx, val in enumerate(row_data):
            cell = row_cells[c_idx]
            set_cell_bg(cell, bg)
            p = cell.paragraphs[0]
            run = p.add_run(str(val))
            run.font.size = Pt(10)

    # Column widths
    if col_widths:
        for row in table.rows:
            for i, cell in enumerate(row.cells):
                if i < len(col_widths):
                    cell.width = Cm(col_widths[i])

    doc.add_paragraph()  # spacing after table
    return table


# ══════════════════════════════════════════════════════════════════════════════
# BUILD DOCUMENT
# ══════════════════════════════════════════════════════════════════════════════

def build():
    doc = Document()

    # ── Page margins ──────────────────────────────────────────────────────────
    for section in doc.sections:
        section.top_margin    = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin   = Cm(3.0)
        section.right_margin  = Cm(2.0)

    # ── Default paragraph font ─────────────────────────────────────────────────
    style = doc.styles["Normal"]
    font = style.font
    font.name = "Calibri"
    font.size = Pt(11)

    # ══════════════════════════════════════════════════════════════════════════
    # TITLE PAGE
    # ══════════════════════════════════════════════════════════════════════════
    doc.add_paragraph()
    doc.add_paragraph()

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("POLITECHNIKA")
    run.bold = True
    run.font.size = Pt(14)
    run.font.color.rgb = RGBColor.from_string("1F3864")

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run("Automatyka i Robotyka II Stopnia\nInformatyka w Sterowaniu i Zarządzaniu")
    run.font.size = Pt(12)
    run.font.color.rgb = RGBColor.from_string("404040")

    doc.add_paragraph()
    doc.add_paragraph()

    main_title = doc.add_paragraph()
    main_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = main_title.add_run("System Analizy Rynku Kryptowalut")
    run.bold = True
    run.font.size = Pt(22)
    run.font.color.rgb = RGBColor.from_string("1F3864")

    subject_line = doc.add_paragraph()
    subject_line.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subject_line.add_run("Sprawozdanie z projektu")
    run.font.size = Pt(14)
    run.font.color.rgb = RGBColor.from_string("555555")
    run.italic = True

    doc.add_paragraph()

    subject_box = doc.add_paragraph()
    subject_box.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subject_box.add_run("Przedmiot: Zaawansowane Bazy Danych")
    run.bold = True
    run.font.size = Pt(13)

    doc.add_paragraph()
    doc.add_paragraph()
    doc.add_paragraph()

    authors_para = doc.add_paragraph()
    authors_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = authors_para.add_run("Autorzy:\n")
    run.bold = True
    run.font.size = Pt(12)
    run = authors_para.add_run("Michał Dusza\nSzymon Bugajski\nMateusz Basiura")
    run.font.size = Pt(12)

    doc.add_paragraph()

    date_para = doc.add_paragraph()
    date_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = date_para.add_run("Maj 2026")
    run.font.size = Pt(12)
    run.font.color.rgb = RGBColor.from_string("555555")

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════════════════
    # 1. WSTĘP I CEL PROJEKTU
    # ══════════════════════════════════════════════════════════════════════════
    add_heading(doc, "1. Wstęp i cel projektu", 1)

    add_heading(doc, "1.1 Kontekst", 2)
    add_para(doc,
        "Rynek kryptowalut charakteryzuje się wyjątkowo wysoką zmiennością i generuje ogromną "
        "ilość danych w czasie rzeczywistym. Monitorowanie i analiza tych danych wymaga "
        "niezawodnej infrastruktury do ich przechowywania oraz narzędzi do interaktywnej "
        "eksploracji. Projekt odpowiada na to zapotrzebowanie, łącząc pobieranie danych "
        "przez REST API, relacyjne przechowywanie w bazie SQLite oraz interaktywne wizualizacje."
    )

    add_heading(doc, "1.2 Cel projektu", 2)
    add_para(doc, "Celem projektu było zaprojektowanie i zaimplementowanie systemu, który:")
    goals = [
        "Automatycznie pobiera historyczne i bieżące dane rynkowe kryptowalut z publicznego API CoinGecko.",
        "Przechowuje dane w znormalizowanej relacyjnej bazie danych SQLite z właściwie "
        "zdefiniowanymi kluczami, ograniczeniami i indeksami.",
        "Prezentuje zebrane dane w postaci interaktywnych wizualizacji statystycznych — "
        "zarówno w środowisku notebooka Jupyter, jak i przez przeglądarkową aplikację webową Streamlit.",
    ]
    for i, g in enumerate(goals, 1):
        p = doc.add_paragraph(style="List Number")
        p.add_run(g).font.size = Pt(11)

    add_heading(doc, "1.3 Motywacja wyboru tematu", 2)
    add_para(doc,
        "Kryptowaluty stanowią doskonały przypadek użycia dla systemów baz danych "
        "zorientowanych na szeregi czasowe: dane mają charakter cykliczny (codzienne "
        "aktualizacje), wymagają idempotentnego zapisu (ten sam rekord nie może być "
        "zduplikowany przy ponownym pobieraniu), a analizy statystyczne (korelacje, "
        "zmienność, rozkłady) są naturalnymi operacjami na tego rodzaju danych."
    )

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════════════════
    # 2. ZAKRES FUNKCJONALNY
    # ══════════════════════════════════════════════════════════════════════════
    add_heading(doc, "2. Zakres funkcjonalny", 1)

    add_table(doc,
        headers=["Moduł", "Funkcjonalność"],
        rows=[
            ["Pozyskiwanie danych",    "Pobieranie 365-dniowych danych historycznych (cena, kapitalizacja, wolumen) z CoinGecko API"],
            ["Pozyskiwanie danych",    "Pobieranie bieżącego snapshotu rynkowego (24h high/low, ATH, rank, supply)"],
            ["Baza danych",            "Trzy tabele relacyjne z kluczami obcymi, ograniczeniami UNIQUE i indeksami"],
            ["Analiza szeregów czasu", "Interaktywny wykres liniowy z filtrowaniem po monecie, zakresie dat, metryce; opcja MA i skali logarytmicznej"],
            ["Analiza ilościowa",      "Wykresy słupkowy / pudełkowy / skrzypcowy z agregacjami (mean, max, min, std)"],
            ["Dashboard rynkowy",      "Karty KPI, tabela podsumowująca, grupowany wykres słupkowy, heatmapa, treemap"],
            ["Korelacja i zmienność",  "Macierz korelacji, roczna zmienność, krocząca 30-dniowa korelacja z BTC"],
        ],
        col_widths=[4.5, 12.0],
    )

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════════════════
    # 3. ZASTOSOWANE TECHNOLOGIE
    # ══════════════════════════════════════════════════════════════════════════
    add_heading(doc, "3. Zastosowane technologie", 1)

    add_table(doc,
        headers=["Komponent", "Technologia", "Wersja", "Uzasadnienie"],
        rows=[
            ["Język programowania", "Python",    "3.13",   "Ekosystem data-science; SQLite w stdlib"],
            ["Menedżer pakietów",   "uv",        "0.10.9+","Szybki resolver, deterministyczny uv.lock"],
            ["Baza danych",         "SQLite 3",  "stdlib", "Zero-konfiguracyjna, jednolikowa, pełny SQL"],
            ["Źródło danych",       "CoinGecko API v3", "public", "Darmowy dostęp, dane historyczne i bieżące"],
            ["Notebook",            "JupyterLab","4.x",    "Interaktywne środowisko z ipywidgets"],
            ["Wizualizacja",        "Plotly",    "6.7",    "Interaktywne wykresy, plotly_dark template"],
            ["Interaktywność",      "ipywidgets","8.1",    "Natywne widgety w notebooku"],
            ["Aplikacja webowa",    "Streamlit", "1.57",   "Szybkie tworzenie UI data-science"],
            ["Manipulacja danymi",  "pandas",    "2.2+",   "DataFrame + pd.read_sql jako warstwa SQL↔Python"],
        ],
        col_widths=[4.0, 4.0, 2.5, 7.0],
    )

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════════════════
    # 4. PROJEKT BAZY DANYCH
    # ══════════════════════════════════════════════════════════════════════════
    add_heading(doc, "4. Projekt bazy danych", 1)

    add_heading(doc, "4.1 Model konceptualny", 2)
    add_para(doc,
        "Baza danych składa się z trzech tabel w relacji gwiazdy (star schema): "
        "tabela wymiarów cryptocurrencies oraz dwie tabele faktów: market_snapshots "
        "(dane historyczne) i market_current (bieżące snapshoty)."
    )

    add_para(doc, "Relacje między tabelami:", bold=True, space_after=2)
    rels = [
        "cryptocurrencies  (1) ──────── (∞)  market_snapshots",
        "cryptocurrencies  (1) ──────── (∞)  market_current",
    ]
    for r in rels:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(1)
        run = p.add_run(r)
        run.font.name = "Courier New"
        run.font.size = Pt(10)

    doc.add_paragraph()

    add_heading(doc, "4.2 Opis tabel", 2)

    # cryptocurrencies
    add_para(doc, "Tabela cryptocurrencies — słownik monet", bold=True, space_after=2)
    add_para(doc,
        "Tabela referencyjna zawierająca jeden rekord dla każdej śledzonej kryptowaluty. "
        "Pełni rolę wymiaru (dimension) w modelu gwiazdy.",
        space_after=4,
    )
    add_table(doc,
        headers=["Kolumna", "Typ", "Ograniczenia", "Opis"],
        rows=[
            ["id",     "TEXT",    "PRIMARY KEY",         "Kanoniczny identyfikator CoinGecko, np. bitcoin"],
            ["symbol", "TEXT",    "NOT NULL",             "Ticker giełdowy, np. BTC"],
            ["name",   "TEXT",    "NOT NULL",             "Pełna nazwa wyświetlana, np. Bitcoin"],
        ],
        col_widths=[3.5, 2.0, 3.5, 8.0],
    )

    # market_snapshots
    add_para(doc, "Tabela market_snapshots — historyczne dane dzienne", bold=True, space_after=2)
    add_para(doc,
        "Tabela faktów przechowująca dzienne wartości ceny, kapitalizacji i wolumenu obrotu. "
        "Jeden rekord = jeden dzień dla jednej monety. Źródło: endpoint /coins/{id}/market_chart.",
        space_after=4,
    )
    add_table(doc,
        headers=["Kolumna", "Typ", "Ograniczenia", "Opis"],
        rows=[
            ["record_id",     "INTEGER", "PK, AUTOINCREMENT",        "Klucz surogatowy"],
            ["crypto_id",     "TEXT",    "NOT NULL, FK",             "Odwołanie do cryptocurrencies.id"],
            ["snapshot_date", "DATE",    "NOT NULL, UNIQUE z FK",    "Data snapshotu YYYY-MM-DD (UTC)"],
            ["price_usd",     "REAL",    "—",                        "Cena zamknięcia w USD"],
            ["market_cap",    "REAL",    "—",                        "Całkowita kapitalizacja rynkowa w USD"],
            ["total_volume",  "REAL",    "—",                        "Wolumen obrotu 24h w USD"],
        ],
        col_widths=[3.5, 2.0, 3.5, 8.0],
    )

    # market_current
    add_para(doc, "Tabela market_current — bieżące snapshoty live", bold=True, space_after=2)
    add_para(doc,
        "Tabela faktów przechowująca bogate dane z bieżącego stanu rynku. "
        "Każde wywołanie funkcji pobierania tworzy nowy zestaw wierszy z aktualnym znacznikiem "
        "czasu — dane nie są nadpisywane, budując historię kolejnych pobrań. "
        "Źródło: endpoint /coins/markets.",
        space_after=4,
    )
    add_table(doc,
        headers=["Kolumna", "Typ", "Opis"],
        rows=[
            ["record_id",                   "INTEGER PK",  "Klucz surogatowy"],
            ["crypto_id",                   "TEXT FK",     "Odwołanie do cryptocurrencies.id"],
            ["collected_at",                "DATETIME",    "Znacznik czasu pobrania (UTC)"],
            ["price_usd",                   "REAL",        "Bieżąca cena w USD"],
            ["market_cap",                  "REAL",        "Kapitalizacja rynkowa"],
            ["total_volume",                "REAL",        "Wolumen 24h"],
            ["high_24h / low_24h",          "REAL",        "Maksimum i minimum ceny w ciągu 24h"],
            ["price_change_24h",            "REAL",        "Bezwzględna zmiana ceny w 24h (USD)"],
            ["price_change_percentage_24h", "REAL",        "Procentowa zmiana ceny w 24h"],
            ["price_change_percentage_7d",  "REAL",        "Procentowa zmiana ceny w 7 dniach"],
            ["market_cap_rank",             "INTEGER",     "Globalny ranking wg kapitalizacji"],
            ["circulating_supply",          "REAL",        "Liczba monet w obiegu"],
            ["total_supply / max_supply",   "REAL",        "Całkowita i maksymalna podaż"],
            ["ath",                         "REAL",        "Historyczne maksimum ceny w USD"],
            ["ath_change_percentage",       "REAL",        "Odległość od ATH w % (ujemna = poniżej ATH)"],
        ],
        col_widths=[5.5, 2.5, 9.5],
    )

    add_heading(doc, "4.3 Ograniczenia integralności", 2)
    add_table(doc,
        headers=["Ograniczenie", "Tabela", "Definicja", "Cel"],
        rows=[
            ["PRIMARY KEY",  "wszystkie",        "id lub record_id",                 "Jednoznaczna identyfikacja wiersza"],
            ["FOREIGN KEY",  "market_snapshots", "crypto_id → cryptocurrencies.id",  "Brak rekordów osieroconych"],
            ["FOREIGN KEY",  "market_current",   "crypto_id → cryptocurrencies.id",  "Brak rekordów osieroconych"],
            ["UNIQUE",       "market_snapshots", "(crypto_id, snapshot_date)",        "Jeden rekord na monetę na dzień; idempotentny INSERT OR REPLACE"],
            ["NOT NULL",     "market_snapshots", "crypto_id, snapshot_date",          "Klucz naturalny musi być zawsze podany"],
            ["NOT NULL",     "market_current",   "crypto_id, collected_at",           "Klucz identyfikujący musi być zawsze podany"],
        ],
        col_widths=[3.5, 3.5, 5.0, 5.5],
    )

    add_heading(doc, "4.4 Indeksy i optymalizacja zapytań", 2)
    add_para(doc,
        "Schemat wykorzystuje trzy mechanizmy indeksowania:"
    )

    idx_items = [
        ("Indeks z klucza głównego (automatyczny)",
         "SQLite automatycznie tworzy B-drzewo na kolumnie PRIMARY KEY każdej tabeli."),
        ("Indeks złożony z ograniczenia UNIQUE",
         "Ograniczenie UNIQUE(crypto_id, snapshot_date) na market_snapshots tworzy ukryty "
         "indeks złożony, który obsługuje wydajnie zapytania z równością na crypto_id "
         "i zakresem dat na snapshot_date — najczęstszy wzorzec zapytań w systemie."),
        ("Jawne indeksy dodatkowe",
         "idx_snapshots_date na kolumnie snapshot_date — optymalizuje filtrowanie bez warunku "
         "na crypto_id. idx_current_collected_at na collected_at — optymalizuje "
         "zapytania historyczne na tabeli market_current."),
    ]
    for title, desc in idx_items:
        p = doc.add_paragraph(style="List Bullet")
        run = p.add_run(title + ": ")
        run.bold = True
        run.font.size = Pt(11)
        run = p.add_run(desc)
        run.font.size = Pt(11)

    add_para(doc, "Przykład planu zapytania (EXPLAIN QUERY PLAN):", bold=True, space_before=8)
    add_code(doc,
        "SELECT snapshot_date, price_usd\n"
        "FROM   market_snapshots\n"
        "WHERE  crypto_id = 'bitcoin'\n"
        "  AND  snapshot_date BETWEEN '2025-01-01' AND '2025-12-31';\n\n"
        "-- Plan: SEARCH market_snapshots\n"
        "--       USING INDEX sqlite_autoindex_market_snapshots_1\n"
        "--       (crypto_id=? AND snapshot_date>? AND snapshot_date<?)"
    )

    add_heading(doc, "4.5 Normalizacja", 2)
    add_para(doc,
        "Schemat spełnia wymagania Trzeciej Postaci Normalnej (3NF)."
    )
    nf_items = [
        ("1NF", "Wszystkie wartości kolumn są atomowe. Brak grup powtarzających się."),
        ("2NF", "Tabele faktów używają kluczy surogatowych (record_id), więc każdy "
                "atrybut zależy od całego klucza. W tabeli cryptocurrencies symbol i name "
                "są w pełnej zależności funkcyjnej od id."),
        ("3NF", "Brak przechodnich zależności. Metadane monety (symbol, name) przechowywane "
                "są wyłącznie w cryptocurrencies — tabele faktów zawierają tylko klucz obcy "
                "crypto_id, nie powielają nazwy ani symbolu."),
    ]
    for nf, desc in nf_items:
        p = doc.add_paragraph(style="List Bullet")
        run = p.add_run(f"{nf}: ")
        run.bold = True
        run.font.size = Pt(11)
        run = p.add_run(desc)
        run.font.size = Pt(11)

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════════════════
    # 5. ARCHITEKTURA SYSTEMU
    # ══════════════════════════════════════════════════════════════════════════
    add_heading(doc, "5. Architektura systemu", 1)

    add_para(doc,
        "System zbudowany jest w oparciu o trójwarstwową architekturę: warstwa pozyskiwania "
        "danych, warstwa przechowywania oraz warstwa prezentacji."
    )

    add_code(doc,
        "┌────────────────────────────────────────────────────────┐\n"
        "│               WARSTWA PREZENTACJI                      │\n"
        "│   Jupyter Notebook (11 etapów)   Streamlit (6 stron)   │\n"
        "└──────────────────────┬─────────────────────────────────┘\n"
        "                       │ pd.read_sql (SELECT + JOIN)\n"
        "┌──────────────────────▼─────────────────────────────────┐\n"
        "│               WARSTWA PRZECHOWYWANIA                   │\n"
        "│         SQLite 3 — crypto_market.db                    │\n"
        "│  cryptocurrencies | market_snapshots | market_current  │\n"
        "└──────────────────────┬─────────────────────────────────┘\n"
        "                       │ INSERT OR REPLACE / INSERT\n"
        "┌──────────────────────▼─────────────────────────────────┐\n"
        "│               WARSTWA POZYSKIWANIA DANYCH              │\n"
        "│  fetch_market_chart()       fetch_markets_current()    │\n"
        "│       CoinGecko Public REST API v3                     │\n"
        "└────────────────────────────────────────────────────────┘"
    )

    add_heading(doc, "5.1 Przepływ danych — dane historyczne", 2)
    steps_hist = [
        "Użytkownik inicjuje pobieranie (notebook Stage 5 lub przycisk w Streamlit).",
        "Dla każdej z 5 monet wysyłane jest żądanie GET /coins/{id}/market_chart?days=365.",
        "Odpowiedź JSON zawiera tablice par [timestamp_ms, value] dla ceny, kapitalizacji i wolumenu.",
        "Timestamp milisekundowy konwertowany jest na datę YYYY-MM-DD (UTC).",
        "Wiersze zapisywane są za pomocą INSERT OR REPLACE do market_snapshots.",
        "Między kolejnymi żądaniami stosowane jest opóźnienie 10 sekund (limit API).",
    ]
    for i, s in enumerate(steps_hist, 1):
        p = doc.add_paragraph(style="List Number")
        p.add_run(s).font.size = Pt(11)

    add_heading(doc, "5.2 Przepływ danych — bieżący snapshot", 2)
    steps_live = [
        "Jedno żądanie GET /coins/markets?ids=bitcoin,ethereum,solana,binancecoin,ripple.",
        "API zwraca listę 5 obiektów z aktualnymi danymi rynkowymi.",
        "Dane wstawiane są do market_current z bieżącym znacznikiem czasu UTC.",
    ]
    for s in steps_live:
        p = doc.add_paragraph(style="List Number")
        p.add_run(s).font.size = Pt(11)

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════════════════
    # 6. IMPLEMENTACJA — WARSTWA DANYCH
    # ══════════════════════════════════════════════════════════════════════════
    add_heading(doc, "6. Implementacja — warstwa danych", 1)

    add_heading(doc, "6.1 Inicjalizacja bazy danych", 2)
    add_para(doc,
        "Funkcja create_database() wywoływana jest przy każdym uruchomieniu systemu "
        "(notebook: Stage 3; Streamlit: main()). Stosuje CREATE TABLE IF NOT EXISTS "
        "i CREATE INDEX IF NOT EXISTS, co sprawia, że operacja jest idempotentna — "
        "bezpieczna dla wielokrotnego uruchomienia:"
    )
    add_code(doc,
        "def create_database() -> None:\n"
        "    conn = sqlite3.connect(DB_PATH)\n"
        "    cur  = conn.cursor()\n"
        "    cur.execute(\"\"\"\n"
        "        CREATE TABLE IF NOT EXISTS market_snapshots (\n"
        "            record_id     INTEGER PRIMARY KEY AUTOINCREMENT,\n"
        "            crypto_id     TEXT    NOT NULL,\n"
        "            snapshot_date DATE    NOT NULL,\n"
        "            price_usd     REAL,\n"
        "            market_cap    REAL,\n"
        "            total_volume  REAL,\n"
        "            UNIQUE(crypto_id, snapshot_date),\n"
        "            FOREIGN KEY (crypto_id) REFERENCES cryptocurrencies(id)\n"
        "        )\n"
        "    \"\"\")\n"
        "    conn.commit()\n"
        "    conn.close()"
    )

    add_heading(doc, "6.2 Idempotentny zapis danych historycznych", 2)
    add_para(doc,
        "Zastosowanie INSERT OR REPLACE na ograniczeniu UNIQUE(crypto_id, snapshot_date) "
        "sprawia, że ponowne uruchomienie pobierania danych jest bezpieczne — nie tworzy "
        "duplikatów, a jedynie aktualizuje wartości dla dni, które już istnieją:"
    )
    add_code(doc,
        "conn.executemany(\n"
        "    \"INSERT OR REPLACE INTO market_snapshots\"\n"
        "    \"(crypto_id, snapshot_date, price_usd, market_cap, total_volume)\"\n"
        "    \"VALUES (?,?,?,?,?)\",\n"
        "    rows,   # lista tupli; parametry pozycyjne ? zapobiegają SQL Injection\n"
        ")\n"
        "conn.commit()"
    )

    add_heading(doc, "6.3 Odczyt do DataFrame", 2)
    add_para(doc,
        "Dane ładowane są jednorazowo jako denormalizowany DataFrame przez zapytanie "
        "JOIN, a następnie filtrowane w pamięci dla interaktywnych analiz. "
        "Dekorator @st.cache_data(ttl=60) eliminuje zbędne zapytania do bazy:"
    )
    add_code(doc,
        "@st.cache_data(ttl=60)\n"
        "def load_snapshots() -> pd.DataFrame:\n"
        "    conn = sqlite3.connect(DB_PATH)\n"
        "    df = pd.read_sql(\"\"\"\n"
        "        SELECT s.snapshot_date, s.price_usd, s.market_cap, s.total_volume,\n"
        "               c.name, c.symbol\n"
        "        FROM market_snapshots s\n"
        "        JOIN cryptocurrencies c ON s.crypto_id = c.id\n"
        "        ORDER BY s.snapshot_date\n"
        "    \"\"\", conn)\n"
        "    conn.close()\n"
        "    df[\"snapshot_date\"] = pd.to_datetime(df[\"snapshot_date\"])\n"
        "    return df"
    )

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════════════════
    # 7. IMPLEMENTACJA — WARSTWA PREZENTACJI
    # ══════════════════════════════════════════════════════════════════════════
    add_heading(doc, "7. Implementacja — warstwa prezentacji", 1)

    add_heading(doc, "7.1 Notebook Jupyter — 11 etapów", 2)
    add_table(doc,
        headers=["Etap", "Opis", "Kluczowe elementy"],
        rows=[
            ["1",  "Środowisko",            "Dokumentacja zarządzania pakietami przez uv"],
            ["2",  "Importy i stałe",        "DB_PATH, BASE_URL, REQUEST_DELAY=10, COINS, METRIC_MAP"],
            ["3",  "Inicjalizacja DB",       "create_database() — CREATE TABLE / INDEX"],
            ["4",  "Dane słownikowe",        "populate_cryptocurrencies() + weryfikacja SELECT"],
            ["5",  "Funkcje API + pobieranie","fetch_market_chart, store_market_chart; pętla po 5 monetach; 1826 wierszy"],
            ["6",  "Weryfikacja DB",         "Liczniki wierszy, zakres dat, kontrola spójności"],
            ["7",  "Ładowanie DataFrame",    "pd.read_sql z JOIN; rzutowanie typów"],
            ["8",  "Szeregi czasowe",        "6 widgetów ipywidgets; wykres liniowy Plotly"],
            ["9",  "Analiza ilościowa",      "6 widgetów ipywidgets; bar/box/violin"],
            ["10", "Dashboard rynkowy",      "build_dashboard_df(); 4 wykresy Plotly"],
            ["11", "Korelacja i zmienność",  "pct_change(), corr(), zmienność roczna, krocząca korelacja 30d"],
        ],
        col_widths=[1.5, 4.5, 11.5],
    )

    add_heading(doc, "7.2 Aplikacja webowa Streamlit — 6 stron", 2)
    add_para(doc,
        "Aplikacja app.py dostępna pod adresem http://localhost:8501 oferuje wszystkie "
        "analizy notebooka w przeglądarce, bez potrzeby środowiska Jupyter. "
        "Nawigacja realizowana jest przez st.radio w lewym pasku bocznym."
    )
    add_table(doc,
        headers=["Strona", "Opis"],
        rows=[
            ["🏠 Overview",               "Metryki DB (liczba monet, snapshotów, zakres dat), tabela nawigacji"],
            ["📥 Data Collection",        "Przyciski pobierania danych historycznych i live; pasek postępu; podsumowanie DB"],
            ["📈 Time Series",            "Wykres liniowy; 6 filtrów (monety, daty, metryka, MA, skala log)"],
            ["📊 Quantitative Analysis",  "Bar/Box/Violin; 6 filtrów (monety, metryka, okres, agregacja, sortowanie, typ)"],
            ["🗺️ Market Dashboard",       "Karty KPI; tabela; grupowany słupkowy; heatmapa zmian; treemap kapitalizacji"],
            ["🔗 Correlation & Volatility","Macierz korelacji; zmienność roczna; krocząca 30-dniowa korelacja z BTC"],
        ],
        col_widths=[4.5, 13.0],
    )

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════════════════
    # 8. OPIS ANALIZ I WIZUALIZACJI
    # ══════════════════════════════════════════════════════════════════════════
    add_heading(doc, "8. Opis analiz i wizualizacji", 1)

    add_heading(doc, "8.1 Analiza szeregów czasowych", 2)
    add_para(doc,
        "Wykres liniowy prezentuje ewolucję wybranej metryki w czasie. Opcja średniej "
        "kroczącej (MA) wygładza szum krótkoterminowy i ujawnia trendy. Skala logarytmiczna "
        "umożliwia porównywanie monet o bardzo różnych cenach (np. BTC ~$90 000 vs XRP ~$2)."
    )

    add_heading(doc, "8.2 Analiza ilościowa", 2)
    add_para(doc,
        "Wykres słupkowy umożliwia porównanie zagregowanych wartości. "
        "Wykres pudełkowy (Box plot) prezentuje rozkład: medianę, kwartyle i wartości odstające. "
        "Wykres skrzypcowy (Violin plot) dodaje szacowanie gęstości rozkładu. "
        "Wszystkie trzy typy obsługują te same 6 filtrów."
    )

    add_heading(doc, "8.3 Macierz korelacji", 2)
    add_para(doc,
        "Korelacja Pearsona obliczana jest na dziennych zwrotach (nie na cenach), "
        "co eliminuje trend i skupia się na współzależności ruchów:"
    )
    add_code(doc,
        "price_pivot = df.pivot(index=\"snapshot_date\", columns=\"name\", values=\"price_usd\")\n"
        "returns     = price_pivot.pct_change().dropna()\n"
        "corr        = returns.corr()    # macierz Pearsona n×n"
    )

    add_heading(doc, "8.4 Zmienność roczna (Annualised Volatility)", 2)
    add_para(doc, "Standardowa miara zmienności finansowej:")
    add_code(doc,
        "sigma_roczna = std(dzienne_zwroty) × sqrt(365) × 100 [%]"
    )
    add_para(doc,
        "Wartość ta mówi, o ile procent może zmienić się cena w ciągu roku "
        "przy założeniu stacjonarności zmienności."
    )

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════════════════
    # 9. DANE ZEBRANE W PROJEKCIE
    # ══════════════════════════════════════════════════════════════════════════
    add_heading(doc, "9. Dane zebrane w projekcie", 1)

    add_heading(doc, "9.1 Stan bazy danych", 2)
    add_table(doc,
        headers=["Tabela", "Wiersze", "Opis"],
        rows=[
            ["cryptocurrencies", "5",     "Bitcoin, Ethereum, Solana, BNB, XRP"],
            ["market_snapshots", "1 826", "366 dni × 5 monet (rok historii, 2025-05-26 → 2026-05-26)"],
            ["market_current",   "10",    "2 pobierania live × 5 monet"],
        ],
        col_widths=[5.0, 2.5, 10.0],
    )

    add_heading(doc, "9.2 Śledzone kryptowaluty", 2)
    add_table(doc,
        headers=["Symbol", "Nazwa", "Typ / charakterystyka"],
        rows=[
            ["BTC", "Bitcoin",           "Proof-of-Work, pierwsza kryptowaluta, cyfrowe złoto"],
            ["ETH", "Ethereum",          "Smart contracts, Proof-of-Stake po The Merge"],
            ["SOL", "Solana",            "High-throughput PoS, niskie opłaty transakcyjne"],
            ["BNB", "BNB (Binance Coin)","Token ekosystemu giełdy Binance"],
            ["XRP", "XRP (Ripple)",      "Sieć do rozliczeń płatności instytucjonalnych"],
        ],
        col_widths=[2.0, 4.5, 11.0],
    )
    add_para(doc,
        "Wybór obejmuje pięć największych kryptowalut pod względem kapitalizacji rynkowej, "
        "reprezentujących różne technologie i przypadki użycia.",
        italic=True,
    )

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════════════════
    # 10. INSTRUKCJA URUCHOMIENIA
    # ══════════════════════════════════════════════════════════════════════════
    add_heading(doc, "10. Instrukcja uruchomienia", 1)

    add_heading(doc, "Wymagania wstępne", 2)
    reqs = [
        "Python 3.13 (zalecane zarządzanie przez uv)",
        "uv — instalacja: pip install uv lub docs.astral.sh/uv",
        "Dostęp do internetu (CoinGecko API)",
    ]
    for r in reqs:
        p = doc.add_paragraph(style="List Bullet")
        p.add_run(r).font.size = Pt(11)

    add_heading(doc, "Krok 1 — Instalacja zależności", 2)
    add_code(doc, "cd coingeko_project\nuv sync")

    add_heading(doc, "Krok 2 — Uruchomienie notebooka Jupyter", 2)
    add_code(doc,
        "# Rejestracja kernela (tylko raz):\n"
        "uv run python -m ipykernel install --user \\\n"
        "    --name crypto-market-analysis \\\n"
        "    --display-name \"Python (crypto-market-analysis)\"\n\n"
        "# Uruchomienie JupyterLab:\n"
        "uv run jupyter lab"
    )
    add_para(doc,
        "Otworzyć plik crypto_market_analysis.ipynb i wybrać kernel "
        "Python (crypto-market-analysis). Wykonać komórki od góry (Run → Run All Cells)."
    )

    add_heading(doc, "Krok 3 — Uruchomienie aplikacji Streamlit", 2)
    add_code(doc, "uv run streamlit run app.py")
    add_para(doc,
        "Aplikacja dostępna pod adresem http://localhost:8501. "
        "Po pierwszym uruchomieniu przejść do strony Data Collection i pobrać dane historyczne."
    )

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════════════════
    # 11. NAPOTKANE PROBLEMY I ROZWIĄZANIA
    # ══════════════════════════════════════════════════════════════════════════
    add_heading(doc, "11. Napotkane problemy i rozwiązania", 1)

    add_table(doc,
        headers=["Problem", "Przyczyna", "Zastosowane rozwiązanie"],
        rows=[
            ["ModuleNotFoundError przy starcie kernela",
             "pyproject.toml wymagał Pythona 3.14, który nie był zainstalowany",
             "Zmiana requires-python >= 3.14 na >= 3.13; aktualizacja .python-version"],
            ["HTTP 429 Too Many Requests",
             "Darmowy tier CoinGecko ma limit ~10–30 req/min",
             "Zwiększono REQUEST_DELAY do 10 s; dodano retry z opóźnieniem"],
            ["Pusty dashboard (Stage 10)",
             "Tabela market_current była pusta; dashboard bazował wyłącznie na tej tabeli",
             "Przebudowa Stage 10 — obliczanie zmian z market_snapshots (dane historyczne zawsze dostępne)"],
            ["AttributeError: DataFrame has no attribute 'applymap'",
             "applymap usunięty w pandas 2.1",
             "Zmiana .applymap(...) na .map(...) w app.py"],
            ["DeprecationWarning w pyproject.toml",
             "Przestarzała sekcja [tool.uv.dev-dependencies]",
             "Migracja do nowej składni [dependency-groups]"],
            ["KeyboardInterrupt podczas time.sleep(20)",
             "Użytkownik przerwał oczekiwanie między żądaniami API",
             "Dodano dedykowaną komórkę retry; dane live ostatecznie pobrane pomyślnie"],
        ],
        col_widths=[4.5, 5.5, 7.5],
    )

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════════════════
    # 12. WNIOSKI
    # ══════════════════════════════════════════════════════════════════════════
    add_heading(doc, "12. Wnioski", 1)

    add_heading(doc, "12.1 Osiągnięcia", 2)
    achievements = [
        ("Kompletny system end-to-end",
         "Od pobrania surowych danych przez REST API, przez relacyjną bazę danych, "
         "do interaktywnych wizualizacji — w dwóch niezależnych interfejsach (Jupyter i Streamlit)."),
        ("Poprawny projekt bazy danych",
         "Schemat spełnia 3NF, zawiera klucze obce, ograniczenie UNIQUE na kluczu naturalnym "
         "(crypto_id, snapshot_date) oraz indeksy wspierające najczęstsze wzorce zapytań."),
        ("Idempotentne pobieranie danych",
         "INSERT OR REPLACE sprawia, że ponowne uruchomienie skryptu nigdy nie duplikuje "
         "danych — tylko aktualizuje istniejące i dodaje nowe rekordy."),
        ("Reprodukowalność środowiska",
         "uv + uv.lock gwarantują identyczne środowisko Python na każdej maszynie."),
    ]
    for title, desc in achievements:
        p = doc.add_paragraph(style="List Bullet")
        run = p.add_run(title + ": ")
        run.bold = True
        run.font.size = Pt(11)
        run = p.add_run(desc)
        run.font.size = Pt(11)

    add_heading(doc, "12.2 Możliwe rozszerzenia", 2)
    extensions = [
        "Zwiększenie liczby monitorowanych monet — wystarczy rozszerzyć listę COINS.",
        "Automatyczny harmonogram pobierania — APScheduler lub Windows Task Scheduler.",
        "PostgreSQL zamiast SQLite — dla większej liczby użytkowników jednoczesnych.",
        "Eksport do CSV/Excel — przycisk st.download_button w Streamlit.",
        "Powiadomienia cenowe — alerty mailowe lub webhook gdy cena przekroczy próg.",
    ]
    for e in extensions:
        p = doc.add_paragraph(style="List Bullet")
        p.add_run(e).font.size = Pt(11)

    add_heading(doc, "12.3 Uwagi końcowe", 2)
    add_para(doc,
        "Projekt pokazuje, że SQLite jest w pełni wystarczający do analitycznych zastosowań "
        "lokalnych o umiarkowanej skali — baza z 1826 wierszami obsługuje wszystkie zapytania "
        "poniżej 50 ms. Prawidłowe zaplanowanie indeksów (w tym wykorzystanie ograniczenia "
        "UNIQUE jako indeksu złożonego) jest kluczowe dla wydajności zapytań z filtrowaniem "
        "zakresowym na datach."
    )

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════════════════
    # 13. LITERATURA
    # ══════════════════════════════════════════════════════════════════════════
    add_heading(doc, "13. Literatura i źródła", 1)

    literature = [
        "CoinGecko API Documentation — https://www.coingecko.com/en/api/documentation",
        "SQLite Documentation — https://www.sqlite.org/docs.html",
        "pandas Documentation — https://pandas.pydata.org/docs/",
        "Plotly Python Documentation — https://plotly.com/python/",
        "Streamlit Documentation — https://docs.streamlit.io/",
        "uv Documentation — https://docs.astral.sh/uv/",
        "ipywidgets Documentation — https://ipywidgets.readthedocs.io/",
        "E. F. Codd, A Relational Model of Data for Large Shared Data Banks, "
        "Communications of the ACM, 1970.",
        "C. J. Date, An Introduction to Database Systems, Addison-Wesley, 8th ed., 2003.",
        "W. McKinney, Python for Data Analysis, O'Reilly, 3rd ed., 2022.",
    ]
    for i, item in enumerate(literature, 1):
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(1)
        p.paragraph_format.first_line_indent = Cm(-1)
        run = p.add_run(f"[{i}]  ")
        run.bold = True
        run.font.size = Pt(10)
        run = p.add_run(item)
        run.font.size = Pt(10)

    # ── Footer note ────────────────────────────────────────────────────────────
    doc.add_paragraph()
    footer_p = doc.add_paragraph()
    footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = footer_p.add_run(
        "Sprawozdanie przygotowane w ramach przedmiotu Zaawansowane Bazy Danych\n"
        "Michał Dusza · Szymon Bugajski · Mateusz Basiura · Maj 2026"
    )
    run.font.size = Pt(9)
    run.italic = True
    run.font.color.rgb = RGBColor.from_string("888888")

    # ── Save ───────────────────────────────────────────────────────────────────
    out = "SPRAWOZDANIE.docx"
    doc.save(out)
    print(f"Saved: {out}")


if __name__ == "__main__":
    build()
