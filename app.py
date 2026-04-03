"""
app.py — Streamlit メインアプリ (UX改修版・3C縦積みレイアウト ＋ PDF添付機能 ＋ UIプロフェッショナル化 ＋ 堅牢化)

担当: Cさん（UI担当）/ PMO監修
"""
import base64
import os
import tempfile

import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network

# ============================================================
# 【モックアップ用インポート】
# ※実際の環境に合わせてパスやモジュール名は適宜修正してください
# ============================================================
from retrieval.vector_store import search
from retrieval.graph_search import build_graph, build_context, get_neighbors

# .env が未設定でもクラッシュせずエラーを画面表示する
try:
    from llm.analyzer import analyze

    ANALYZER_AVAILABLE = True
except ValueError as e:
    ANALYZER_AVAILABLE = False
    ANALYZER_ERROR = str(e)
except ImportError:
    # 開発環境でモジュールがない場合のモック処理用（必要に応じて）
    ANALYZER_AVAILABLE = False
    ANALYZER_ERROR = "analyzerモジュールが見つかりません。"


# ============================================================
# CSS
# ============================================================
CUSTOM_CSS = """
<style>
/* ===== 全体背景 ===== */
html, body, [data-testid="stAppViewContainer"], .stApp {
  background: #131B4A !important;
  color: #FFFFFF;
}

/* ===== メインテキスト（紺背景側） ===== */
h1, h2, h3, h4, h5, h6,
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] span,
[data-testid="stWidgetLabel"] {
  color: #FFFFFF !important;
}

/* 明示的に使い分けたいクラス */
.normal-text {
  color: #FFFFFF !important;
}

.sub-text {
  color: #000000 !important;
}

/* ===== 入力欄（紺背景上） ===== */
input, textarea {
  background-color: #1C245A !important;
  color: #FFFFFF !important;
}

input::placeholder,
textarea::placeholder {
  color: #C9D1FF !important;
}

/* ===== file_uploader 本体 ===== */
[data-testid="stFileUploader"] {
  color: #FFFFFF !important;
}

/* アップロードエリアの白背景 */
[data-testid="stFileUploaderDropzone"] {
  background: #F3F4F6 !important;
  border: 1px solid #D1D5DB !important;
}

/* 白背景側の文字を黒系にする */
[data-testid="stFileUploaderDropzone"] * {
  color: #111827 !important;
}

/* Browse files ボタン相当 */
[data-testid="stFileUploaderDropzone"] button,
[data-testid="stBaseButton-secondary"] {
  background: #FFFFFF !important;
  color: #111827 !important;
  border: 1px solid #C7C9D1 !important;
}

/* ボタン */
.stButton > button,
[data-testid="stFormSubmitButton"] button {
  background-color: #4CAF50 !important;
  color: #FFFFFF !important;
  border-radius: 8px;
  border: none;
}

/* 成功/注意メッセージ視認性 */
[data-testid="stAlert"] {
  border-radius: 10px;
}

/* ===== ヘッダー右画像 ===== */
.hero-wrap {
  position: relative;
  width: 100%;
  max-width: 520px;
  margin: 0auto;
}

.hero-image {
  width: 120%;
  height: 260px;
  object-fit: cover;
}

.hero-overlay {
  position: absolute;
  left: 24px;
  bottom: 20px;
  color: white !important;
  font-size: 2rem;
  font-weight: 800;
  font-style: italic;
  letter-spacing: 0.08em;
  text-shadow: 0 3px 12px rgba(0,0,0,0.55);
  line-height: 1.2;
}

.hero-sub {
  position: absolute;
  left: 24px;
  top: 20px;
  color: rgba(255,255,255,0.92) !important;
  font-size: 0.95rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  text-shadow: 0 2px 8px rgba(0,0,0,0.45);
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ============================================================
# ヘッダー
# ============================================================

def get_image_base64(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

st.set_page_config(
    page_title="PROJECT ZERO — 新規事業判断支援",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

#banner_path = "factory.png"  # ここを使いたい画像ファイル名にする
#banner_b64 = get_image_base64(banner_path)

#st.markdown(
#        f"""
#        <div class="hero-wrap">
#            <img src="data:image/png;base64,{banner_b64}" class="hero-image">
#            <h1 class="hero-overlay">Technozeron</h1>
#        </div>
#        """,
#        unsafe_allow_html=True,
#   )

