"""
Rebuild fee-table rows from a PDF's embedded text layer.

The 2025-26 fee PDFs are scans with an OCR text layer from the scanner, so
there are no vector table lines for pdfplumber's table finder. Instead we use
word positions (pdfplumber.extract_words):

  1. a table starts at its "Odd / Even Semester(s)" heading line
  2. rows are anchored by their serial number ("1.", "2.", OCR "t2.") or a
     "Total ..." label; values and label words go to the nearest anchor by y
  3. value x-positions are clustered into columns; each column is named from
     the header words above it (General, SC/ST, income group, DASA, All) and
     assigned to the nearest odd/even semester heading
  4. the programme comes from the nearest "Fee structure for ..." title above

Each row becomes one self-contained line, e.g.
  "Fee PG 2025-26 | M.Tech. (Full-time) | Odd semester | Tuition Fee | General: 35000 | SC/ST: -"
"""

import argparse
import os
import re
import sys

import pdfplumber
from langchain_core.documents import Document

from rag.metadata import readable_title

# OCR confusions inside numbers: t000.00 -> 1000.00, 1s00.00 -> 1500.00
OCR_DIGIT_MAP = str.maketrans({"t": "1", "r": "1", "l": "1", "I": "1", "i": "1",
                               "s": "5", "S": "5", "o": "0", "O": "0"})
AMOUNT_PATTERN = re.compile(r"^[\dtrlIisSoO][\dtrlIisSoO,]*(?:[.,]\d\d)?$")

# Serial numbers in the S. No. column, including OCR noise ("I", "t2.", "r0.", "\45")
SERIAL_PATTERN = re.compile(r"^\\?[\dIiltr]{1,3}\.?$")

MIN_VALUE_X = 200        # numbers left of this are serial numbers
MAX_SERIAL_X = 150       # serial numbers are left of this
ANCHOR_MERGE_Y = 3       # anchors closer than this are one row ("Grant Total")
OWN_ROW_Y = 6            # a value row this far from every anchor is its own row
BELOW_LAST_ROW_Y = 8     # label words further below the last row are notes
LINE_MERGE_Y = 5         # label words this close in y form one line
COLUMN_GAP = 25          # x gap that separates two value columns
COLUMN_WINDOW = 40       # header words within this x distance name a column

SECTION_LINE = re.compile(r"^\s*(?:[A-D]\.|\(common|s\.\s*no|note\b)", re.IGNORECASE)

TITLE_PATTERN = re.compile(
    r"fee structure for (.*?)\s+(?:students\s+)?admi\w+\s+"
    r"(?:under\s+(.*?)\s+programme\s+)?in\s+the\s+session",
    re.IGNORECASE,
)


def _center(word) -> float:
    return (word["x0"] + word["x1"]) / 2


def _clean_amount(text: str) -> str | None:
    """
    Normalize an OCR'd amount ("t000.00" -> "1000", "20,834.00" -> "20834").
    Returns None if the token is not an amount.
    """
    if not AMOUNT_PATTERN.match(text) or not re.search(r"\d", text):
        return None

    # "62500,00": comma used as the decimal point
    text = re.sub(r",(\d\d)$", r".\1", text)
    value = text.translate(OCR_DIGIT_MAP).replace(",", "")

    if not re.fullmatch(r"\d+(?:\.\d\d)?", value):
        return None

    return value[:-3] if value.endswith(".00") else value


def _same_line(words, y, tolerance=4):
    return sorted((w for w in words if abs(w["top"] - y) < tolerance),
                  key=lambda w: w["x0"])


def _group_lines(words, tolerance=LINE_MERGE_Y) -> list[list[dict]]:
    """
    Group words into lines by y, each line sorted by x.
    """
    lines = []

    for word in sorted(words, key=lambda w: w["top"]):
        if lines and abs(word["top"] - lines[-1][0]["top"]) <= tolerance:
            lines[-1].append(word)
        else:
            lines.append([word])

    return [sorted(line, key=lambda w: w["x0"]) for line in lines]


def _programme_from_title(text: str) -> str:
    """
    "Fee structure for M.Tech. (Full-time) students admitted in the session"
    -> "M.Tech. (Full-time)"; Study in India pages get "(Study in India)".
    """
    text = re.sub(r"(?i)session(?=\d)", "session ", text)
    match = TITLE_PATTERN.search(text)

    if not match:
        return re.sub(r"(?i)^.*?fee structure for\s+", "", text).strip()

    programme = match.group(1).strip()
    if match.group(2):
        programme += f" ({match.group(2).strip()})"

    return programme


