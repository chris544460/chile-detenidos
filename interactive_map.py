import pandas as pd
import geopandas as gpd
import plotly.express as px
import streamlit as st
from pathlib import Path
import json
import re

FILE_DIR = Path(__file__).resolve().parent / "data"
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

def plot_map(level: str, agg: pd.DataFrame, measure: str):
    geojson_path = GEOJSON_PATHS[level]
    if not geojson_path.exists():
        st.error(f"GeoJSON not found: {geojson_path}")
        return
    # Load geojson manually to avoid fiona.path error
    gj = json.loads(Path(geojson_path).read_text())
    # Map GADM NAME fields to our level names
    name_map = {'Región': 'NAME_1', 'Prefectura': 'NAME_2', 'Comuna': 'NAME_3'}
    gadm_name_field = name_map[level]
    # Sanitize geojson feature names for consistent matching
    for feat in gj['features']:
        feat['properties'][gadm_name_field] = (
            feat['properties'][gadm_name_field]
              .upper()
              .replace(' ', '')
        )
    shapes = gpd.GeoDataFrame.from_features(gj["features"])
    shapes.crs = "EPSG:4326"
    # Rename & normalize to match agg
    shapes = shapes.rename(columns={gadm_name_field: level})
    shapes[level] = shapes[level].str.upper().str.replace(r'\s+', '', regex=True)
    st.write("Sanitized shapes:", shapes[[level]].head())
    merged = shapes.merge(agg, left_on=level, right_on=level, how='left').fillna({'Total': 0})
    st.write("Merged sample:", merged[[level, 'Total']].head())
    color = 'Total' if measure == 'Detenciones' else 'DPI'
    fig = px.choropleth_mapbox(
        merged,
        geojson=gj,
        locations=level,
        featureidkey=f"properties.{gadm_name_field}",
        color=color,
        hover_name=level,
        center={'lat': -35.7, 'lon': -71},
        mapbox_style='carto-positron',
        zoom=3.5,
        opacity=0.6,
        color_continuous_scale='Blues',
        labels={color: measure}
    )
    st.plotly_chart(fig, use_container_width=True)

def main():
    st.title("Detenciones en Chile")
    df = load_all_data()

    nationality = st.selectbox('Nacionalidad', sorted(df['Nacionalidad'].dropna().unique()))
    level = st.selectbox('Nivel', ['Región', 'Prefectura', 'Comuna'])
    measure = st.selectbox('Medida', ['Detenciones', 'DPI'])

    filtered = filter_detentions(df, nationality)
    agg = aggregate_detentions(filtered, level)
    st.write("Aggregate data sample:", agg.head())

    # Normalize region names to match GeoJSON
    if level == 'Región':
        agg['Región'] = (
            agg['Región']
              .str.replace('REGIÓN DE ', '', case=False)
              .str.upper()
              .str.replace(r'\s+', '', regex=True)
        )
        st.write("Normalized agg:", agg.head())

    if measure == 'DPI':
        total = agg['Total'].sum()
        # share per region
        agg['DPI'] = agg['Total'] / total
        # uniform share
        uniform_share = 1 / len(agg)
        agg['DPI'] = agg['DPI'] / uniform_share
        st.write("Computed DPI:", agg.head())

    plot_map(level, agg, measure)

if __name__ == '__main__':
    main()
