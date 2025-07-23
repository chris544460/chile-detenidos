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

### Foreign population dataset

To build `census_pop_foreign.csv` with estimated foreign population by comuna
and year (2018–2023), run:

```bash
python fetch_foreign.py
```

The script downloads the official spreadsheets from
`serviciomigraciones.cl`, unzips them into `data/extranjeros/` and compiles a
single CSV.


Discretionary Offenses
These are offenses where police officers have more flexibility in deciding whether or not to make a stop, issue a citation, or make an arrest. They tend to involve lesser violations or situations where there’s no immediate victim.

Examples:

Traffic violations (e.g., “driving without a license”)

Public order violations (e.g., "riña pública" or public brawls)

Health and safety infractions (e.g., “violation of sanitary regulations” like not wearing a mask in certain areas)

Why are they discretionary?
Police officers can choose whether to stop someone for minor traffic infractions or whether to enforce a health regulation (e.g., whether to fine someone for a small violation). There’s leeway in enforcement, meaning police can focus on certain populations (in this case, migrants) depending on their priorities, availability of resources, or even biases.

Serious Offenses
These are more severe crimes where police involvement is typically mandatory—there's less room for discretion. These crimes typically involve harm to others (e.g., theft, assault) and often require evidence of harm or victim complaint for enforcement.

Examples:

Violent crimes (e.g., “homicide”, “robbery with violence”)

Theft (e.g., “burglary”, “larceny”)

Sexual offenses (e.g., “sexual abuse”)

Why are they serious?
Serious offenses usually have set penalties and defined legal procedures (e.g., arrests for robbery, murder). Police don’t usually have much leeway in deciding whether to arrest—it's a legal necessity once the crime is reported or detected. The severity of the offense dictates a response that is usually automatic (no or limited discretion).

Why This Matters in Your Study
Discretionary offenses are where policing bias is more likely to be evident. These are areas where minor infractions—like driving without a license—can be disproportionately enforced on certain populations (in this case, Venezuelan migrants).

Serious offenses are less prone to biased policing, because officers usually don’t have much leeway in whether they make an arrest or not. If a person is involved in robbery or homicide, they’re going to be arrested, regardless of nationality.

Using This in Your Analysis
In your study, the goal is to distinguish between policing bias in minor infractions (where discretion plays a role) versus serious crimes where enforcement is more uniform and objective.

For example:

If you find that Venezuelans are detained more for "driving without a license" than Chileans (a discretionary offense), but not for crimes like robbery (a serious offense), this suggests over-policing or discriminatory enforcement, not that Venezuelans are inherently more criminal.