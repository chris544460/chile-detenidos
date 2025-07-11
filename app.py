from pathlib import Path
import pandas as pd
import unicodedata

# Define expected raw header layout (must match exactly)
EXPECTED_COLS = [
    '', 'Detenido', 'Región', 'Provincia', 'Comuna', 'Zonas',
    'Prefectura', 'Destacamentos', 'Año', 'Mes', 'Nacionalidad',
    'Delitos o faltas', 'Total'
]

# Map un-accented, lower-case column keys to canonical names
COL_MAP = {
    "detenido":        "detained",
    "región":          "region",
    "region":          "region",
    "provincia":       "province",
    "comuna":          "comuna",
    "zonas":           "zones",
    "prefectura":      "prefecture",
    "destacamentos":   "detachment",
    "año":             "year",
    "ano":             "year",
    "mes":             "month",
    "nacionalidad":    "nat",
    "delitos o faltas":"offense",
    "total":           "n_det",
}

# Mapping of Spanish month names to numeric values
MONTH_MAP = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12
}


def unaccent(s: str) -> str:
    """Strip accents from a string, e.g. 'Año' → 'Ano'."""
    return ''.join(
        ch for ch in unicodedata.normalize('NFKD', s)
        if not unicodedata.combining(ch)
    )


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rename DataFrame columns by matching un-accented, lower-case keys against COL_MAP.
    """
    rename = {}
    for col in df.columns:
        key = unaccent(col).strip().lower()
        if key in COL_MAP:
            rename[col] = COL_MAP[key]
    return df.rename(columns=rename)


def convert_month(series: pd.Series) -> pd.Series:
    """
    Convert Spanish month names in a Series to numeric month (1-12). Handles case-insensitive and unaccented values.
    """
    def to_num(val):
        if pd.isna(val):
            return pd.NA
        key = unaccent(str(val)).strip().lower()
        return MONTH_MAP.get(key, pd.NA)
    return series.map(to_num).astype('Int64')


def load_and_clean():
    """Load all XLSB files, enforce headers, clean and export CSV with full context."""
    xlsb_paths = sorted(Path("data").glob("20*.xlsb"))
    frames = []

    for p in xlsb_paths:
        year_file = int(p.stem[:4])

        # 1) Read and drop fully empty rows
        df = pd.read_excel(p, sheet_name=0, engine="pyxlsb", header=6)
        df = df.dropna(how="all").reset_index(drop=True)

        # 2) Enforce raw header layout
        if len(df.columns) == len(EXPECTED_COLS):
            df.columns = EXPECTED_COLS
        else:
            raise ValueError(
                f"Unexpected columns in {p.name}: expected {len(EXPECTED_COLS)}, got {len(df.columns)}"
            )

        # 3) Standardize to canonical names
        df = standardize_columns(df)

        # 4) Filter by in-file year if present
        if 'year' in df.columns:
            df['year'] = pd.to_numeric(df['year'], errors='coerce')
            df = df[df['year'] == year_file]

        # 5) Convert month names to numeric
        df['month'] = convert_month(df.get('month'))

        # 6) Numeric conversion for detention counts
        df['n_det'] = pd.to_numeric(df['n_det'], errors='coerce').fillna(0).astype(int)

        # 7) Overwrite/set year from filename
        df['year'] = year_file

        # 8) Keep all relevant columns
        cols = [
            'year', 'detained', 'region', 'province', 'comuna',
            'zones', 'prefecture', 'detachment', 'month',
            'nat', 'offense', 'n_det'
        ]
        frames.append(df[cols])

    # 9) Concatenate and save full dataset
    det = pd.concat(frames, ignore_index=True)
    det.to_csv("detentions_2021_25.csv", index=False)


if __name__ == "__main__":
    load_and_clean()
