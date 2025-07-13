from __future__ import annotations

import zipfile
from pathlib import Path
import pandas as pd
import urllib.request

DATA_DIR = Path("data/extranjeros")
YEARS = list(range(2018, 2024))
BASE_URL = (
    "https://serviciomigraciones.cl/wp-content/uploads/estudios/Estimaciones/"
    "Estimacion-extranjeros-{year}.zip"
)


def download_and_extract(year: int) -> Path:
    """Download and extract the ZIP for a given year. Returns extraction path."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = DATA_DIR / f"Estimacion-extranjeros-{year}.zip"
    if not zip_path.exists():
        url = BASE_URL.format(year=year)
        print(f"Downloading {url}...")
        urllib.request.urlretrieve(url, zip_path)
    extract_dir = DATA_DIR / str(year)
    if not extract_dir.exists():
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(extract_dir)
    return extract_dir


def find_comuna_data(path: Path) -> pd.DataFrame | None:
    """Search for a file containing comuna-level totals inside a directory."""
    for p in path.rglob('*'):
        if p.suffix.lower() in {'.xlsx', '.xls', '.csv'}:
            try:
                if p.suffix.lower() == '.csv':
                    df = pd.read_csv(p)
                else:
                    df = pd.read_excel(p)
            except Exception:
                continue
            cols = [c.lower() for c in df.columns]
            has_comuna = any('comuna' in c for c in cols)
            has_total = (
                any('total' in c and 'extranj' in c for c in cols)
                or any('poblacion' in c and 'extranj' in c for c in cols)
            )
            if has_comuna and has_total:
                rename = {}
                for c in df.columns:
                    lc = c.lower()
                    if 'comuna' in lc:
                        rename[c] = 'comuna'
                    elif 'total' in lc and 'extranj' in lc or (
                        'poblacion' in lc and 'extranj' in lc
                    ):
                        rename[c] = 'total_foreign'
                df = df.rename(columns=rename)
                df = df[['comuna', 'total_foreign']].dropna()
                return df
    return None


def build_dataset() -> pd.DataFrame:
    frames = []
    for year in YEARS:
        dir_path = DATA_DIR / str(year)
        if not dir_path.exists():
            dir_path = download_and_extract(year)
        df = find_comuna_data(dir_path)
        if df is None:
            print(f"No comuna data found for {year}")
            continue
        df['year'] = year
        frames.append(df)
    if not frames:
        raise RuntimeError("No data found in any year directories")
    result = pd.concat(frames, ignore_index=True)
    return result


if __name__ == "__main__":
    df = build_dataset()
    df.to_csv('census_pop_foreign.csv', index=False)
    print("Wrote census_pop_foreign.csv")
