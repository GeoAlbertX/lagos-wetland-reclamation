// =====================================================================
// Wetland loss and land reclamation in Lagos, 1986–2024
// Google Earth Engine script: land-cover maps with Random Forest,
// accuracy assessment and wetland-change statistics.
//
// HOW TO USE
// 1. Open https://code.earthengine.google.com and paste this script.
// 2. Choose the year to classify in YEAR below (run once per epoch).
// 3. Create training points with the geometry tools (point icon),
//    one layer per class, each imported as a FeatureCollection with
//    a numeric property "class":
//        water = 0, wetland_mangrove = 1, other_vegetation = 2,
//        built_up = 3, bare_sand_fill = 4
//    Name the imports exactly: water, wetland, vegetation, builtup, bare.
//    Aim for 50–100 well-spread points per class. Use the true-colour
//    composite, the JRC water layer and Google satellite basemap to judge.
// 4. Run. Check the accuracy printed in the Console, then use the
//    Tasks tab to export the classified map and the area table.
// =====================================================================

// ---------------- settings -------------------------------------------
var YEAR = 2024;          // epochs used in the study: 1986, 2000, 2013, 2024
var TREES = 300;
var SEED = 42;

// Study area: Lagos State (FAO GAUL level 1)
var lagos = ee.FeatureCollection('FAO/GAUL/2015/level1')
  .filter(ee.Filter.eq('ADM1_NAME', 'Lagos'));
var aoi = lagos.geometry();
Map.centerObject(aoi, 10);

// ---------------- Landsat Collection 2 Level-2 -----------------------
// Dry season (November of the previous year to March) to avoid
// rainy-season cloud. Landsat 7 is used only as a fallback because of
// the 2003 scan-line gaps.
function maskAndScale(img) {
  var qa = img.select('QA_PIXEL');
  var clear = qa.bitwiseAnd(1 << 1).eq(0)       // dilated cloud
    .and(qa.bitwiseAnd(1 << 3).eq(0))           // cloud
    .and(qa.bitwiseAnd(1 << 4).eq(0));          // cloud shadow
  var sr = img.select('SR_B.').multiply(0.0000275).add(-0.2);
  return img.addBands(sr, null, true).updateMask(clear);
}

function renameTM(img) {   // Landsat 5 / 7
  return img.select(['SR_B1', 'SR_B2', 'SR_B3', 'SR_B4', 'SR_B5', 'SR_B7'],
                    ['blue', 'green', 'red', 'nir', 'swir1', 'swir2']);
}
function renameOLI(img) {  // Landsat 8 / 9
  return img.select(['SR_B2', 'SR_B3', 'SR_B4', 'SR_B5', 'SR_B6', 'SR_B7'],
                    ['blue', 'green', 'red', 'nir', 'swir1', 'swir2']);
}

function landsatComposite(year) {
  var start = ee.Date.fromYMD(year - 1, 11, 1);
  var end = ee.Date.fromYMD(year, 3, 31);
  var tm = ee.ImageCollection('LANDSAT/LT05/C02/T1_L2')
    .merge(ee.ImageCollection('LANDSAT/LE07/C02/T1_L2'))
    .filterBounds(aoi).filterDate(start, end).map(maskAndScale).map(renameTM);
  var oli = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
    .merge(ee.ImageCollection('LANDSAT/LC09/C02/T1_L2'))
    .filterBounds(aoi).filterDate(start, end).map(maskAndScale).map(renameOLI);
  var col = year >= 2013 ? oli : tm;
  return col.median().clip(aoi);
}

// ---------------- features -------------------------------------------
function addFeatures(img) {
  var ndvi = img.normalizedDifference(['nir', 'red']).rename('NDVI');
  var mndwi = img.normalizedDifference(['green', 'swir1']).rename('MNDWI');
  var ndbi = img.normalizedDifference(['swir1', 'nir']).rename('NDBI');
  var elev = ee.ImageCollection('COPERNICUS/DEM/GLO30').select('DEM')
    .mosaic().clip(aoi).rename('elevation');
  return img.addBands([ndvi, mndwi, ndbi, elev]);
}