col_left, col_center, col_right = st.columns([1,3,1])

with col_center:
    st.image("factory.png", use_container_width=True)

#col_left, col_right = st.columns([1, 2])

#with col_left:
#    st.markdown("<h1 style='margin-bottom:0.2rem;'>PROJECT ZERO</h1>", unsafe_allow_html=True)
#    st.markdown('<div class="hero-sub">新規事業判断支援ダッシュボード —「この提案、うちでやれるか？今やるべきか？」</div>',
#    unsafe_allow_html=True
#    )
#with col_right:
#    st.markdown(
#        f"""
#        <div class="hero-wrap">
#            <img src="data:image/png;base64,{banner_b64}" class="hero-image">
#            <h1 class="hero-overlay">Technozeron</h1>
#        </div>
#        """,
#        unsafe_allow_html=True,
#    )


if not ANALYZER_AVAILABLE:
    st.error(f"設定エラー: {ANALYZER_ERROR}")
    st.info(
        ".env ファイルに OPENAI_API_KEY を設定するか、モジュールパスを確認してください。"
    )
    st.stop()

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
        "technology": "#4CAF50",
        "person": "#2196F3",
        "market": "#FF9800",
        "past_project": "#9C27B0",
    }

    for node_id, attrs in G.nodes(data=True):
        is_highlighted = node_id in highlighted_ids
        base_color = type_colors.get(attrs.get("type", ""), "#AAAAAA")
        net.add_node(
            node_id,
            label=attrs.get("label", node_id),
            color={
                "background": "#FFD700" if is_highlighted else base_color,
                "border": "#FF4500" if is_highlighted else base_color,
            },
            size=25 if is_highlighted else 15,
            title=f"{attrs.get('label', node_id)} ({attrs.get('type', '')})",
        )

    for src, tgt, attrs in G.edges(data=True):
        net.add_edge(src, tgt, title=attrs.get("relation", ""), color="#555555")

    html = net.generate_html()
    components.html(html, height=520)


# ============================================================
# 入力エリア（ガイド付きフォームでプロンプト品質を担保）
# ============================================================
st.markdown("### 💡 ビジネスアイデアの入力")
with st.form("idea_form"):

      # --- PDFアップロード機能 ---
    st.markdown(
        '<p class="normal-text"><strong>📁 既存の企画書・関連資料をアップロード（任意）</strong></p>',
        unsafe_allow_html=True,
    )
    uploaded_file = st.file_uploader(
        "PDFファイルを添付", type=["pdf"], label_visibility="collapsed"
    )


    # ファイルがアップロードされた場合のUIフィードバック（モック）
    if uploaded_file is not None:
        st.success(
            f"📄 『{uploaded_file.name}』 を読み込みました。AIが文脈として考慮します。"
        )
    st.markdown("<br>", unsafe_allow_html=True)
    # ---------------------------------

    col_input1, col_input2 = st.columns(2)
    with col_input1:
        target_market = st.text_input(
            "ターゲット市場 / 想定顧客",
            placeholder="例：欧州の大規模農業法人",
        )
    with col_input2:
        assets = st.text_input(
            "活用したい自社アセット・コア技術",
            placeholder="例：100%植物由来ポリマー「Green Planet」",
        )

    idea_detail = st.text_area(
        "提供価値・事業アイデアの詳細",
        placeholder="例：環境規制強化を背景に、農業用マルチフィルムとして展開。haあたり300ユーロの廃棄コストを削減し...",
    )

    run_button = st.form_submit_button("投資判断AIによる分析スタート", type="primary")

