# chile-detenidos

This repository contains detention statistics from multiple XLSB files. The new
`interactive_map.py` script provides an example Streamlit application that
visualizes the data on an interactive map of Chile. The application lets you
filter by nationality and select the aggregation level (Región, Prefectura or
Comuna).

## Usage

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Place GeoJSON shape files for Chile inside `data/shapes/` with filenames
   `regiones.geojson`, `prefecturas.geojson` and `comunas.geojson`.
3. Run the Streamlit app:
   ```bash
   streamlit run interactive_map.py
   ```

The map will display a heatmap of detentions based on the selected filters and
show counts when hovering over regions.
