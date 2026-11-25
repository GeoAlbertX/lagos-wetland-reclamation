# Lost wetlands, land reclamation and flood storage in Lagos (1986–2050)

Atta Albert · Research in progress · Google Earth Engine, Landsat, Sentinel-2, Random Forest, Python

**Keywords:** land reclamation, wetland loss, mangroves, dredging, flood storage, land-use change, Random Forest, Google Earth Engine, Lagos Lagoon, urban flooding

**Status:** first 2025 land-cover map complete (86.8 % overall accuracy, kappa 0.83; see [results/2025_first_map.md](results/2025_first_map.md)). Maps for earlier years and the change analysis are under way.

---

## Why this study

Lagos has been filling its lagoon edges for decades. Mangroves, swamps and shallow lagoon water have been dredged over and built on, from small plots in Ikorodu and Lekki to Banana Island and Eko Atlantic. Flooding has worsened over the same period, and residents and the state government both blame reclamation. Yet nobody has measured how much flood storage the city has actually lost.

The [literature review](LITERATURE_REVIEW.md) found three problems with the existing evidence:

1. **The studies disagree.** One study found mangroves on the eastern lagoon fringe fell by 77 % between 1984 and 2006. Two statewide studies report wetland *gains* over similar periods, and several studies contain internal inconsistencies.
2. **Most are snapshots.** Published work compares two or three dates with different class definitions, and several studies report no accuracy assessment.
3. **The flood link is assumed, not measured.** No study converts lost wetland area into lost flood-storage volume, and the feedback loop in which flooding drives more land filling is known only from residents' accounts.