def _find_titles(words) -> list[tuple[float, str]]:
    """
    (y, programme) of every "Fee structure for ..." title on the page.
    """
    titles = []

    for word in words:
        if word["text"].lower() != "fee":
            continue

        line = _same_line(words, word["top"])
        following = [w for w in line if w["x0"] > word["x0"]]

        if not following or following[0]["text"].lower() != "structure":
            continue

        text = " ".join(w["text"] for w in line if w["x0"] >= word["x0"])

        # A title may wrap onto the next line ("... in the" / "session 2025-26")
        if "session" not in text.lower():
            below = [w for w in words if 4 <= w["top"] - word["top"] < 16]
            text += " " + " ".join(w["text"] for w in sorted(below, key=lambda w: w["x0"]))

        titles.append((word["top"], _programme_from_title(text)))

    return titles


def _cluster_columns(xs: list[float]) -> list[tuple[float, float]]:
    """
    1-D clustering of value x-positions into column ranges.
    """
    columns = []

    for x in sorted(xs):
        if columns and x - columns[-1][1] <= COLUMN_GAP:
            columns[-1][1] = x
        else:
            columns.append([x, x])

    return [(start, end) for start, end in columns]


def _column_name(header_text: str, band_text: str) -> str:
    """
    Map the header words above a column to a short name.
    """
    text = header_text.lower()
    prefix = "General/OBC " if "obc" in band_text.lower() else ""

    if "below" in text or "most" in text:
        return f"{prefix}income below 1 lakh".strip().capitalize()
    if "1 lac to 5" in text or "other" in text:
        return f"{prefix}income 1-5 lakh".strip().capitalize()
    if "above" in text:
        return f"{prefix}income above 5 lakh".strip().capitalize()
    if "sc/st" in text or "sc/" in text:
        return "SC/ST/PH" if "ph" in text else "SC/ST"
    if "obc" in text:
        return "General/OBC"
    if "general" in text or "eneral" in text:
        return "General"
    if "ciwg" in text:
        return "DASA CIWG"
    if "dasa" in text or "iccr" in text:
        return "DASA, MEA & ICCR" if "mea" in text else "DASA & ICCR"
    if "all" in text or "categor" in band_text.lower():
        return "All categories"

    return "Amount"


EVEN_MARGIN = 30         # a column this far left of "Even" still belongs to it


def _semester_for(center: float, headings) -> str:
    """
    A column belongs to the Even semester if it lies right of the Even
    heading's left edge (minus a margin), otherwise to the Odd semester.
    """
    if not headings:
        return "Per semester"

    if len(headings) == 1:
        return headings[0]["label"]

    even = [h for h in headings if h["label"] == "Even semester"]
    odd = [h for h in headings if h["label"] == "Odd semester"]

    if even and center >= even[0]["x0"] - EVEN_MARGIN:
        return "Even semester"

    return "Odd semester" if odd else headings[0]["label"]


def _semester_headings(header_line) -> list[dict]:
    """
    "Odd" / "Even" headings of a table, or one combined heading for
    "Odd Semester & Even Semester".
    """
    headings = []

    for word in header_line:
        lowered = word["text"].lower()
        if lowered.startswith("od"):
            headings.append({**word, "label": "Odd semester"})
        elif lowered.startswith("eve"):
            headings.append({**word, "label": "Even semester"})

    if "&" in [w["text"] for w in header_line] and len(headings) == 2:
        return [{**headings[0], "label": "Odd & even semester"}]

    return headings


def _table_starts(words) -> list[list[dict]]:
    """
    Lines that start a table: they contain an Odd/Even semester heading.
    """
    lines = _group_lines([w for w in words if w["x0"] >= MIN_VALUE_X], 6)

    return [
        line for line in lines
        if any(w["text"].lower().startswith(("odd", "even")) for w in line)
    ]


