"""
Malawi election results harmonizer.
Turns 12 differently-shaped Excel files (1994-2020, presidential + parliamentary)
into ONE tidy long-format table: one row per (election, place, candidate).
"""
import re
import pandas as pd
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "data" / "raw"

# ----------------------------------------------------------------------
# STEP 1 — small, reusable cleaning helpers
# ----------------------------------------------------------------------
def coerce_int(series):
    """Vote counts are stored as text ('40098', sometimes '1,470' or ' ').
    Strip commas/spaces, turn '' into missing, return a nullable integer column.
    If the column is absent (None), return an all-missing column."""
    if series is None:
        return pd.Series(pd.NA, dtype="Int64")
    s = (series.astype("string")
                .str.replace(",", "", regex=False)
                .str.strip()
                .replace({"": pd.NA, "-": pd.NA, "nan": pd.NA}))
    return pd.to_numeric(s, errors="coerce").astype("Int64")

def clean_place(series):
    """District/constituency names arrive as 'CHITIPA', ' CHITIPA', 'Chitipa'.
    Trim, collapse inner spaces, Title-Case so they match across years."""
    s = series.astype("string").str.strip().str.replace(r"\s+", " ", regex=True)
    return s.str.title()

REGION_MAP = {
    "northern": "Northern", "northern region 1": "Northern",
    "central":  "Central",  "central region 2":  "Central",
    "southern": "Southern", "southern region 3": "Southern",
}
def normalize_region(series):
    """Collapse 'Northern Region 1' / 'Northern' -> 'Northern'."""
    s = series.astype("string").str.strip().str.lower()
    return s.map(lambda x: REGION_MAP.get(x, x.title() if isinstance(x, str) else x))

# leading code like '001 ' or trailing ' 01' / ' 001' on constituency names
_LEAD_CODE = re.compile(r"^\s*\d{1,4}\s+")
_TRAIL_CODE = re.compile(r"\s+\d{1,4}\s*$")
def clean_constituency(series):
    s = series.astype("string").str.strip()
    s = s.str.replace(_LEAD_CODE, "", regex=True)
    s = s.str.replace(_TRAIL_CODE, "", regex=True)
    return s.str.replace(r"\s+", " ", regex=True).str.title()

# ----------------------------------------------------------------------
# STEP 2 — parse a candidate header like:
#   'Bakili Muluzi - UDF'      -> ('Bakili Muluzi', 'UDF')
#   'Lazarus Chakwera (MCP)'   -> ('Lazarus Chakwera', 'MCP')
#   'Bingu wa Mutharika\n(DPP)'-> ('Bingu wa Mutharika', 'DPP')
# ----------------------------------------------------------------------
def parse_candidate_header(h):
    h = str(h).replace("\n", " ").strip()
    m = re.match(r"^(.*?)\s*\(([^)]+)\)\s*$", h)      # Name (PARTY)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    if " - " in h:                                     # Name - PARTY
        name, party = h.rsplit(" - ", 1)
        return name.strip(), party.strip()
    return h, pd.NA

# Final column order for every produced frame
COLS = ["year","election_type","region","district","constituency","ward",
        "centre","station","candidate","party","votes","valid_votes",
        "null_void","total_voted","registered","granularity","source_file"]

