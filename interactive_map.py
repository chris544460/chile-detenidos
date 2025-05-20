import pandas as pd
import geopandas as gpd
import plotly.express as px
import streamlit as st
from pathlib import Path

FILE_DIR = Path("./data")
FILE_PATHS = {
    2021: FILE_DIR / '2021 Detenidos_Nacional.xlsb',
    2022: FILE_DIR / '2022 Detenidos_Nacional.xlsb',
    2023: FILE_DIR / '2023 Detenidos_Nacional.xlsb',
    2024: FILE_DIR / '2024 Detenidos_Nacional.xlsb',
    2025: FILE_DIR / '2025 Detenidos_Nacional.xlsb'
}

SHAPE_DIR = FILE_DIR / "shapes"
GEOJSON_PATHS = {
    'Región': SHAPE_DIR / 'regiones.geojson',
    'Prefectura': SHAPE_DIR / 'prefecturas.geojson',
    'Comuna': SHAPE_DIR / 'comunas.geojson'
}

COLUMNS = [
    '', 'Detenido', 'Región', 'Provincia', 'Comuna', 'Zonas', 'Prefectura',
    'Destacamentos', 'Año', 'Mes', 'Nacionalidad', 'Delitos o faltas', 'Total'
]

def load_yearly_data(year: int, path: Path) -> pd.DataFrame:
    """Load detention data for a given year"""
    xls = pd.ExcelFile(path, engine='pyxlsb')
    sheet = xls.sheet_names[0]
    df = pd.read_excel(path, sheet_name=sheet, engine='pyxlsb', header=6)
    df = df.dropna(how='all').reset_index(drop=True)
    df.columns = COLUMNS
    df['Año'] = pd.to_numeric(df['Año'], errors='coerce')
    df = df[df['Año'] == int(year)]
    df['Total'] = pd.to_numeric(df['Total'], errors='coerce').fillna(0).astype(int)
    return df

def load_all_data() -> pd.DataFrame:
    frames = []
    for year, path in FILE_PATHS.items():
        frames.append(load_yearly_data(year, path))
    return pd.concat(frames, ignore_index=True)

def filter_detentions(df: pd.DataFrame, nationality: str) -> pd.DataFrame:
    return df[df['Nacionalidad'].str.contains(nationality, case=False, na=False)]

def aggregate_detentions(df: pd.DataFrame, level: str) -> pd.DataFrame:
    return df.groupby(level)['Total'].sum().reset_index()

def plot_map(level: str, agg: pd.DataFrame):
    geojson_path = GEOJSON_PATHS[level]
    shapes = gpd.read_file(geojson_path)
    merged = shapes.merge(agg, on=level, how='left').fillna({'Total': 0})
    fig = px.choropleth_mapbox(
        merged,
        geojson=merged.geometry.__geo_interface__,
        locations=merged.index,
        color='Total',
        hover_name=level,
        center={'lat': -35.7, 'lon': -71},
        mapbox_style='carto-positron',
        zoom=3.5,
        opacity=0.6,
    )
    st.plotly_chart(fig, use_container_width=True)

def main():
    st.title("Detenciones en Chile")
    df = load_all_data()

    nationality = st.selectbox('Nacionalidad', sorted(df['Nacionalidad'].dropna().unique()))
    level = st.selectbox('Nivel', ['Región', 'Prefectura', 'Comuna'])

    filtered = filter_detentions(df, nationality)
    agg = aggregate_detentions(filtered, level)
    plot_map(level, agg)

if __name__ == '__main__':
    main()