def _table_rows(table_words, values, labels, anchors, columns, header_words,
                semester_headings, document, programme) -> list[str]:
    """
    Build the output lines for one table.
    """
    band_text = " ".join(w["text"] for w in header_words)

    # Each header word names only the column it is nearest to
    centers = [(start + end) / 2 for start, end in columns]
    words_for_column = {i: [] for i in range(len(columns))}
    for word in sorted(header_words, key=lambda w: (w["top"], w["x0"])):
        nearest = min(range(len(columns)), key=lambda i: abs(centers[i] - _center(word)))
        start, end = columns[nearest]
        if start - COLUMN_WINDOW <= _center(word) <= end + COLUMN_WINDOW:
            words_for_column[nearest].append(word["text"])

    column_info = []
    for index, (start, end) in enumerate(columns):
        header_text = " ".join(words_for_column[index])
        center = (start + end) / 2
        semester = _semester_for(center, semester_headings)
        column_info.append({
            "range": (start - 15, end + 15),
            "name": _column_name(header_text, band_text),
            "semester": semester,
        })

    def nearest_anchor(word):
        return min(range(len(anchors)), key=lambda i: abs(anchors[i] - word["top"]))

    row_values = {i: [] for i in range(len(anchors))}
    row_labels = {i: [] for i in range(len(anchors))}

    for value in values:
        row_values[nearest_anchor(value)].append(value)

    for label in labels:
        row_labels[nearest_anchor(label)].append(label)

    # Cell values of every kept row: (label, [cell per column])
    table = []

    for i in range(len(anchors)):
        cells = row_values[i]

        # Plain integers only count if the row also has a real amount
        if not any(v["real"] for v in cells):
            continue

        label = " ".join(
            " ".join(w["text"] for w in line)
            for line in _group_lines(row_labels[i])
        ).strip()

        if not label:
            continue

        table.append((label, [
            next((v["amount"] for v in cells
                  if column["range"][0] <= v["x0"] <= column["range"][1]), "-")
            for column in column_info
        ]))

    # Drop stray columns that are empty in every row of this table
    used = [any(row[1][c] != "-" for row in table) for c in range(len(column_info))]

    lines_out = []

    for label, row_cells in table:
        by_semester = {}
        for column, cell, keep in zip(column_info, row_cells, used):
            if not keep:
                continue
            by_semester.setdefault(column["semester"], []).append(
                f"{column['name']}: {cell}"
            )

        for semester, parts in by_semester.items():
            if all(p.endswith(": -") for p in parts):
                continue
            fields = [document, programme, semester, label] + parts
            lines_out.append(" | ".join(f for f in fields if f))

    return lines_out