var composite = addFeatures(landsatComposite(YEAR));
var bands = ['blue', 'green', 'red', 'nir', 'swir1', 'swir2',
             'NDVI', 'MNDWI', 'NDBI', 'elevation'];

Map.addLayer(composite, {bands: ['red', 'green', 'blue'], min: 0, max: 0.25},
             'True colour ' + YEAR);
Map.addLayer(composite, {bands: ['swir1', 'nir', 'red'], min: 0, max: 0.4},
             'False colour (SWIR-NIR-Red) ' + YEAR, false);

// Reference layer: JRC Global Surface Water occurrence 1984–2021
var gsw = ee.Image('JRC/GSW1_4/GlobalSurfaceWater').clip(aoi);
Map.addLayer(gsw.select('occurrence'), {min: 0, max: 100, palette: ['white', 'blue']},
             'JRC water occurrence 1984–2021', false);

// ---------------- training and classification ------------------------
// The training layers (water, wetland, vegetation, builtup, bare) are the
// geometry imports created in step 3 above.
var points = water.merge(wetland).merge(vegetation).merge(builtup).merge(bare);

var samples = composite.select(bands).sampleRegions({
  collection: points, properties: ['class'], scale: 30, tileScale: 4
}).randomColumn('rand', SEED);

var train = samples.filter(ee.Filter.lt('rand', 0.7));
var test = samples.filter(ee.Filter.gte('rand', 0.7));

var rf = ee.Classifier.smileRandomForest({numberOfTrees: TREES, seed: SEED})
  .train({features: train, classProperty: 'class', inputProperties: bands});

var classified = composite.select(bands).classify(rf).rename('class');

var palette = ['1f78b4', '33a02c', 'b2df8a', 'e31a1c', 'fdbf6f'];
Map.addLayer(classified, {min: 0, max: 4, palette: palette}, 'Land cover ' + YEAR);

// ---------------- accuracy assessment --------------------------------
var cm = test.classify(rf).errorMatrix('class', 'classification');
print('Confusion matrix (rows = reference, columns = map)', cm);
print('Overall accuracy', cm.accuracy());
print('Kappa', cm.kappa());
print("Producer's accuracy (per class)", cm.producersAccuracy());
print("User's accuracy (per class)", cm.consumersAccuracy());
print('Variable importance', ee.Dictionary(rf.explain()).get('importance'));

// ---------------- area per class (km²) --------------------------------
var areaImg = ee.Image.pixelArea().divide(1e6).addBands(classified);
var areas = areaImg.reduceRegion({
  reducer: ee.Reducer.sum().group({groupField: 1, groupName: 'class'}),
  geometry: aoi, scale: 30, maxPixels: 1e13, tileScale: 4
});
print('Mapped area by class (km²), ' + YEAR, areas);

// ---------------- exports ---------------------------------------------
Export.image.toDrive({
  image: classified.toByte(),
  description: 'lagos_landcover_' + YEAR,
  folder: 'lagos_wetlands',
  region: aoi, scale: 30, maxPixels: 1e13
});

Export.table.toDrive({
  collection: ee.FeatureCollection(ee.List(areas.get('groups')).map(function (g) {
    return ee.Feature(null, ee.Dictionary(g)).set('year', YEAR);
  })),
  description: 'lagos_class_areas_' + YEAR,
  folder: 'lagos_wetlands',
  fileFormat: 'CSV'
});

Export.table.toDrive({
  collection: test.classify(rf),
  description: 'lagos_accuracy_points_' + YEAR,
  folder: 'lagos_wetlands',
  fileFormat: 'CSV'
});

// Next steps (separate scripts): compare epochs to map wetland converted to
// built-up or bare fill, then estimate lost flood storage from the DEM.
