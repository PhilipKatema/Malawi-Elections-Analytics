# Malawi Elections Analytics (1994-2020)

**A full-cycle data analytics study of every Malawian presidential and parliamentary election from the founding multiparty vote of 1994 to the court-ordered presidential re-run of 2020** - from 12 messy official PDF files to a harmonized 189,419-row dataset, seven political-science metrics, district-level maps, and a publish-ready findings report.

[[Presidential winner by district, 2019 vs 2020](https://github.com/PhilipKatema/Malawi-Elections-Analytics/blob/main/docs/figures/metric_b2.png)]

*The whole story in one image: in 2019 Malawi is three colors - a UTM-purple North, an MCP-green Centre, a DPP-blue South. In the 2020 re-run the purple vanishes: every UTM district (and only the UTM districts) flips to MCP. Not one district changed hands between the two big parties directly.*

## The headline finding

Between the annulled 2019 election (the "Tipp-Ex election," overturned by Malawi's Constitutional Court in February 2020) and the fresh 2020 poll:

* The **effective number of presidential competitors collapsed from 3.15 to 1.95** - a 38% contraction of the field, with the same electorate voting 13 months apart.
* **MCP's vote share jumped from 35.4% to 59.3%** - almost exactly its 2019 share plus UTM's.
* MCP gained **50-64 percentage points** in the districts where Saulos Chilima's UTM ran strongest in 2019 (Ntcheu +64, Chitipa +63, Karonga +61, Rumphi +60), while the DPP's Southern heartland barely moved.
* A quarter of the national vote changed party labels between the two polls (**25.6% Pedersen volatility**) - two similar-looking elections hiding a massive reshuffle.

The 2020 result was not a national mood swing. It was a **geographically surgical coalition transfer**, made arithmetically necessary by the Constitutional Court's new 50%+1 majority rule - and the data shows it in a way headlines never could.

## What's in the analysis

**Behavioural metrics (Part A of the notebook)**

|#|Metric|Question it answers|
|-|-|-|
|1|Effective number of competitors (Laakso-Taagepera)|How fragmented is the vote? Did 2020 consolidate it?|
|2|Margin of victory + competitiveness tiers (+ swing map)|Which seats are safe vs genuine swing markets? Where did the 2020 swing land?|
|3|Pedersen volatility|How much support churns between elections?|
|4|Regional concentration (Herfindahl)|Is a party regional or national?|
|5|Split-ticket divergence|Do voters back one party for President, another for MP?|
|6|Wasted-vote share|How much of the vote elects nobody under FPTP?|
|7|Incumbent re-election|Do sitting MPs survive? *(plus a lesson in join fragility)*|

**Descriptive analytics (Part B)** - national vote share by party, district winner maps, seats won by party, region × party dominance heatmaps, winning-margin choropleths, turnout (with an honest exclusion of two corrupted/missing registration years), Gallagher disproportionality, and bellwether districts.

Some long-arc findings:

* Parliamentary **safe seats fell from 88% (1994) to 38% (2019)**; tossups rose from 6% to 35%.
* The **mean wasted-vote share doubled from 25% to 56%** - by 2014 the average winning MP was opposed by more voters than backed them. This is the arithmetic behind Malawi's move to a 50%+1 presidential rule.
* **Independents** grew from 4 parliamentary seats (1999) to a 52-55 seat bloc (2014-2019) - the second-largest "party" in the National Assembly.
* Gallagher disproportionality **spiked to 16.3 in 2009**, when the DPP converted 40% of the vote into 59% of the seats.
* Tiny **Likoma island is Malawi's perfect bellwether** (matched the national presidential winner in all 4 elections it appears in); Lilongwe and Dedza are the strongest partisan anchors (matched once in six).

## Repository structure

```
├── data/
│   ├── raw/                  # the 12 MEC source workbooks
│   ├── processed/            # malawi\\\_elections\\\_enriched.csv - the harmonized dataset
│   ├── geo/                  # malawi\\\_districts.geojson - 28-district boundaries (Natural Earth-derived)
│   └── DATA\\\_DICTIONARY.md    # column definitions, grain, caveats
├── src/
│   ├── harmonize.py          # 12 heterogeneous Excel files -> one long table
│   └── party\\\_reconcile.py    # 54 raw party strings -> 44 canonical codes
├── notebooks/
│   └── Malawi\\\_Elections\\\_Analysis.ipynb   # the full analysis, written as a learning document
├── outputs/                  # every computed metric table as CSV (m1-m7, b1-b7)
├── report/
│   └── Malawi\\\_Elections\\\_Report.docx      # 26-page publish-ready findings report with all figures
├── docs/figures/             # every chart and map as PNG
└── assets/social/            # hi-res social-media exports


## The data cleaning story (why this repo exists)

The 12 source files span two administrative eras and two shapes: hand-compiled **wide** district summaries (1994-2014 presidential) and station-level **long** returns (2019-2020). The pipeline's core ideas, all explained inline in the code and notebook:

* **Grain as an explicit column.** 97% of rows come from the 2019-2020 station-level files; every metric first rolls up to a stated, consistent grain so early elections aren't drowned.
* **Votes vs denominators.** Columns like `valid\\\_votes` describe the *place* and repeat on every candidate row - the pipeline splits them into a deduplicated one-row-per-place table before any aggregation.
* **Declarative file configs.** Each source file is described once (sheet, column map, granularity); two generic loaders do all the work.
* **Rules over lists.** Independent-party variants (`IND 1`…`IND 7`, `INDEPENDENT 2`, …) are collapsed by regex, so future files are handled automatically.
* **Year-aware lookups.** The abbreviation `UP` names two different parties in different eras.
* **Invariant assertions.** The 51.6M-vote national total is asserted identical before and after reconciliation.
* **Canonical districts.** 33 raw district spellings (Chikwawa/Chikhwawa, Nkhata Bay/Nkhatabay, …) collapse to Malawi's 28 official districts before any per-district count.

## Honest limitations

* **No 2004 presidential file** - the 1999→2009 presidential volatility step spans a decade and is flagged as an interval artifact.
* **2019 voter registration is missing and 2020's is corrupted** (it implies a 24% turnout against a true \~65%), so turnout is reported only for 1994-2014.
* **The incumbency metric's 2004→2009 and 2009→2014 transitions are join artifacts** (inconsistent name formats across file pairs) and are flagged as such - kept in deliberately as the project's clearest data-quality lesson.
* The Gallagher index was corrected during development after an earlier draft merged co-running independents into one bloc (17-29 phantom seats per year); the notebook documents the fix. *The metric is only as trustworthy as the join beneath it.*

## Roadmap

* Ingest the **2025** station-level results - turning the 2020 consolidation into the middle of a rise-and-fall arc (the Tonse Alliance dissolved in 2024; the DPP returned in 2025).
* Source clean 2019/2020 registration data to unlock the turnout-elasticity question.
* Fuzzy name-matching to rehabilitate the incumbency metric.
* An **interactive dashboard** built on the `outputs/` tables and district geometry.

## License \& data notes

Code is MIT-licensed. Election results are public records of the Malawi Electoral Commission; district boundaries derive from Natural Earth (public domain), with one documented geometry correction (a mislabeled Karonga polygon). The full findings report in `report/` includes source citations for all external political context.