def extract_table_rows(pdf_path: str, page_index: int, file_name: str) -> list[str]:
    """
    Rebuild the fee-table rows of one page as self-contained text lines.
    """
    with pdfplumber.open(pdf_path) as pdf:
        words = pdf.pages[page_index].extract_words(x_tolerance=2)

    document = readable_title(file_name)
    titles = _find_titles(words)
    starts = _table_starts(words)

    # Lines of section headings (A. ..., (Common for all students), S. No. ...)
    section_words = set()
    for line in _group_lines([w for w in words if w["x0"] < MIN_VALUE_X]):
        if SECTION_LINE.match(" ".join(w["text"] for w in line)):
            section_words.update(id(w) for w in line)

    lines_out = []

    for t, start_line in enumerate(starts):
        top = start_line[0]["top"] - 2
        bottom = starts[t + 1][0]["top"] - 2 if t + 1 < len(starts) else 10_000
        table_words = [w for w in words if top <= w["top"] < bottom]

        # Values: amounts right of the serial-number column
        values = []
        for word in table_words:
            amount = _clean_amount(word["text"]) if word["x0"] >= MIN_VALUE_X else None
            if amount is None:
                continue
            before = [w for w in _same_line(table_words, word["top"])
                      if 0 <= word["x0"] - w["x1"] < 30 and "$" in w["text"]]
            values.append({
                **word,
                "amount": f"US $ {amount}" if before else amount,
                # A real amount has decimals or a currency; plain integers
                # may be header digits ("1 Lac to 5 Lac")
                "real": "." in word["text"] or bool(before),
            })

        real_values = [v for v in values if v["real"]]
        if not real_values:
            continue

        first_value_y = min(v["top"] for v in real_values)
        # Rows end just below the last real value (numbered notes follow)
        last_value_y = max(v["top"] for v in real_values) + BELOW_LAST_ROW_Y
        table_words = [w for w in table_words if w["top"] <= last_value_y]
        columns = _cluster_columns([v["x0"] for v in values if v["top"] >= first_value_y - 3])
        first_column_x = columns[0][0]

        header_words = [w for w in table_words if w["top"] < first_value_y - 3
                        and w["x0"] >= first_column_x - COLUMN_WINDOW]
        values = [v for v in values if v["top"] >= first_value_y - 3]

        # Row anchors: serial numbers and "Total" labels
        anchor_ys = sorted(
            w["top"] for w in table_words
            if w["top"] >= first_value_y - 12 and (
                (w["x0"] < MAX_SERIAL_X and SERIAL_PATTERN.match(w["text"]))
                or w["text"].lower() in ("total", "grant")
            )
        )

        # Value rows without a serial (e.g. two tuition lines under one
        # serial number) become rows of their own: a value row that is far
        # from its nearest anchor while that anchor has a closer value row
        value_ys = [line[0]["top"] for line in _group_lines([v for v in values if v["real"]], 3)]
        closest_row = {}
        for y in value_ys:
            if anchor_ys:
                anchor = min(anchor_ys, key=lambda a: abs(a - y))
                if anchor not in closest_row or abs(y - anchor) < abs(closest_row[anchor] - anchor):
                    closest_row[anchor] = y
        for y in value_ys:
            if not anchor_ys:
                anchor_ys.append(y)
                continue
            anchor = min(anchor_ys, key=lambda a: abs(a - y))
            if abs(y - anchor) > OWN_ROW_Y and closest_row.get(anchor) != y:
                anchor_ys.append(y)

        anchors = []
        for y in sorted(anchor_ys):
            if not anchors or y - anchors[-1] >= ANCHOR_MERGE_Y:
                anchors.append(y)
        if not anchors:
            continue

        serial_ids = {id(w) for w in table_words
                      if w["x0"] < MAX_SERIAL_X and SERIAL_PATTERN.match(w["text"])}

        # Label area: left of the first value column, from the first row to
        # just below the last row (the "Note:" text after a table is skipped)
        label_area = [
            w for w in table_words
            if first_value_y - 12 <= w["top"] <= max(anchors[-1], last_value_y)
            and w["x1"] < first_column_x - 2
            and _clean_amount(w["text"]) is None
            and id(w) not in serial_ids
        ]

        # Section headings (A. ..., (Common for all students), S. No.) are not row labels
        section_ids = set()
        for line in _group_lines(label_area, 3):
            if SECTION_LINE.match(" ".join(w["text"] for w in line)):
                section_ids.update(id(w) for w in line)

        labels = [w for w in label_area
                  if id(w) not in section_ids and id(w) not in section_words]

        above = [title for title in titles if title[0] < start_line[0]["top"]]
        programme = (above[-1] if above else (titles[0] if titles else (0, "")))[1]

        lines_out += _table_rows(
            table_words, values, labels, anchors, columns, header_words,
            _semester_headings(start_line), document, programme,
        )

    return lines_out


def build_table_row_documents(pdf_path: str, documents: list[Document]) -> list[Document]:
    """
    One Document per table row, with the metadata of the page it came from
    (file/page/year/category/page_title) plus chunk_type="table_row".

    Args:
        pdf_path: PDF file
        documents: The loaded (and metadata-enriched) pages of that PDF
    """
    file_name = os.path.basename(pdf_path)
    row_documents = []

    for page in documents:
        page_index = page.metadata.get("page", 0)

        for line in extract_table_rows(pdf_path, page_index, file_name):
            metadata = dict(page.metadata)
            metadata["chunk_type"] = "table_row"
            row_documents.append(Document(page_content=line, metadata=metadata))

    return row_documents


def main():
    """
    Print sample table rows so the column mapping can be checked by eye:
        python -m rag.table_rows [--samples 10] [--data-dir data/Raw/public]
    """
    from config.config import TABLE_ROW_FILES

    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument("--samples", type=int, default=10)
    parser.add_argument("--data-dir", default="data/Raw/public")
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")

    for file_name in TABLE_ROW_FILES:
        pdf_path = os.path.join(args.data_dir, file_name)

        with pdfplumber.open(pdf_path) as pdf:
            page_count = len(pdf.pages)

        rows = [
            (page + 1, line)
            for page in range(page_count)
            for line in extract_table_rows(pdf_path, page, file_name)
        ]

        # Tuition rows first (most important to check), then a spread of others
        tuition = [r for r in rows if "tuition" in r[1].lower()]
        others = [r for r in rows if r not in tuition]
        step = max(1, len(others) // max(1, args.samples - min(len(tuition), args.samples // 2)))
        samples = (tuition[: args.samples // 2] + others[::step])[: args.samples]

        print(f"\n##### {file_name}: {len(rows)} rows from {page_count} pages")
        for page, line in samples:
            print(f"  p{page:<2} {line}")


if __name__ == "__main__":
    main()