# プロンプトの合成
theme = f"【想定顧客/市場】{target_market}\n【活用アセット】{assets}\n【アイデア概要】{idea_detail}"

# ============================================================
# 分析の実行と結果の表示
# ============================================================
if run_button:
    if not idea_detail:
        st.warning("⚠️ 「提供価値・事業アイデアの詳細」は必ず入力してください。")
        st.stop()

    # --- 待機時間のUX向上（実況中継風ステータス） ---
    with st.status("🧠 AIが多角的に分析・評価中...", expanded=True) as status:

        # PDFがアップロードされていた場合の実況メッセージを追加
        if uploaded_file is not None:
            st.write("📑 添付されたPDF資料の内容を解析・抽出中...")

        st.write("🔍 社内データ・過去の失敗プロジェクトを検索中...")
        G = get_graph()
        vector_results = search(theme, n=5)

        st.write("📊 外部環境・社内資産・組織体制の文脈を構築中...")
        context = build_context(vector_results, graph=G)

        st.write("⚖️ 投資判断と3C分析を生成中（数秒かかります）...")
        results = analyze(theme, context, search_results=vector_results)

        status.update(label="✅ 分析完了！", state="complete", expanded=False)

    # 辞書キー欠損エラー回避のための安全な取得
    stage1 = results.get("stage1", {})
    stage2 = results.get("stage2", {})

    st.divider()

    # --- 結論ファースト：ダッシュボードトップ ---
    st.header("🎯 エグゼクティブ・サマリー（事業化 Go/No-Go 判定）")
    st.caption(
        "※本AI判定は、市場性・技術適合性・組織体制の3軸に基づき、初期投資の妥当性を評価したものです。"
    )

    # サマリー文章の切り出し
    summary_text = stage2.get(
        "approver_summary", "サマリー情報が生成されませんでした。"
    )
    st.info(summary_text, icon="📢")

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("3軸評価と根拠詳細")

    # --- 縦積みカード型レイアウト ---
    ext_data = stage1.get("external", {})
    int_data = stage1.get("internal", {})
    org_data = stage1.get("org", {})

    # 【外部環境】
    with st.container():
        c_score, c_reason = st.columns([1, 4])
        with c_score:
            st.metric("🌍 外部環境", ext_data.get("score", "N/A"))
        with c_reason:
            st.markdown("**💡 評価根拠**")
            st.write(ext_data.get("reason", "評価根拠がありません。"))
    st.divider()

    # 【社内適合】
    with st.container():
        c_score, c_reason = st.columns([1, 4])
        with c_score:
            st.metric("🏢 社内適合", int_data.get("score", "N/A"))
        with c_reason:
            st.markdown("**💡 評価根拠**")
            st.write(int_data.get("reason", "評価根拠がありません。"))
    st.divider()

    # 【組織体制】
    with st.container():
        c_score, c_reason = st.columns([1, 4])
        with c_score:
            st.metric("🤝 組織体制", org_data.get("score", "N/A"))
        with c_reason:
            st.markdown("**💡 評価根拠**")
            st.write(org_data.get("reason", "評価根拠がありません。"))

    st.markdown("<br>", unsafe_allow_html=True)

    # --- 情報の階層化：残りの情報をタブでスッキリ見せる ---
    tab_proposal, tab_3c, tab_graph = st.tabs(
        ["💡 事業提案・アクション", "📊 3C分析", "🌐 関連ノードグラフ"]
    )

    # 【タブ1】事業提案・アクション
    with tab_proposal:
        st.subheader("AIからのピボット提案")
        proposals = stage2.get("proposals", [])
        if proposals:
            for i, proposal in enumerate(proposals):
                # タイトルの切り出し
                p_title = proposal.get("title", "無題の提案")

                with st.expander(f"提案 {i+1}： {p_title}", expanded=(i == 0)):
                    st.write(proposal.get("summary", ""))

                    c1, c2 = st.columns(2)
                    with c1:
                        st.metric("タイミング評価", proposal.get("timing_score", "-"))
                        st.caption(proposal.get("timing_reason", ""))
                    with c2:
                        st.metric("技術適合性", proposal.get("tech_fit_score", "-"))
                        st.caption(proposal.get("tech_fit_reason", ""))

                    # 文字列事故防止のため、変数を切り出してから展開
                    bottleneck_text = proposal.get("bottleneck", "特になし")
                    solution_text = proposal.get("bottleneck_solution", "特になし")

                    st.warning(f"**最大のボトルネック**: {bottleneck_text}")
                    st.success(f"**解決策**: {solution_text}")

                    st.markdown("#### 🏃 次の具体的なアクション")
                    next_actions = proposal.get("next_actions", [])
                    if next_actions:
                        for action in next_actions:
                            person = action.get("person", "担当未定")
                            task = action.get("action", "タスク内容未定義")
                            st.markdown(f"- **{person}**: {task}")
                    else:
                        st.write("現在提示できる具体的なアクションはありません。")
        else:
            st.write("ピボット提案はありません。")

    # 【タブ2】3C分析
    with tab_3c:
        tier2 = stage2.get("tier2", {})
        if tier2:
            st.markdown("<br>", unsafe_allow_html=True)

            cust_data = tier2.get("customer", {})
            comp_data = tier2.get("competitor", {})
            co_data = tier2.get("company", {})

            # Customer
            with st.container():
                c_title, c_content = st.columns([1, 4])
                with c_title:
                    st.markdown("### 🧑‍🤝‍🧑 Customer")
                    st.caption("市場・顧客")
                with c_content:
                    st.write(cust_data.get("summary", "情報なし"))
                    for insight in cust_data.get("key_insights", []):
                        st.write(f"・{insight}")
            st.divider()

            # Competitor
            with st.container():
                c_title, c_content = st.columns([1, 4])
                with c_title:
                    st.markdown("### ⚔️ Competitor")
                    st.caption("競合環境")
                with c_content:
                    st.write(comp_data.get("summary", "情報なし"))

                    # 変数切り出し
                    white_space = comp_data.get("white_space", "不明")
                    our_adv = comp_data.get("our_advantage", "不明")

                    st.write(f"**空白地帯**: {white_space}")
                    st.write(f"**自社優位性**: {our_adv}")

                    for insight in comp_data.get("key_insights", []):
                        st.write(f"・{insight}")
            st.divider()

            # Company
            with st.container():
                c_title, c_content = st.columns([1, 4])
                with c_title:
                    st.markdown("### 🏢 Company")
                    st.caption("自社状況")
                with c_content:
                    if co_data:
                        st.write(co_data.get("summary", "情報なし"))

                        reusable = co_data.get("reusable_assets", [])
                        if reusable:
                            st.markdown("**武器になる資産**")
                            for asset in reusable:
                                st.write(f"・{asset}")

                        key_persons = co_data.get("key_persons", [])
                        if key_persons:
                            st.markdown("**キーパーソン**")
                            for p in key_persons:
                                p_name = p.get("name", "氏名不明")
                                p_role = p.get("role", "役職不明")
                                st.write(f"・**{p_name}**: {p_role}")

                        lessons = co_data.get("lessons_learned", "")
                        if lessons:
                            st.write(f"**過去の学び**: {lessons}")

    # 【タブ3】PyVis グラフ
    with tab_graph:
        st.subheader("関連情報ネットワーク")
        if vector_results:
            result_ids = {r.get("id") for r in vector_results if "id" in r}
            try:
                neighbor_ids = {
                    nb.get("id")
                    for nb in get_neighbors(list(result_ids), graph=G)
                    if "id" in nb
                }
            except Exception:
                neighbor_ids = set()

            highlighted_ids = result_ids | neighbor_ids
            render_graph(highlighted_ids)
            st.caption("🟡 検索ヒット　🟢 技術　🔵 人物　🟠 市場　🟣 過去PJ")
        else:
            st.warning(
                "検索結果が取得できませんでした。検索キーワード（ターゲット市場やアセット）を変更して、再度お試しください。"
            )
