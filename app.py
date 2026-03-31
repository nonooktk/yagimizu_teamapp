"""
app.py — Streamlit メインアプリ

担当: Cさん（UI担当）

【このファイルの役割】
- ユーザー入力を受け取り、検索・分析を実行し、結果を表示する
- 3軸評価パネル・提案タブ・承認者サマリー・PyVis グラフを表示する

【実行方法】
  streamlit run app.py
"""

import os
import tempfile

import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network

from retrieval.vector_store import search
from retrieval.graph_search import build_graph, build_context, get_neighbors

# .env が未設定でもクラッシュせずエラーを画面表示する
try:
    from llm.analyzer import analyze
    ANALYZER_AVAILABLE = True
except ValueError as e:
    ANALYZER_AVAILABLE = False
    ANALYZER_ERROR = str(e)

# ============================================================
# ページ設定
# ============================================================
st.set_page_config(
    page_title="PROJECT ZERO — 新規事業判断支援",
    page_icon="🔍",
    layout="wide"
)

st.title("PROJECT ZERO")
st.caption("新規事業判断支援システム — 「この提案、うちでやれるか？今やるべきか？」")

if not ANALYZER_AVAILABLE:
    st.error(f"設定エラー: {ANALYZER_ERROR}")
    st.info(".env ファイルに OPENAI_API_KEY を設定してください。")
    st.stop()

st.divider()

# ============================================================
# グラフをキャッシュ（起動時に1回だけ構築）
# ============================================================
@st.cache_resource
def get_graph():
    return build_graph()


# ============================================================
# PyVis グラフ描画
# ============================================================
def render_graph(highlighted_ids: set):
    G = get_graph()
    net = Network(height="500px", width="100%", bgcolor="#1a1a2e", font_color="white")

    type_colors = {
        "technology":   "#4CAF50",
        "person":       "#2196F3",
        "market":       "#FF9800",
        "past_project": "#9C27B0",
    }

    for node_id, attrs in G.nodes(data=True):
        is_highlighted = node_id in highlighted_ids
        base_color = type_colors.get(attrs.get("type", ""), "#AAAAAA")
        net.add_node(
            node_id,
            label=attrs.get("label", node_id),
            color={"background": "#FFD700" if is_highlighted else base_color,
                   "border":     "#FF4500" if is_highlighted else base_color},
            size=25 if is_highlighted else 15,
            title=f"{attrs.get('label', node_id)} ({attrs.get('type', '')})",
        )

    for src, tgt, attrs in G.edges(data=True):
        net.add_edge(src, tgt, title=attrs.get("relation", ""), color="#555555")

    # HTML を生成して Streamlit に埋め込む
    html = net.generate_html()
    components.html(html, height=520)


# ============================================================
# 入力エリア
# ============================================================
theme = st.text_input(
    "検討テーマを入力してください",
    placeholder="例：ビルエネルギー管理で新事業を考えたい"
)
run_button = st.button("分析スタート", type="primary")

# ============================================================
# 分析の実行と結果の表示
# ============================================================
if run_button and theme:
    with st.spinner("分析中..."):
        G = get_graph()
        vector_results = search(theme, n=5)
        context = build_context(vector_results, graph=G)
        results = analyze(theme, context, search_results=vector_results)

    stage1 = results["stage1"]
    stage2 = results["stage2"]

    # --- 3軸評価パネル ---
    st.subheader("3軸評価")
    col_ext, col_int, col_org = st.columns(3)

    with col_ext:
        st.metric("外部環境（今やるべきか）", stage1["external"]["score"])
        with st.expander("根拠を見る"):
            st.write(stage1["external"]["reason"])
            for point in stage1["external"].get("key_points", []):
                st.write(f"・{point}")

    with col_int:
        st.metric("社内適合（自社でやれるか）", stage1["internal"]["score"])
        with st.expander("根拠を見る"):
            st.write(stage1["internal"]["reason"])
            for point in stage1["internal"].get("key_points", []):
                st.write(f"・{point}")

    with col_org:
        st.metric("組織（誰とやるか）", stage1["org"]["score"])
        with st.expander("根拠を見る"):
            st.write(stage1["org"]["reason"])
            for point in stage1["org"].get("key_points", []):
                st.write(f"・{point}")

    st.divider()

    # --- 事業提案タブ ---
    st.subheader("事業提案")
    proposals = stage2.get("proposals", [])

    if proposals:
        tabs = st.tabs([f"案 {i+1}: {p['title']}" for i, p in enumerate(proposals)])
        for tab, proposal in zip(tabs, proposals):
            with tab:
                st.write(proposal["summary"])
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("タイミング", proposal["timing_score"])
                    st.caption(proposal["timing_reason"])
                with col2:
                    st.metric("技術適合性", proposal["tech_fit_score"])
                    st.caption(proposal["tech_fit_reason"])

                st.warning(f"**ボトルネック**: {proposal['bottleneck']}")
                st.success(f"**解決策**: {proposal['bottleneck_solution']}")

                st.subheader("次のアクション")
                for action in proposal["next_actions"]:
                    st.write(f"- **{action['person']}**: {action['action']}")

    # --- 3C分析（Customer / Competitor / Company）---
    tier2 = stage2.get("tier2")
    if tier2:
        st.divider()
        st.subheader("3C分析")
        col_cust, col_comp, col_co = st.columns(3)

        with col_cust:
            with st.expander("Customer（顧客・市場）", expanded=True):
                st.write(tier2["customer"]["summary"])
                for insight in tier2["customer"].get("key_insights", []):
                    st.write(f"・{insight}")

        with col_comp:
            with st.expander("Competitor（競合）", expanded=True):
                st.write(tier2["competitor"]["summary"])
                st.write(f"**空白地帯**: {tier2['competitor']['white_space']}")
                st.write(f"**自社優位性**: {tier2['competitor']['our_advantage']}")
                for insight in tier2["competitor"].get("key_insights", []):
                    st.write(f"・{insight}")

        with col_co:
            company = tier2.get("company")
            if company:
                with st.expander("Company（自社）", expanded=True):
                    st.write(company["summary"])
                    assets = company.get("reusable_assets", [])
                    if assets:
                        st.write("**活用可能資産**")
                        for asset in assets:
                            st.write(f"・{asset}")
                    persons = company.get("key_persons", [])
                    if persons:
                        st.write("**キーパーソン**")
                        for p in persons:
                            st.write(f"・**{p['name']}**: {p['role']}")
                    if company.get("lessons_learned"):
                        st.write(f"**過去の学び**: {company['lessons_learned']}")

    st.divider()

    # --- 承認者サマリー ---
    with st.expander("承認者向けサマリー（黒崎CDO向け）", expanded=True):
        st.info(stage2["approver_summary"])

    st.divider()

    # --- PyVis グラフ ---
    st.subheader("関連ノードグラフ")
    result_ids = {r["id"] for r in vector_results}
    neighbor_ids = {nb["id"] for nb in get_neighbors(list(result_ids), graph=G)}
    highlighted_ids = result_ids | neighbor_ids
    render_graph(highlighted_ids)
    st.caption("🟡 ハイライト: 検索結果・関連ノード　🟢 技術　🔵 人物　🟠 市場　🟣 過去PJ")

elif run_button and not theme:
    st.warning("テーマを入力してください。")
