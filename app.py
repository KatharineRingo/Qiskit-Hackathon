"""Streamlit UI for the Undertow demo.  Run:  streamlit run app.py"""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

sys.path.insert(0, str(Path(__file__).parent / "src"))

from undertow.data_synthetic import adjacency_pairs, make_grid_network  # noqa: E402
from undertow.metrics import score_plan  # noqa: E402
from undertow.qubo import build_program  # noqa: E402
from undertow.risk import add_scores  # noqa: E402
from undertow.solve import num_qubits, solve_current_policy, solve_exact, solve_qaoa  # noqa: E402
from undertow.viz import build_map  # noqa: E402

st.set_page_config(page_title="Undertow", page_icon="🌊", layout="wide")
st.title("🌊 Undertow: which road repairs to fund")
st.caption("Hidden-damage risk → shortlist → QUBO → QAOA vs classical vs the current 311-report policy")

with st.sidebar:
    st.header("Controls")
    budget = st.slider("Repair budget (cost units)", 2, 16, 8)
    k = st.slider("Candidates sent to optimizer", 4, 12, 10, help="More candidates = more qubits = slower.")
    reps = st.slider("QAOA layers (reps)", 1, 4, 2)
    use_qaoa = st.checkbox("Run QAOA simulator", value=True)
    run = st.button("Run optimization", type="primary", width="stretch")


@st.cache_data(show_spinner=False)
def run_all(budget, k, reps, use_qaoa):
    csv = Path(__file__).parent / "data" / "segments.csv"
    df = pd.read_csv(csv) if csv.exists() else make_grid_network()[1]
    df = add_scores(df)
    pairs_all = adjacency_pairs(df)
    cand = df.sort_values("value", ascending=False).head(k)
    ids = set(cand["segment_id"])
    pairs = [(a, b) for a, b in pairs_all if a in ids and b in ids]
    qp = build_program(cand, pairs, budget)
    results = [solve_current_policy(df, budget), solve_exact(qp)]
    if use_qaoa:
        results.append(solve_qaoa(qp, reps=reps, label="QAOA simulator"))
    rows = []
    for r in results:
        s = score_plan(df, pairs_all, r.chosen)
        rows.append({"plan": r.name, **s, "seconds": round(r.seconds, 2),
                     "repairs": " ".join(sorted(r.chosen))})
    table = pd.DataFrame(rows).set_index("plan")
    fmap = build_map(df, {r.name: r.chosen for r in reversed(results)},
                     scores={r["plan"]: {k: v for k, v in r.items() if k != "plan"} for r in rows},
                     demo_data=not csv.exists())
    return df, table, fmap._repr_html_(), len(df), num_qubits(qp)


if run or "done" in st.session_state:
    st.session_state["done"] = True
    with st.spinner("Solving…"):
        df, table, map_html, n_seg, n_qubits = run_all(budget, k, reps, use_qaoa)

    c1, c2, c3 = st.columns(3)
    c1.metric("Segments in city", n_seg)
    c2.metric("Qubits needed", n_qubits)
    best = table["hidden_risk_removed"].idxmax()
    base = table.iloc[0]["hidden_risk_removed"]
    c3.metric("Best plan", best, f"+{table['hidden_risk_removed'].max() - base:.2f} risk removed vs current policy")

    left, right = st.columns([3, 2])
    with left:
        st.subheader("Map")
        components.html(map_html, height=560)
    with right:
        st.subheader("Plan comparison")
        st.dataframe(table.drop(columns=["repairs"]), width="stretch")
        st.bar_chart(table[["hidden_risk_removed"]])
        st.bar_chart(table[["evac_route_open_%"]])
    st.subheader("Segments repaired")
    st.dataframe(table[["repairs"]], width="stretch")
    with st.expander("Scored segments"):
        st.dataframe(df, width="stretch")
else:
    st.info("Set the controls on the left and click **Run optimization**.")

