# Rules

How the definition of a `Variable` decides which operations are meaningful and how its values are aggregated and disaggregated. Nothing is blocked: `warn_unless_permitted`, `warn_unless_aggregation_permitted`, and `warn_unless_disaggregation_permitted` only raise a `MeaninglessOperationWarning`.

## Valid Definitions

A variable has a level of measurement and a `Combination` for each dimension along which its units are combined or split. Every property must be given explicitly; a dimension left out of the combinations is one along which the data never combine or split units, such as time for a single snapshot, and asking for its aggregation or disaggregation raises a `DimensionNotCombinedError`. At least one dimension is required.

| Level | Additivities | Period | Sign |
|---|---|---|---|
| Nominal | Intensive, first, last, non-additive | — | — |
| Ordinal | Those of nominal, maximal, minimal | — | — |
| Interval | All but extensive | — | — |
| Ratio | All | — | Required |
| Cyclic | Intensive, first, last, non-additive | Required | — |

Nominal, ordinal, interval, and ratio form a chain in which each level supports the operations of the ones before it. Cyclic branches off after nominal: its values can be subtracted within one period, but they have no order and no true zero. So only ratio variables can be extensive, and only ordered levels can be maximal or minimal. Chrisman (1998) treats cyclic values as a level of their own; placing it after nominal is this package's simplification.

The sign tells whether a ratio variable can be negative, as for profit or net migration. Its zero still means none, so it can be extensive, but ratios between its values are meaningless.

### Dimensions

`Dimension.SPACE` and `Dimension.TIME` are predefined. Define a `Dimension` for any other breakdown along which values are combined:

| Dimension | Sized | Ordered | Example |
|---|---|---|---|
| Space | Yes: area or length | No | Merging polygons |
| Time | Yes: duration | Yes | Months into a year |
| Depth or elevation layers | Yes: thickness | Yes | Soil horizons into a profile |
| Age groups, industries, sexes | No | Age groups only | Census breakdowns into a total |
| Monitoring stations, wells, sample points | No | No | Stations into a regional value |
| Instants, such as sensor readings | No | Yes | Readings into an hourly value |
| Replicates: climate normals, ensemble members, Monte Carlo runs | No | No | Members into a typical member |

`Weighting.SIZE` needs a sized dimension, and first and last need an ordered one. `Dimension.SPACE` has polygons or lines and `Dimension.TIME` has intervals; give points, instants, and replicates dimensions of their own with other names, such as "station" or "reading", because a dimension is identified by its definition and the same name with a different definition is rejected.

Along a replicate dimension even an extensive quantity is intensive with `Weighting.EQUAL`: the mean of 30 Januaries is a typical January, not their union. Along sized dimensions, `Weighting.EQUAL` for an extensive variable splits a unit into equal shares regardless of size, which is rarely intended.

### Additivity

| Additivity | Value of combined units | Examples |
|---|---|---|
| Extensive | Sum | Population over space and over age groups, sales, precipitation over time |
| Intensive | Weighted central value | Density, rates, temperature, a stock over time, land use of a parcel |
| Maximal | Largest value | Daily maximum temperature over time, worst hazard rank, whether any part is flooded |
| Minimal | Smallest value | Daily minimum temperature over time, whether every part is flooded |
| First | Value of the first part | Opening balance |
| Last | Value of the last part | Closing balance, a stock reported at the end of each period |
| Non-additive | None; recompute from the underlying data | Number of species, median income, percentiles, identifiers |

A stock is intensive over time when its mean over the interval is wanted, because a longer interval does not hold more of it, and last when the value at the end of the interval is wanted, as data warehouses do for semi-additive measures.

A yes-or-no flag is ordinal with no before yes. A nominal identifier, such as a municipality code, is non-additive, because no code describes merged units.

### Weights

Extensive and intensive combinations take a weight, the measure over which the variable is spread; the others take none. An intensive variable is averaged by its weight, and an extensive variable is divided among the parts of a split unit in proportion to it.

