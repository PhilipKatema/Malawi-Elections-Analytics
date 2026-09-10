"""
Party reconciliation: turn 54 raw party strings into consistent canonical
codes, and attach human-readable party names for the dashboard legend.

Two problems being solved:
  1. Many labels mean 'independent': IND, INDEPENDENT, IND 1..IND 7,
     INDEPENDENT 2, 'INDEPENDENT (WITHDRAW...'  ->  all become 'IND'.
  2. One label ('UP') means DIFFERENT parties in different years, so the
     name lookup must be year-aware, not a flat dictionary.
"""
import re
import pandas as pd
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "data" / "processed"

# ----------------------------------------------------------------------
# STEP 1 — collapse the 'independent' family to a single canonical code.
# We detect it with a rule (regex) instead of listing every variant, so
# future files with 'IND 8' or 'Independent' are handled automatically.
# ----------------------------------------------------------------------
_IND = re.compile(r"^(IND|INDEPENDENT)\b", re.IGNORECASE)

def canonical_party(raw):
    if pd.isna(raw):
        return pd.NA
    return "IND" if _IND.match(str(raw).strip()) else str(raw).strip().upper()

# ----------------------------------------------------------------------
# STEP 2 — full party names. Only the parties I can attach with confidence;
# the long tail of small parties is left to the abbreviation (see notes).
# 'UP' is deliberately absent here because it is year-dependent (Step 3).
# ----------------------------------------------------------------------
PARTY_NAME = {
    "MCP":   "Malawi Congress Party",
    "UDF":   "United Democratic Front",
    "DPP":   "Democratic Progressive Party",
    "AFORD": "Alliance for Democracy",
    "PP":    "People's Party",
    "UTM":   "UTM Party",
    "MMD":   "Mbakuwaku Movement for Development",
    "PETRA": "People's Transformation Party",
    "MDP":   "Malawi Democratic Party",
    "PPM":   "People's Progressive Movement",
    "MAFUNDE":"Malawi Forum for Unity and Development",
    "IND":   "Independent",
}

# ----------------------------------------------------------------------
# STEP 3 — resolve the ambiguous code 'UP' using the election year.
# 1999: United Party (Bingu wa Mutharika).  2014+: Umodzi Party (John Chisi).
# ----------------------------------------------------------------------
def party_name(canon, year):
    if canon == "UP":
        return "United Party" if year <= 1999 else "Umodzi Party"
    return PARTY_NAME.get(canon, canon)   # fall back to the code itself

# ----------------------------------------------------------------------
# STEP 4 — apply, validate, save
# ----------------------------------------------------------------------
def run():
    df = pd.read_parquet(OUT / "malawi_elections_1994_2020.parquet")
    before_votes = int(df.votes.sum())
    before_codes = df.party.nunique()

    df["party_canonical"] = df["party"].map(canonical_party)
    df["party_name"] = [party_name(c, y) for c, y in zip(df.party_canonical, df.year)]

    # --- validate: no votes may be created or destroyed by relabelling ---
    assert int(df.votes.sum()) == before_votes, "vote total changed!"
    print(f"party codes: {before_codes} raw  ->  {df.party_canonical.nunique()} canonical")
    print(f"vote total unchanged: {before_votes:,}")

    ind_rows = df[df.party_canonical == "IND"]
    print(f"independent rows folded together: {len(ind_rows):,} "
          f"({int(ind_rows.votes.sum()):,} votes)")

    # export an editable mapping table so the logic is transparent, not hidden
    mp = (df[["party","party_canonical","party_name"]]
            .drop_duplicates()
            .sort_values(["party_canonical","party"]))
    mp.to_csv(OUT / "party_map.csv", index=False)

    df.to_csv(OUT / "malawi_elections_enriched.csv", index=False)
    df.to_parquet(OUT / "malawi_elections_enriched.parquet", index=False)
    print("saved enriched dataset + party_map.csv")
    return df

if __name__ == "__main__":
    df = run()
    print("\nTop parties by total votes (canonical):")
    top = (df.groupby(["party_canonical","party_name"]).votes.sum()
             .sort_values(ascending=False).head(12))
    print(top.to_string())