# ----------------------------------------------------------------------
# STEP 3 — loader for LONG files (parliamentary: already one row/candidate)
# We just rename each file's columns to our standard names.
# ----------------------------------------------------------------------
def load_long(file, year, sheet, rename, granularity):
    df = pd.read_excel(SRC / file, sheet_name=sheet, dtype=str)
    df = df.rename(columns=rename)
    out = pd.DataFrame()
    out["region"]       = normalize_region(df["region"])
    out["district"]     = clean_place(df["district"])
    out["constituency"] = clean_constituency(df["constituency"])
    out["candidate"]    = df["candidate"].astype("string").str.strip()
    out["party"]        = df["party"].astype("string").str.strip().str.upper()
    out["votes"]        = coerce_int(df["votes"])
    out["valid_votes"]  = coerce_int(df.get("valid_votes"))
    out["null_void"]    = coerce_int(df.get("null_void"))
    out["total_voted"]  = coerce_int(df.get("total_voted"))
    out["registered"]   = coerce_int(df.get("registered"))
    # station-level parliamentary (2019) also has ward/centre/station
    for extra in ["ward","centre","station"]:
        out[extra] = clean_place(df[extra]) if extra in df else pd.NA
    out["year"] = year
    out["election_type"] = "parliamentary"
    out["granularity"] = granularity
    out["source_file"] = file
    return out.reindex(columns=COLS)

# ----------------------------------------------------------------------
# STEP 4 — loader for WIDE files (presidential: one column per candidate).
# We MELT candidate columns into rows, then parse name/party from the header.
# ----------------------------------------------------------------------
def load_wide(file, year, sheet, id_cols, cand_cols, meta_map, granularity):
    df = pd.read_excel(SRC / file, sheet_name=sheet, dtype=str)
    melted = df.melt(id_vars=id_cols, value_vars=cand_cols,
                     var_name="cand_header", value_name="votes")
    parsed = melted["cand_header"].map(parse_candidate_header)
    melted["candidate"] = parsed.map(lambda t: t[0])
    melted["party"]     = parsed.map(lambda t: t[1])
    out = pd.DataFrame()
    out["region"]       = normalize_region(melted[meta_map["region"]])
    out["district"]     = clean_place(melted[meta_map["district"]])
    out["constituency"] = (clean_constituency(melted[meta_map["constituency"]])
                           if "constituency" in meta_map else pd.NA)
    for extra in ["ward","centre","station"]:
        out[extra] = clean_place(melted[meta_map[extra]]) if extra in meta_map else pd.NA
    out["candidate"]   = melted["candidate"].astype("string").str.strip()
    out["party"]       = melted["party"].astype("string").str.strip().str.upper()
    out["votes"]       = coerce_int(melted["votes"])
    out["valid_votes"] = coerce_int(melted[meta_map["valid_votes"]]) if "valid_votes" in meta_map else pd.NA
    out["null_void"]   = coerce_int(melted[meta_map["null_void"]])   if "null_void"   in meta_map else pd.NA
    out["total_voted"] = coerce_int(melted[meta_map["total_voted"]]) if "total_voted" in meta_map else pd.NA
    out["registered"]  = coerce_int(melted[meta_map["registered"]])  if "registered"  in meta_map else pd.NA
    out["year"] = year
    out["election_type"] = "presidential"
    out["granularity"] = granularity
    out["source_file"] = file
    return out.reindex(columns=COLS)

