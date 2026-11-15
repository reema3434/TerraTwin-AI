# TerraTwin AI

Student prototype for the NASA International Space Apps Challenge 2026, Al Khobar, Saudi Arabia. This independent project is not an official NASA product or a NASA-endorsed operational system.

TerraTwin AI compares Saudi Arabian terrain with selected lunar and Martian regions, then presents a Mission Test Lab assessment of relative terrain difficulty.

## Features

- Streamlit dashboard with mission configuration and terrain comparison.
- Two Earth candidates: **AlUla** and **Harrat Khaybar**.
- Planetary references: **Connecting Ridge** (Moon) and **Athabasca Valles** (Mars).
- Three comparison modes: Mobility, Navigation, and Robotic Operations; the engine also supports custom feature subsets.
- Optional AI interpretation of natural-language requests and explanations grounded in computed results.
- Mission Test Lab displaying precomputed Low, Medium, and High difficulty percentages.

## Run locally

Use Python 3.10 or newer. Open a terminal in the repository folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

On Windows, replace the activation command with `.venv\Scripts\activate`.

Optional, before launching the app:

```bash
export GROQ_API_KEY="your-own-key"
```

Never commit a real API key. Without a key, numerical comparison and deterministic explanations remain available. Natural-language mission classification falls back to Mobility and the selected fallback body; it does not interpret the query offline. For other modes without an API key, use the explicit mission controls.

The current code requests `openai/gpt-oss-120b` for mission classification and `llama-3.3-70b-versatile` for explanations through Groq. API access and model availability depend on the provider. Failed requests use the code's fallback behavior.

## Similarity method

The five available features are mean slope (`slope_deg`), roughness (`roughness_m`), local relief (`local_relief_m`), slope variability (`slope_std_deg`), and flat fraction (`flat_fraction`).

| Condition | Features |
| --- | --- |
| Mobility | slope, roughness, local relief, slope variability |
| Navigation | roughness, local relief, slope variability |
| Robotic Operations | slope, roughness, flat fraction |

For each selected feature, the engine calculates:

```text
normalized_difference = abs(earth_value - target_value) / (maximum - minimum)
similarity_percent = 100 * (1 - mean(normalized_differences))
```

The minimum and maximum come from **all rows in the supplied CSV**, including Earth, Moon, and Mars. Selected features receive equal weights. A constant feature receives zero normalized difference. Adding or changing dataset rows can change scores, even when the selected pair is unchanged. These are dataset-relative resemblance scores, not probabilities of success.

### Reproduced results from the included dataset

| Target | Condition | Best Earth match | Similarity |
| --- | --- | --- | ---: |
| Moon / Connecting Ridge | Mobility | AlUla | 51.28% |
| Moon / Connecting Ridge | Navigation | AlUla | 46.51% |
| Moon / Connecting Ridge | Robotic Operations | AlUla | 81.39% |
| Mars / Athabasca Valles | Mobility | Harrat Khaybar | 86.35% |
| Mars / Athabasca Valles | Navigation | Harrat Khaybar | 82.85% |
| Mars / Athabasca Valles | Robotic Operations | Harrat Khaybar | 67.35% |

Example Python usage (from the repository folder):

```python
from main import compare

result = compare(
    target_body="Moon",
    target_region="Connecting_Ridge",
    condition="mobility",
)
print(result["best_match"])
```

## Mission Test Lab

The dashboard presents region-level percentages precomputed by the team using a hybrid slope/roughness classification:

- **Low:** slope < 10 degrees AND roughness < 31.28 m.
- **High:** slope >= 15 degrees OR roughness >= 68.30 m.
- **Medium:** remaining valid cells.

The team describes 31.28 m and 68.30 m as roughness P65 and P90, with approximately 16 x 16 km study areas processed at 75 m resolution. These values and difficulty percentages are embedded in `mission_lab_adapter.py`; this package does not recompute raster classification. Original DEMs, GIS extraction projects, and difficulty GeoTIFFs are not included. Raster paths in the adapter are references, not bundled files; the current lab view displays aggregate metrics and a table. Slope-threshold literature and exact source-product identifiers are not supplied in this package and should be added by the team for full reproducibility.

## Verification

The six target/mission combinations were reproduced with the included feature table. Python source files passed syntax checks, and all six dashboard pages executed without application exceptions in Streamlit AppTest without an API key. Live API responses and external map/logo loading were not verified. Plotly is constrained to version 5.x because this dashboard uses its legacy `scatter_mapbox` interface.

## Files

```text
app.py                       Streamlit dashboard
main.py                      Deterministic similarity engine
mission_classifier.py        Optional AI mission classification
similarity_adapter.py        Mission/engine interface
results_explainer.py         Metric-based and optional AI explanations
mission_lab_adapter.py       Precomputed difficulty statistics and explanations
integration_pipeline.py      Integrated analysis workflow
terrain_data.csv             Four-region feature table used by the engine
data/terrain_candidates.csv  Reference table for the dashboard
data/saudi_sites.csv          Earth site coordinates for visualization
requirements.txt             Runtime dependencies
```

## Data and resource credits

Source families below follow the team's supplied project documentation. The bundled files contain derived feature values, not the original elevation products. These links identify the missions/archives; they do not identify the exact tiles used.

- Earth: [Shuttle Radar Topography Mission (SRTM)](https://science.nasa.gov/mission/srtm/).
- Moon: [NASA LRO Lunar Orbiter Laser Altimeter (LOLA), PDS archive](https://pds-geosciences.wustl.edu/missions/lro/lola.htm).
- Mars: [ESA Mars Express HRSC, PDS archive information](https://pds-geosciences.wustl.edu/missions/mars_express/hrsc.htm). HRSC is an ESA mission instrument; NASA archive hosting does not change its mission attribution.
- [QGIS](https://qgis.org/), [Python](https://www.python.org/), [Pandas](https://pandas.pydata.org/), [NumPy](https://numpy.org/), [Streamlit](https://streamlit.io/), [Plotly](https://plotly.com/python/), [Pydeck](https://deckgl.readthedocs.io/).
- [Groq](https://groq.com/) and [ChatGPT](https://chatgpt.com/) for AI assistance.
- The supplied dashboard references an external [Space Apps logo image](https://upload.wikimedia.org/wikipedia/commons/2/27/NASA_Space_Apps_Default_Logo_2-Color_Black.svg). Availability and permitted usage are governed by the source and applicable branding rules; inclusion does not imply NASA endorsement.

## AI assistance disclosure

ChatGPT assisted with code development, debugging, and project documentation. Groq-hosted language models support natural-language mission interpretation and explanations of computed results. Similarity scores are calculated by a deterministic algorithm, not generated by a language model. Mission Test Lab presents precomputed terrain classifications. Elevation source datasets are attributed to their providers and are not presented as AI-generated. The team remains responsible for reviewing the submitted work and disclosing any additional AI-generated assets.

## Limitations

This prototype compares only two Earth candidates. Terrain resemblance and terrain difficulty are distinct metrics. Neither predicts actual rover safety or physical performance. Gravity, radiation, temperature, soil mechanics, wheel design, and other operational conditions are outside the model. Resampling to a common grid does not create equal native detail or accuracy. Equal weights and classification thresholds require further validation; field measurements and expert review are needed before operational use.

No redistribution license for the team's source code has been added; public visibility alone does not grant an open-source license. Third-party resources retain their respective terms.
