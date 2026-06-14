from __future__ import annotations

from pathlib import Path

import streamlit as st

from India_runs_data_and_ai_challenge.ranker import load_candidates, score_candidate


ROOT = Path(__file__).resolve().parent
SAMPLE_PATH = ROOT / "India_runs_data_and_ai_challenge" / "sample_candidates.json"


st.set_page_config(page_title="4Tech Pandas Redrob Ranker", layout="wide")
st.title("4Tech Pandas Redrob Ranker")
st.write("Small sandbox demo for the Redrob hackathon ranker.")
st.caption("This demo loads the sample candidate file and shows the top scored profiles.")

top_k = st.slider("Show top candidates", min_value=5, max_value=25, value=10, step=1)

if not SAMPLE_PATH.exists():
    st.error(f"Sample file not found: {SAMPLE_PATH}")
else:
    scored = []
    for candidate in load_candidates(SAMPLE_PATH):
        candidate_id = candidate.get("candidate_id")
        if not candidate_id:
            continue
        score, reasoning = score_candidate(candidate)
        profile = candidate.get("profile", {})
        scored.append(
            {
                "candidate_id": candidate_id,
                "score": round(score, 4),
                "headline": profile.get("headline", ""),
                "location": profile.get("location", ""),
                "reasoning": reasoning,
            }
        )

    scored.sort(key=lambda item: (-item["score"], item["candidate_id"]))
    st.dataframe(scored[:top_k], use_container_width=True, hide_index=True)
