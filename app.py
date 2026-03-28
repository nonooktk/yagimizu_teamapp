"""
app.py — Streamlit メインアプリ

担当: Cさん（UI担当）

【このファイルの役割】
- ユーザー入力を受け取り、検索・分析を実行し、結果を表示する
- 3軸評価パネル・提案タブ・承認者サマリー・PyVis グラフを表示する

【実行方法】
  streamlit run app.py
"""

import streamlit as st

# --- 他モジュールのインポート（実装後に有効化する）---
# from retrieval.vector_store import search
# from retrieval.graph_search import build_graph, build_context
# from llm.analyzer import analyze

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

st.divider()

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
        # TODO: 以下の処理を順番に実装する
        # 1. search(theme) でベクトル検索
        # 2. build_context() でContext生成
        # 3. analyze(theme, context) でStage1・Stage2を実行
        # 4. 結果を表示する

        # --- 仮データ（実装前の表示確認用）---
        stage1_dummy = {
            "external": {"score": "◎", "reason": "市場が急拡大中", "key_points": ["規制追い風", "需要急増"]},
            "internal": {"score": "○", "reason": "技術的な強みあり", "key_points": ["MEMS技術保有", "失敗条件解決済み"]},
            "org":      {"score": "○", "reason": "推進できるメンバーいる", "key_points": ["田中部長", "佐藤マネージャー"]}
        }
        stage2_dummy = {
            "proposals": [
                {
                    "title": "中小ビル向けSaaS型BEMSサービス",
                    "summary": "初期費用ゼロのSaaS型で中小ビルオーナーに提供する。既存の施工会社ネットワークで展開。",
                    "timing_score": "◎",
                    "timing_reason": "2024年省エネ法義務化により需要が強制的に創出",
                    "tech_fit_score": "○",
                    "tech_fit_reason": "MEMSセンサーとエッジAIで差別化可能",
                    "bottleneck": "ソフトウェア開発人材不足",
                    "bottleneck_solution": "SIerとのアライアンスで補完",
                    "next_actions": [
                        {"person": "佐藤 健", "action": "施工会社パイロット3社の選定"},
                        {"person": "田中 誠", "action": "センサー仕様の確定"}
                    ]
                }
            ],
            "approver_summary": "BEMS事業は全条件が解決済みであり、今が再参入の最適タイミングです。GO推奨。"
        }

        results = {"stage1": stage1_dummy, "stage2": stage2_dummy}

    # --- 3軸評価パネル ---
    st.subheader("3軸評価")
    col_ext, col_int, col_org = st.columns(3)

    with col_ext:
        st.metric("外部環境（今やるべきか）", results["stage1"]["external"]["score"])
        with st.expander("根拠を見る"):
            st.write(results["stage1"]["external"]["reason"])
            for point in results["stage1"]["external"]["key_points"]:
                st.write(f"・{point}")

    with col_int:
        st.metric("社内適合（自社でやれるか）", results["stage1"]["internal"]["score"])
        with st.expander("根拠を見る"):
            st.write(results["stage1"]["internal"]["reason"])
            for point in results["stage1"]["internal"]["key_points"]:
                st.write(f"・{point}")

    with col_org:
        st.metric("組織（誰とやるか）", results["stage1"]["org"]["score"])
        with st.expander("根拠を見る"):
            st.write(results["stage1"]["org"]["reason"])
            for point in results["stage1"]["org"]["key_points"]:
                st.write(f"・{point}")

    st.divider()

    # --- 事業提案タブ ---
    st.subheader("事業提案")
    proposals = results["stage2"]["proposals"]

    if proposals:
        tabs = st.tabs([f"案 {i+1}: {p['title']}" for i, p in enumerate(proposals)])
        for i, (tab, proposal) in enumerate(zip(tabs, proposals)):
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

    st.divider()

    # --- 承認者サマリー ---
    with st.expander("承認者向けサマリー（黒崎CDO向け）", expanded=True):
        st.info(results["stage2"]["approver_summary"])

    st.divider()

    # --- PyVis グラフ表示エリア（TODO）---
    st.subheader("関連ノードグラフ")
    st.info("TODO: PyVis グラフをここに表示する。graph_search.py の実装後に追加する。")
    # TODO: PyVis で関連ノードをハイライトしたグラフを生成し、
    #        components.html() で Streamlit に埋め込む

elif run_button and not theme:
    st.warning("テーマを入力してください。")
