# First land-cover map of Lagos, 2025

*Dry-season Landsat 8/9 composite (November 2024 – March 2025), classified with a Random Forest (300 trees) in Google Earth Engine using [`gee_wetland_change.js`](../gee_wetland_change.js). Training points were placed by hand on the 2025 imagery, checked against high-resolution Google satellite imagery. Recorded 25 November 2026.*

## Accuracy

Accuracy is measured on the 30 % of training points held back from the model (76 points in the final run).

| Measure | Value |
|---|---|
| Overall accuracy | **86.8 %** |
| Kappa | **0.83** |
| Training / test points | 191 / 76 (267 in total) |

| Class | Producer's accuracy | User's accuracy |
|---|---|---|
| Water | 100 % | 94 % |
| Wetland / mangrove | 70 % | 88 % |
| Other vegetation | 89 % | 89 % |
| Built-up | 89 % | 80 % |
| Bare sand / fill | 77 % | 77 % |

Confusion matrix (rows = reference, columns = map):

| | Water | Wetland | Vegetation | Built-up | Bare |
|---|---|---|---|---|---|
| **Water** | 17 | 0 | 0 | 0 | 0 |
| **Wetland** | 1 | 7 | 2 | 0 | 0 |
| **Vegetation** | 0 | 1 | 24 | 0 | 2 |
| **Built-up** | 0 | 0 | 0 | 8 | 1 |
| **Bare** | 0 | 0 | 1 | 2 | 10 |

## How the map was improved

The first classification reached 78 % overall accuracy but confused vegetation with bare ground: in the dry season, grass and harvested farmland dry out and look similar to bare sand. Three rounds of improvement followed.

| Run | Change | Overall accuracy | Kappa | Bare: user's accuracy | Bare area (km²) |
|---|---|---|---|---|---|
| 1 | 205 training points | 78.1 % | 0.72 | 55 % | 208 |
| 2 | More vegetation points, including dry grass and farmland | 80.8 % | 0.75 | 58 % | 556 |
| 3 | Added seasonal greenness (greenest NDVI of the year and its range) | 83.1 % | 0.78 | 58 % | 496 |
| 4 | Corrected the coastal strip: scrub and coconut behind the beach relabelled as vegetation | **86.8 %** | **0.83** | **77 %** | **310** |

## Mapped area (provisional)

| Class | Area (km²) |
|---|---|
| Other vegetation | 1,485 |
| Built-up | 935 |
| Water | 645 |
| Wetland / mangrove | 402 |
| Bare sand / fill | 310 |

These are raw pixel counts and should not yet be cited. The wetland area in particular changed between runs (from 840 to 402 km²) as training data were added, and the test sample contains only about ten points per class. Final areas will be reported with 95 % confidence intervals from an independent stratified random validation sample, following Olofsson et al. (2014).

## Notes

- The Lagos boundary used (FAO GAUL 2015) predates much of Eko Atlantic, so recently reclaimed land on the coast is outside the mapped area. A boundary that includes new coastal land is planned.
- Small gaps in the lagoon are pixels that were cloudy in every image of the season.

## Next steps

1. Independent accuracy assessment and area estimates with confidence intervals (stratified random sample).
2. Maps for 2013, 2000 and 1986 using the same method.
3. Change analysis: wetland converted to built-up land or sand fill.