| Weight | Intensive: average by | Extensive: divide in proportion to |
|---|---|---|
| `Weighting.SIZE` | Area, duration, or thickness, for densities and values that hold over the whole unit | Size, for a quantity spread evenly |
| `Weighting.EQUAL` | One per unit, for points, instants, and categories | Equal shares |
| A variable | Its values, such as population for income per person | Its values, such as residential floor area for population (dasymetric mapping) |

A weight variable must be non-negative and extensive along the dimension. A weight is required rather than defaulted, because a wrong default silently gives a wrong result: income per person averaged by area instead of by population is still a number. Pass the weight a computation uses to the aggregation and disaggregation checks to catch that mistake.

A stock such as population is intensive over time, so it cannot weight over time. To average income per person over years by population, define person-years, the population times the duration, as a ratio variable extensive over time, and weight by it.

### Typical Variables

| Variable | Level | Space | Time |
|---|---|---|---|
| Sales | Ratio | Extensive | Extensive |
| Profit, net migration | Ratio, signed | Extensive | Extensive |
| Population | Ratio | Extensive | Intensive or last |
| Precipitation in millimeters | Ratio | Intensive by size | Extensive |
| Unemployment rate | Ratio | Intensive by labor force | Intensive by labor force-months |
| Density, prices | Ratio | Intensive | Intensive |
| Temperature in °C | Interval | Intensive | Intensive; maximal or minimal for daily extremes |
| Elevation | Interval | Intensive by size; maximal for peaks | — |
| Wind direction | Cyclic, 360 | Intensive | Intensive |
| Hazard rank | Ordinal | Maximal | Maximal |
| Land use | Nominal | Intensive by size | Last |
| Municipality code | Nominal | Non-additive | — |
| Number of species, median income | Ratio | Non-additive | Non-additive |

## Operations

Operations are statistics over a set of values. ✓ means meaningful.

| Operation | Nominal | Ordinal | Interval | Ratio | Ratio, signed | Cyclic |
|---|---|---|---|---|---|---|
| Sum | | | | Where extensive along some dimension | Where extensive along some dimension | |
| Mode | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Ordering | | ✓ | ✓ | ✓ | ✓ | |
| Median | | ✓ | ✓ | ✓ | ✓ | |
| Difference | | | ✓ | ✓ | ✓ | ✓ |
| Mean | | | ✓ | ✓ | ✓ | |
| Standard deviation | | | ✓ | ✓ | ✓ | |
| Circular mean | | | | | | ✓ |
| Circular standard deviation | | | | | | ✓ |
| Ratio | | | | ✓ | | |
| Geometric mean | | | | ✓ | | |
| Coefficient of variation | | | | ✓ | | |

The mode of continuous values is meaningful only after binning them into classes. A difference between cyclic values must be wrapped into one period. The geometric mean is undefined when any value is zero.

## Aggregation and Disaggregation

Each dimension is decided independently by its combination. Along a dimension the variable is combined over, recomputation from the underlying data is always permitted, because it never relies on the parts. Along any other dimension every method is reported, because the definition says the units are never combined there.

| Additivity | Aggregation | Also accepted | Disaggregation | Also accepted |
|---|---|---|---|---|
| Extensive | Sum | | Proportional to the weight | Total-preserving interpolation, such as pycnophylactic |
| Intensive, nominal | Weighted mode | | Replicate | |
| Intensive, ordinal | Weighted median | Weighted mode | Replicate | |
| Intensive, interval or ratio | Weighted mean | | Replicate | Interpolation, such as bilinear resampling or area-to-point kriging |
| Intensive, cyclic | Weighted circular mean | Weighted mode | Replicate | Interpolation |
| Maximal | Maximum | | Recompute | |
| Minimal | Minimum | | Recompute | |
| First | First value | | Recompute | |
| Last | Last value | | Recompute | |
| Non-additive | Recompute | | Recompute | |

