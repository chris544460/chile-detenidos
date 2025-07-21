import re
from pathlib import Path
import pandas as pd
import unicodedata
import logging

# Setup basic debug logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")

DATA_DIR = Path("data/extranjeros")

# Utility to strip accents
def unaccent(text: str) -> str:
    return "".join(
        ch
        for ch in unicodedata.normalize("NFKD", str(text))
        if not unicodedata.combining(ch)
    )

# Regex for sheet names (Comunas-País or Regiones-País)
SHEET_RE = re.compile(
    unaccent(r"^(comunas?[- ]pais|regiones?[- ]pais)$"),
    flags=re.IGNORECASE
)

# Parse a single sheet, with refined header detection

def parse_sheet(df: pd.DataFrame, year: int, source_file: str, sheet: str) -> pd.DataFrame | None:
    logging.debug(f"Parsing sheet '{sheet}' for year {year} in file {source_file}")

    # Detect header row: look for a cell exactly 'comuna(s)' or 'region(es)'
    header_idx = None
    for idx, row in df.iterrows():
        for cell in row:
            if isinstance(cell, str):
                norm = unaccent(cell).strip().lower()
                if norm in ("comuna", "comunas", "region", "regiones"):
                    header_idx = idx
                    break
        if header_idx is not None:
            break

    if header_idx is None:
        logging.debug("No header row with exact 'comuna(s)' or 'region(es)' found; skipping sheet.")
        return None

    logging.debug(f"Detected header row at index {header_idx}")

    # Rebuild DataFrame from header
    header = df.iloc[header_idx].tolist()
    data = df.iloc[header_idx + 1 :].reset_index(drop=True)
    data.columns = header

    # Normalize column names
    data = data.rename(columns={
        c: unaccent(str(c)).strip().lower() for c in data.columns
    })

    # Identify geography column
    if "comuna" in data.columns:
        geo = "comuna"
    elif "region" in data.columns:
        geo = "region"
    else:
        logging.debug("After reheader, no 'comuna' or 'region' column found; skipping.")
        return None

    logging.debug(f"Geography column identified: {geo}")

    # Wide-format detection: columns ending with ' <year>'
    year_str = str(year)
    wide_cols = [c for c in data.columns if c.endswith(f" {year_str}")]
    logging.debug(f"Wide-format columns: {wide_cols}")

    rows = []
    if wide_cols:
        total_cols = [c for c in wide_cols if c.lower().startswith("total ")]
        nat_cols = [c for c in wide_cols if c not in total_cols]

        logging.debug(f"Total columns: {total_cols}")
        logging.debug(f"Nationality columns: {nat_cols}")

        # Parse nationality
        for col in nat_cols:
            country = unaccent(col[: -(len(year_str) + 1)]).strip().upper()
            logging.debug(f"Parsing '{col}' as country '{country}'")
            sub = data[[geo, col]].copy().rename(columns={col: "pop"})
            sub["nat"] = country
            sub["year"] = year
            sub["source_file"] = source_file
            sub["sheet"] = sheet
            rows.append(sub)

        # Parse totals
        for col in total_cols:
            logging.debug(f"Parsing total column '{col}'")
            sub = data[[geo, col]].copy().rename(columns={col: "pop"})
            sub["nat"] = "TOTAL"
            sub["year"] = year
            sub["source_file"] = source_file
            sub["sheet"] = sheet
            rows.append(sub)

        result = pd.concat(rows, ignore_index=True)
        return result.rename(columns={geo: "comuna"})

    # Fallback: long format
    nat_field = next(
        (c for c in data.columns if "pais" in c or "nacionalidad" in c),
        None,
    )
    val_field = next(
        (c for c in data.columns if "total" in c or "pobl" in c),
        None,
    )
    logging.debug(f"Long-format fields detected - nat: {nat_field}, val: {val_field}")

    if nat_field and val_field:
        sub = data[[geo, nat_field, val_field]].rename(
            columns={nat_field: "nat", val_field: "pop"}
        )
        sub["nat"] = sub["nat"].apply(lambda x: unaccent(str(x)).strip().upper())
        sub["year"] = year
        sub["source_file"] = source_file
        sub["sheet"] = sheet
        logging.debug(f"Parsed long format with {len(sub)} rows")
        return sub.rename(columns={geo: "comuna"})

    logging.debug("Sheet format unrecognized; skipping.")
    return None

# Parse an Excel file

def parse_excel(path: Path, year: int) -> list[pd.DataFrame]:
    logging.debug(f"Loading Excel file: {path}")
    xl = pd.ExcelFile(path)
    frames = []

    for sheet in xl.sheet_names:
        if not SHEET_RE.match(unaccent(sheet)):
            continue
        try:
            df = xl.parse(sheet, header=None)
        except Exception as e:
            logging.error(f"Error parsing '{sheet}': {e}")
            continue

        parsed = parse_sheet(df, year, source_file=path.name, sheet=sheet)
        if parsed is not None:
            logging.debug(f"Sheet '{sheet}' yielded {len(parsed)} rows")
            frames.append(parsed)

    logging.debug(f"File '{path.name}' yielded {len(frames)} frames")
    return frames

# Build dataset across years

def build_dataset() -> pd.DataFrame:
    all_frames = []
    for year_dir in sorted(DATA_DIR.iterdir()):
        if not year_dir.is_dir():
            continue
        try:
            year = int(year_dir.name)
        except ValueError:
            continue
        logging.debug(f"Processing year: {year}")
        for xlsx in year_dir.rglob("*.xlsx"):
            all_frames.extend(parse_excel(xlsx, year))

    if not all_frames:
        logging.error("No sheets parsed for any year.")
        raise RuntimeError("No sheets parsed")

    df = pd.concat(all_frames, ignore_index=True)
    df = df.dropna(subset=["comuna", "nat", "pop"]).reset_index(drop=True)
    logging.debug(f"Final dataset rows: {len(df)}")
    return df

# Main function

def main():
    df = build_dataset()
    df.to_csv("census_pop_debug.csv", index=False)
    logging.info("Wrote census_pop_debug.csv")

if __name__ == "__main__":
    main()
