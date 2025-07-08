from pathlib import Path
import pandas as pd


# Map lower‑case column names to canonical ones. This helps when some files have
# slightly different capitalisation or spacing.
COL_MAP = {
    "a\xc3\xb1o": "year",  # handles 'A\u00f1o'
    "ano": "year",  # sometimes the accent is lost
    "comuna": "comuna",
    "nacionalidad": "nat",
    "delitos o faltas": "offense",
    "total": "n_det",
}


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename dataframe columns using COL_MAP, ignoring case and spaces."""
    rename = {}
    for col in df.columns:
        key = col.strip().lower()
        if key in COL_MAP:
            rename[col] = COL_MAP[key]
    return df.rename(columns=rename)


def load_and_clean():
    """Load detention data from XLSB files and save a cleaned CSV."""
    xlsb_paths = list(Path("data").glob("20*.xlsb"))
    frames = []

    for p in xlsb_paths:
        year = int(p.name[:4])
        df = pd.read_excel(p, sheet_name=0, engine="pyxlsb", header=6)
        df = standardize_columns(df)
        df["year"] = year
        frames.append(df[["year", "comuna", "offense", "nat", "n_det"]])

    det = pd.concat(frames, ignore_index=True)

    det.to_csv("detentions_2021_25.csv", index=False)


if __name__ == "__main__":
    load_and_clean()