This study follows on from my [Lagos rainfall and flood-risk research](https://github.com/GeoAlbertX/climate-flood-research). Satellite measurements there showed that central Lagos was already built up by 2005, while built-up land in the Lekki–Ajah corridor rose from 16 % to 26 % and raised runoff there by about a third. Much of that edge growth is on wetland and lagoon fringe. This study maps where the growth went across Lagos, and what it removed.

## Research questions

| # | Question |
|---|---|
| RQ1 | How much wetland, mangrove and lagoon water was converted to built-up land or sand fill in Lagos between 1986 and 2025, where, and when? |
| RQ2 | How much flood-storage volume did that conversion remove, and with what uncertainty? |
| RQ3 | Is there measurable evidence of a feedback loop, i.e. are areas that flood more likely to be filled afterwards? |
| RQ4 | Under different planning scenarios, how much wetland and storage could remain by 2050, given projected sea-level rise and subsidence? |

## Data

All data are free.

| Data | Use | Source |
|---|---|---|
| Landsat 5, 7, 8 and 9 (Collection 2, Level 2) | Land-cover maps 1986–2025, 30 m | USGS, via Earth Engine |
| Sentinel-2 surface reflectance | 10 m maps for 2016–2025 | ESA Copernicus, via Earth Engine |
| JRC Global Surface Water v1.4 | Independent check of lagoon-water change, 1984–2021 | Pekel et al. (2016) |
| Global Mangrove Watch v3 | Check of mangrove extent, 1996–2020 | Bunting et al. |
| GHSL built-up surface (R2023A) | Built-up growth, consistent with the earlier flood-risk study | European Commission JRC |
| Copernicus DEM GLO-30 and FABDEM | Ground elevation for the storage calculation | ESA / University of Bristol |
| NASA/IPCC AR6 sea-level projections | Sea-level rise at Lagos to 2050 and 2100 | NASA Sea Level Change team |
| Sentinel-1 radar | Flood extent for recent events (feedback-loop test) | ESA Copernicus |

## Methods

1. **Land-cover mapping.** Dry-season (November–March) cloud-free composites for 1986, 2000, 2013 and 2025 (roughly evenly spaced, 12–14 years apart), classified with a Random Forest (300 trees) into water, wetland/mangrove, other vegetation, built-up and bare sand/fill. Inputs are the reflectance bands, NDVI, MNDWI, NDBI, elevation, and the year's greenest NDVI and its seasonal range, which help separate dry-season grassland from bare sand. Script: [`gee_wetland_change.js`](gee_wetland_change.js).
2. **Accuracy and area estimation.** A confusion matrix for each map, with producer's and user's accuracy, and stratified area estimates with 95 % confidence intervals following Olofsson et al. (2014), rather than raw pixel counts.
3. **Change detection.** From–to change matrices between epochs. LandTrendr on annual Landsat composites is used to date when each pixel was filled, which no published Lagos study has done.
4. **Lost flood storage.** For every pixel converted from wetland or water to fill or built-up:

   $$V = \sum \max\left(0,\; WL_{\text{ref}} - z_{\text{pre}}\right) \times A_{\text{pixel}}$$

   where $WL_{\text{ref}}$ is a reference lagoon water level and $z_{\text{pre}}$ is the ground level before filling. Because global DEMs have errors of one to two metres in flat coastal areas, the result is reported as a Monte Carlo distribution (median and 5–95 % range), not a single number.
5. **Feedback loop.** Flood extents mapped from Sentinel-1 for recent events are compared with later land-cover change, to test whether flooded wetland is more likely to be filled in the following years.
6. **Projection to 2050.** A land-change model (CA-Markov and an artificial neural network) is first validated by hindcasting 2013 → 2025 and reporting the Figure of Merit. It is then run under three scenarios: current trend, wetland protection, and continued megaproject reclamation. Results are combined with AR6 sea-level rise and published subsidence rates.

## Where machine learning is used

- **Random Forest** classification of every land-cover map, with variable importance reported.
- **Neural-network land-change modelling** for the 2050 scenarios.
- **Optional deep-learning comparison** (U-Net) on the 10 m Sentinel-2 years, to see whether it separates sand fill from built-up land better than Random Forest.

## Limitations

- Dredging volumes, permits and lagoon bathymetry are not publicly available, so dredging is inferred from visible change and water turbidity.
- Elevation models were acquired between 2010 and 2015, so ground level before filling has to be approximated for areas filled earlier.
- Landsat 7 images after 2003 have scan-line gaps and are used only to fill gaps in composites.
- A joint rainfall–tide flood analysis would need tide-gauge records that are not freely available.

## Progress

- [x] Literature review ([LITERATURE_REVIEW.md](LITERATURE_REVIEW.md))
- [x] Earth Engine classification script
- [x] Training data and land-cover map for 2025 (267 points; 86.8 % overall accuracy)
- [ ] Land-cover maps for 1986, 2000 and 2013
- [ ] Accuracy assessment and area estimates
- [ ] Change detection and dating of fill
- [ ] Lost-storage estimate
- [ ] Feedback-loop analysis
- [ ] 2050 scenarios
- [ ] Results and discussion

## Key references

- Obiefuna, J. N., Nwilo, P. C., Atagbaza, A. O. & Okolie, C. J. (2013). Spatial changes in the wetlands of Lagos/Lekki Lagoons of Lagos, Nigeria. *Journal of Sustainable Development* 6(7): 123–133. https://doi.org/10.5539/jsd.v6n7p123
- Aniramu, O., Iyanda, O. & Orimoogunje, O. (2026). Remote sensing and GIS-based modelling of land use dynamics and urban flood risk in Lagos megacity for future flood mitigation. *Scientific Reports* 16: 8125. https://doi.org/10.1038/s41598-026-38544-1
- Pekel, J.-F., Cottam, A., Gorelick, N. & Belward, A. S. (2016). High-resolution mapping of global surface water and its long-term changes. *Nature* 540: 418–422. https://doi.org/10.1038/nature20584
- Hawker, L., Uhe, P., Paulo, L., Sosa, J., Savage, J., Sampson, C. & Neal, J. (2022). A 30 m global map of elevation with forests and buildings removed. *Environmental Research Letters* 17: 024016. https://doi.org/10.1088/1748-9326/ac4d4f
- Olofsson, P., Foody, G. M., Herold, M., Stehman, S. V., Woodcock, C. E. & Wulder, M. A. (2014). Good practices for estimating area and assessing accuracy of land change. *Remote Sensing of Environment* 148: 42–57. https://doi.org/10.1016/j.rse.2014.02.015
- Worou, K., Fichefet, T. & Goosse, H. (2023). Future changes in the mean and variability of extreme rainfall indices over the Guinea coast and role of the Atlantic equatorial mode. *Weather and Climate Dynamics* 4: 511–530. https://doi.org/10.5194/wcd-4-511-2023

The full reference list, with each source marked by how well it was checked, is in the [literature review](LITERATURE_REVIEW.md#references).
