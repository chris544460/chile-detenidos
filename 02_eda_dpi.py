# 02_eda_dpi.py

import pandas as pd
import geopandas as gpd
import plotly.express as px

# 1. Load your cleaned detentions + pop data
det = pd.read_csv("detentions_2021_25.csv")
pop = pd.read_csv("census_pop.csv")  
# census_pop.csv must have: year, comuna, nat, pop

# 2. Filter to Venezuelans only (for your raw DPI map)
det_ven = det[det["nat"] == "VENEZOLANA"].copy()
pop_ven = pop[pop["nat"] == "VENEZOLANA"].copy()

# 3. Compute per-year totals (for normalization)
total_det_per_year = det_ven.groupby("year")["n_det"].sum().rename("total_det")
total_pop_per_year = pop_ven.groupby("year")["pop"].sum().rename("total_pop")

# 4. Merge totals back into the commune-level data
det_ven = det_ven.merge(total_det_per_year, on="year")
pop_ven = pop_ven.merge(total_pop_per_year, on="year")

# 5. Compute DPIᶜ,ʸ = (det_ct / total_det_y) ÷ (pop_ct / total_pop_y)
#    i.e. share of detentions ÷ share of population
df = (
    det_ven
    .groupby(["comuna", "year"])["n_det"]
    .sum()
    .rename("det_ct")
    .reset_index()
    .merge(pop_ven.groupby(["comuna","year"])["pop"].sum().rename("pop_ct").reset_index(),
           on=["comuna","year"])
    .merge(total_det_per_year.reset_index(), on="year")
    .merge(total_pop_per_year.reset_index(), on="year")
)
df["dpi"] = (df["det_ct"] / df["total_det"]) / (df["pop_ct"] / df["total_pop"])

# 6. Average DPI across years 2021–25
avg_dpi = (
    df.groupby("comuna")["dpi"]
      .mean()
      .rename("dpi_avg")
      .reset_index()
)

# 7. Save top-10 highest-DPI comunas
top10 = avg_dpi.sort_values("dpi_avg", ascending=False).head(10)
top10.to_csv("dpi_summary.csv", index=False)
print("Top 10 high-DPI comunas:\n", top10)

# 8. Plot choropleth map of avg DPI
#    — load your GeoJSON (must match 'comuna' field)
shp = gpd.read_file("data/shapes/comunas.geojson")
shp["comuna_norm"] = shp["properties.COMUNA"].str.upper().str.replace(r"\s+","")
avg_dpi["comuna_norm"] = avg_dpi["comuna"].str.upper().str.replace(r"\s+","")

merged = shp.merge(avg_dpi, on="comuna_norm")

fig = px.choropleth_mapbox(
    merged,
    geojson=merged.geometry.__geo_interface__,
    locations=merged.index,
    color="dpi_avg",
    mapbox_style="carto-positron",
    center={"lat": -35.7, "lon": -71},
    zoom=4,
    opacity=0.6,
    labels={"dpi_avg":"Avg DPI"}
)
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
fig.write_image("maps/fig1_raw_dpi_map.png", scale=2)
print("Saved choropleth to fig1_raw_dpi_map.png")