# ----------------------------------------------------------------------
# STEP 5 — configs: describe each file once, declaratively.
# ----------------------------------------------------------------------
# Parliamentary (LONG). Each dict maps THIS file's headers -> our names.
PARL = [
    dict(file="Parliamentary1994ElectionsStructured.xlsx", year=1994,
         sheet="Parliamentary Results", granularity="constituency",
         rename={"Region":"region","District":"district","Constituency":"constituency",
                 "Candidate":"candidate","Party":"party","Votes":"votes",
                 "Valid Votes":"valid_votes","Null & Void":"null_void",
                 "Registered Voters":"registered","Total Votes":"total_voted"}),
    dict(file="PARLIAMENTARYRESULTS1999_conv.xlsx", year=1999,
         sheet="Parliamentary", granularity="constituency",
         rename={"Region":"region","District":"district","Constituency":"constituency",
                 "Candidate":"candidate","Party":"party","Votes":"votes",
                 "Valid Votes":"valid_votes","Null & Void":"null_void",
                 "Registered Voters":"registered","Total Votes Cast":"total_voted"}),
    dict(file="PARLIAMENTARYSUMMARYRESULTSFOR2004ELECTIONS_conv.xlsx", year=2004,
         sheet="Structured Results", granularity="constituency",
         rename={"Region":"region","District":"district","Constituency":"constituency",
                 "Candidate":"candidate","Party":"party","Votes":"votes",
                 "Valid Votes":"valid_votes","Null and Void":"null_void",
                 "Total Registered":"registered","Total Votes":"total_voted"}),
    dict(file="ParliamentaryResults29May09_conv.xlsx", year=2009,
         sheet="Results", granularity="constituency",
         rename={"Region":"region","District":"district","Constituency":"constituency",
                 "Candidate":"candidate","Party":"party","Votes":"votes",
                 "Valid Votes":"valid_votes","Null & Void":"null_void",
                 "Registered Voters":"registered","Total Votes":"total_voted"}),
    dict(file="Parliamentresults_2014_conv.xlsx", year=2014,
         sheet="Results", granularity="constituency",   # NB: 'Results', NOT 'AllPages'
         rename={"Region":"region","District":"district","Constituency":"constituency",
                 "Candidate":"candidate","Party":"party","Votes":"votes",
                 "Valid Votes":"valid_votes","Null & Void":"null_void",
                 "Registered Voters":"registered","Total Votes":"total_voted"}),
    dict(file="2019ParliamentaryResultsByPollingStation_conv.xlsx", year=2019,
         sheet="Structured Results", granularity="station",
         rename={"Region":"region","District":"district","Constituency":"constituency",
                 "Ward":"ward","Centre":"centre","Station":"station",
                 "Candidate":"candidate","Party":"party","Votes":"votes",
                 "Valid Votes":"valid_votes","Null & Void":"null_void",
                 "Total Votes":"total_voted"}),
]

