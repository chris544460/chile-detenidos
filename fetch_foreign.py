from pathlib import Path
import pandas as pd
import unicodedata
import requests
import zipfile

BASE_URL = (
    "https://serviciomigraciones.cl/wp-content/uploads/estudios/Estimaciones/"
    "Estimacion-extranjeros-{year}.zip"
)
DATA_DIR = Path("data/extranjeros")


def unaccent(text: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFKD", str(text)) if not unicodedata.combining(ch))


def download_year(year: int) -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = DATA_DIR / f"Estimacion-extranjeros-{year}.zip"
    if not zip_path.exists():
        url = BASE_URL.format(year=year)
        print(f"Downloading {url}")
        resp = requests.get(url, stream=True)
        resp.raise_for_status()
        with open(zip_path, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=8192):
                fh.write(chunk)
    return zip_path


def extract_zip(zip_path: Path, year: int) -> Path:
    out_dir = DATA_DIR / str(year)
    if not out_dir.exists():
        out_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(out_dir)
    return out_dir


def find_excel(dir_path: Path) -> Path:
    matches = []
    for ext in ("*.xlsx", "*.xls", "*.xlsb", "*.xlsm"):
        matches.extend(dir_path.rglob(ext))
    if matches:
        return matches[0]
    print(f"[DEBUG] No Excel found under {dir_path}. Contents:")
    for p in dir_path.rglob("*"):
        print("   ", p.relative_to(dir_path))
    raise FileNotFoundError(f"No Excel file found in {dir_path}")


def parse_foreign(file_path: Path, year: int) -> pd.DataFrame:
    df = pd.read_excel(file_path, header=0)
    # Standardize column names
    cols = {c: unaccent(c).strip().lower() for c in df.columns}
    df = df.rename(columns=cols)

    comuna_col = None
    total_col = None
    for c in df.columns:
        key = unaccent(str(c)).strip().lower()
        if comuna_col is None and "comuna" in key:
            comuna_col = c
        if total_col is None and "total" in key and ("extran" in key or "migr" in key or "foreign" in key):
            total_col = c
    if comuna_col is None or total_col is None:
        raise ValueError(f"Required columns not found in {file_path}")
    df = df[[comuna_col, total_col]]
    df.columns = ["comuna", "total_foreign"]
    df["year"] = year
    return df


def load_foreign_year(year: int) -> pd.DataFrame | None:
    """
    Download, extract and parse the foreign‑population spreadsheet for a single year.
    Returns a DataFrame on success, or None if the file is missing / unparsable.
    """
    try:
        zip_path = download_year(year)
        folder = extract_zip(zip_path, year)
        excel_path = find_excel(folder)  # folder already points to …/extranjeros/<year>
        return parse_foreign(excel_path, year)
    except FileNotFoundError as e:
        print(f"Warning: {e}. Skipping year {year}.")
        return None
    except Exception as e:
        print(f"Error processing year {year}: {e}. Skipping year {year}.")
        return None


def main():
    frames: list[pd.DataFrame] = []
    for year in range(2018, 2024):
        df_year = load_foreign_year(year)
        if df_year is not None:
            frames.append(df_year)
    if not frames:
        print("No data frames collected – nothing to write.")
        return
    df = pd.concat(frames, ignore_index=True)
    df.to_csv("census_pop_foreign.csv", index=False)


if __name__ == "__main__":
    main()
