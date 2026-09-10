# Malawi Elections 1994–2020 — Unified Dataset

**Grain:** one row = one candidate's result in one place in one election.
**Rows:** 189,419  **Files combined:** 12  **Format:** tidy / long.

## Columns

|column|type|notes|
|-|-|-|
|year|int|1994, 1999, 2004, 2009, 2014, 2019, 2020|
|election\_type|text|`presidential` or `parliamentary`|
|region|text|Normalized to `Northern` / `Central` / `Southern`|
|district|text|Title-cased, trimmed|
|constituency|text|Parliamentary + 2019/2020 presidential; blank for older presidential|
|ward|text|Station-level files only (2019/2020)|
|centre|text|Station-level files only|
|station|text|Station-level files only|
|candidate|text|Parsed out of the source column/field|
|party|text|Uppercase abbreviation (MCP, UDF, DPP, UTM, IND, ...)|
|votes|int|Votes for THIS candidate in THIS place|
|valid\_votes|int|Total valid votes at that place (repeats across candidates)|
|null\_void|int|Spoiled ballots at that place (where reported)|
|total\_voted|int|Total ballots cast (where reported)|
|registered|int|Registered voters (where reported)|
|granularity|text|`district`, `constituency`, or `station`|

## Important caveats

* **Granularity is mixed.** Presidential 1994–2014 is district-level; 2019/2020 is polling-station level; parliamentary 1994–2014 is constituency-level; 2019 is station-level. 
* Party abbreviations are uppercased but NOT yet reconciled across years (e.g. `IND` vs `INDEPENDENT`). A follow-up mapping table is recommended.

