from __future__ import annotations

from pathlib import Path
import pandas as pd
import unicodedata

DATA_DIR = Path("data/extranjeros")


def unaccent(text: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFKD", str(text)) if not unicodedata.combining(ch))


def normalize_cols(df: pd.DataFrame) -> pd.DataFrame:
    rename = {c: unaccent(c).strip().lower() for c in df.columns}
    return df.rename(columns=rename)


def parse_sheet(df: pd.DataFrame, year: int) -> pd.DataFrame | None:
    df = normalize_cols(df)
    if "comuna" not in df.columns:
        return None

    # wide format: columns for different nationalities
    nat_cols: list[str] = []
    total_col: str | None = None
    for col in df.columns:
        if "venezuela" in col:
            nat_cols.append(col)
        if "chile" in col or "chilena" in col:
            nat_cols.append(col)
        if "total" in col and total_col is None:
            total_col = col

    if nat_cols:
        out_rows = []
        for nat_col in nat_cols:
            nat = "VENEZOLANA" if "venezuela" in nat_col else "CHILENA"
            subset = df[["comuna", nat_col]].copy()
            subset = subset.rename(columns={nat_col: "pop"})
            subset["nat"] = nat
            subset["year"] = year
            out_rows.append(subset)
        if total_col is not None:
            total = df[["comuna", total_col]].copy()
            total = total.rename(columns={total_col: "pop"})
            total["nat"] = "TOTAL"
            total["year"] = year
            out_rows.append(total)
        return pd.concat(out_rows, ignore_index=True)

    # long format with 'nacionalidad' column
    nat_field = None
    value_field = None
    for col in df.columns:
        if "nacionalidad" in col or "pais" in col:
            nat_field = col
        if "total" in col or "pobl" in col:
            value_field = col
    if nat_field and value_field:
        df = df[["comuna", nat_field, value_field]].rename(columns={nat_field: "nat", value_field: "pop"})
        df["nat"] = df["nat"].apply(lambda x: unaccent(str(x)).strip().upper())
        df["year"] = year
        return df
    return None


def parse_excel(path: Path, year: int) -> list[pd.DataFrame]:
    xl = pd.ExcelFile(path)
    frames = []
    for sheet in xl.sheet_names:
        try:
            df = xl.parse(sheet)
        except Exception:
            continue
        parsed = parse_sheet(df, year)
        if parsed is not None:
            frames.append(parsed)
    return frames


def build_dataset() -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for year_dir in sorted(DATA_DIR.iterdir()):
        if not year_dir.is_dir():
            continue
        try:
            year = int(year_dir.name)
        except ValueError:
            continue
        for xls in year_dir.rglob("*.xlsx"):
            frames.extend(parse_excel(xls, year))
    if not frames:
        raise RuntimeError("No sheets parsed")
    df = pd.concat(frames, ignore_index=True)
    df = df.dropna(subset=["comuna", "nat", "pop"])
    return df


def main():
    df = build_dataset()
    df.to_csv("census_pop.csv", index=False)


if __name__ == "__main__":
    main()