For categories and directions the value of merged units is a convention, so the majority, as in mode resampling of a raster, is accepted beside the central value. For quantities the weighted mean is exact when the weight is the denominator of the variable, so no alternative is accepted. Estimating a surface from points, such as inverse distance weighting from stations, does not split a unit and is outside this package.

Splitting a maximum or a minimum is not a replication: the value of the whole is only an upper or lower bound for each part. The first or last value belongs to one part only. Replication assumes the unit is homogeneous, and proportional division assumes the quantity follows the weight. A split count becomes fractional; round it by a method that keeps the total if whole numbers are needed.

The weighted mode keeps only the dominant category. To keep the others, aggregate the share of each category instead, defined as one intensive ratio variable per category.

## Values That Need Care

The definition describes a variable, not its values, so some properties of the data must be handled when the values are processed. Most of them become ordinary variables after a transformation.

| Data | Problem | Approach |
|---|---|---|
| Missing values | A sum over parts with a missing value is too small; a mean over the others is unbiased only if values are missing at random | Extensive: leave the result missing or impute the part. Intensive: average the others with their weights. Maximal, minimal: the result is only a bound. Non-additive: recompute |
| Values below a detection limit | They are not zero and not missing | Keep them censored and use a method for censored data, or recompute |
| Margins of error, as in census estimates | They do not add up, and they cannot be split | For a sum of independent estimates, sum the variances and take the square root. For a weighted mean, the variance is Σwᵢ²·varᵢ / (Σwᵢ)²; for a ratio of estimates, use the ratio formula of the survey. A variance cannot be divided among the parts of a split unit, and a median's variance cannot be combined; recompute both. Define the margin itself as non-additive |
| Rates that compound, such as growth rates or survival | The combined value is a product, not a sum or a mean | Define log(1 + r), or −log S for survival, as a ratio variable extensive over time, then convert back |
| Layered conductivity or resistivity | Flow across layers follows the harmonic mean, not the arithmetic one | Define the resistance of each layer, thickness divided by conductivity, as a ratio variable extensive over depth, then convert back |
| Graded membership, as in fuzzy classification | A membership is not a category | Define it as a ratio variable from 0 to 1: intensive for the average membership, maximal for a fuzzy union, minimal for a fuzzy intersection |
| Probability that an event occurs | Neither a sum nor a mean for combined units | For independent units, define −log(1 − p) as a ratio variable extensive along the dimension, then convert back |
| Values on a logarithmic scale, such as pH or decibels | Their arithmetic mean is not the mean of the underlying quantity (Stevens' log-interval scale) | Convert to the underlying quantity, such as a concentration or a power, and define it as a ratio variable |
| Vectors, such as wind weighted by speed | The direction cannot be averaged on its own, and speed is not extensive | Define the eastward and northward components, u and v, as ratio variables, aggregate them, and derive the direction afterwards |
| Compositions, such as land use shares | Shares must keep summing to one | Aggregate each share as an intensive ratio variable with the same weight; the sum is then kept |
| Cyclic categories, such as weekdays | Not ordinal | Define them as nominal, or, when numbered, as cyclic, such as months 1 to 12 with a period of 12 |
| Units of measurement | Additivity depends on the unit: precipitation in millimeters is intensive over space, in cubic meters extensive | Define each unit as its own variable; converting between units is outside this package |

## Combining Along Several Dimensions

Each dimension is checked on its own, so the package cannot tell whether aggregations along several dimensions agree. Combining space first and time second gives the same result as the reverse order only when the weights agree: an unemployment rate weighted by the labor force over space and by labor force-months over time is consistent, because labor force-months are the labor force times the duration, but weighting it by population over time is not. Choose weights that describe the same underlying quantity along every dimension, or recompute from the underlying data.

A dimension is identified by its name, size, and order. Two dimensions whose names match apart from case and spacing but whose definitions differ are rejected wherever they meet, because one of them is almost always a mistake.