# Presidential (WIDE). List candidate columns explicitly + map meta columns.
PRES = [
    dict(file="1994_presidential_results.xlsx", year=1994, sheet="By District",
         granularity="district",
         id_cols=["Region","District","District Valid Votes","Null & Void",
                  "Registered Voters","Total Votes Cast"],
         cand_cols=["Chakufwa Chihana - AFORD","Dr. H. Kamuzu Banda - MCP",
                    "Bakili Muluzi - UDF","Kamlepo Kalua - MDP"],
         meta_map=dict(region="Region",district="District",
                       valid_votes="District Valid Votes",null_void="Null & Void",
                       registered="Registered Voters",total_voted="Total Votes Cast")),
    dict(file="1999_presidential_results.xlsx", year=1999, sheet="Wide Format",
         granularity="district",
         id_cols=["Region","District","Valid Votes","Null & Void",
                  "Registered Voters","Total Votes Cast"],
         cand_cols=["Mr. Chakuamba, Gwanda - MCP","Mr. Kalua, Kamlepo - MDP",
                    "Dr. Muluzi, Bakili - UDF","Dr. Mutharika, Bingu wa - UP",
                    "Bishop Nkhumbwe, Daniel Kamfosi - CONU"],
         meta_map=dict(region="Region",district="District",valid_votes="Valid Votes",
                       null_void="Null & Void",registered="Registered Voters",
                       total_voted="Total Votes Cast")),
    dict(file="PRESIDENTIALSUMMARYRESULTSFOR2009ELECTIONS_conv.xlsx", year=2009,
         sheet="Results", granularity="district",
         id_cols=["Region","District","Valid\nVotes","Null &\nVoid","Total Voted",
                  "Registered\nVoters"],
         cand_cols=["Bingu wa Mutharika\n(DPP)","Kamuzu W. Chibambo\n(PETRA)",
                    "Loveness Gondwe\n(NARC)","Stanley E. Masauli\n(RP)",
                    "Gowa D. Nyasulu\n(AFORD)","James M. Nyondo\n(IND)",
                    "John Z.U. Tembo\n(MCP)"],
         meta_map=dict(region="Region",district="District",valid_votes="Valid\nVotes",
                       null_void="Null &\nVoid",total_voted="Total Voted",
                       registered="Registered\nVoters")),
    dict(file="04_PRESIDENTIAL_SUMMARY_RESULTS_FOR_2014_ELECTIONS_conv.xlsx", year=2014,
         sheet="Restructured", granularity="district",
         id_cols=["Region","District","Valid votes","Null and void","Total voted"],
         cand_cols=["Dr. Joyce Hilda BANDA - PP","Dr. Lazarus McCarthy CHAKWERA - MCP",
                    "Kamuzu Walter CHIBAMBO - PETRA","Prof. John CHISI - UP",
                    "Friday Anderson JUMBE - NLP","Aaron Davies Chester KATSONGA - CCP",
                    "Mark KATSONGA PHIRI - PPM","Atupele MULUZI - UDF",
                    "Prof. Peter MUTHARIKA - DPP","George NNENSA - MAFUNDE",
                    "James Mbowe NYONDO - NASAF","Abusa Helen SINGH - UIP"],
         meta_map=dict(region="Region",district="District",valid_votes="Valid votes",
                       null_void="Null and void",total_voted="Total voted")),
    dict(file="2019PresidentialResultsByPollingStation_conv.xlsx", year=2019,
         sheet="Structured Data", granularity="station",
         id_cols=["Region","District","Constituency","Ward","Centre Name",
                  "Polling Station","Valid Votes","Null & Void","Total Voted"],
         cand_cols=["Lazarus Chakwera (MCP)","Arthur Peter Mutharika (DPP)",
                    "Saulos Chilima (UTM)","Atupele Muluzi (UDF)","Peter Kuwani (MMD)",
                    "John Chisi (UP)","Hadwick Kaliya (IND)"],
         meta_map=dict(region="Region",district="District",constituency="Constituency",
                       ward="Ward",centre="Centre Name",station="Polling Station",
                       valid_votes="Valid Votes",null_void="Null & Void",
                       total_voted="Total Voted")),
    dict(file="2020FreshPresidentialElectionResultsPerstation_conv.xlsx", year=2020,
         sheet="Structured Data", granularity="station",
         id_cols=["Region","District","Constituency","Ward","Centre Name",
                  "Polling Station","Registered Voters","Valid Votes","Null & Void",
                  "Total Voted"],
         cand_cols=["Lazarus Chakwera (MCP)","Peter Kuwani (MMD)","Peter Mutharika (DPP)"],
         meta_map=dict(region="Region",district="District",constituency="Constituency",
                       ward="Ward",centre="Centre Name",station="Polling Station",
                       registered="Registered Voters",valid_votes="Valid Votes",
                       null_void="Null & Void",total_voted="Total Voted")),
]

# ----------------------------------------------------------------------
# STEP 6 — run everything, stack, validate, save
# ----------------------------------------------------------------------
def build():
    frames = []
    for c in PARL:
        f = load_long(**c); print(f"  parl {c['year']}: {len(f):>6} rows"); frames.append(f)
    for c in PRES:
        f = load_wide(**c); print(f"  pres {c['year']}: {len(f):>6} rows"); frames.append(f)
    data = pd.concat(frames, ignore_index=True)
    # drop rows where a melted candidate column was blank (no vote value at all)
    data = data[data["votes"].notna()].reset_index(drop=True)
    return data

if __name__ == "__main__":
    df = build()
    print("\nTOTAL rows:", len(df))
    print("Years:", sorted(df.year.unique()))
    out_dir = Path(__file__).resolve().parents[1] / "data" / "processed"; out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "malawi_elections_1994_2020.csv", index=False)
    df.to_parquet(out_dir / "malawi_elections_1994_2020.parquet", index=False)
    print("Saved CSV + Parquet.")
