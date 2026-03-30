# B担当 + ChromaDB担当 タスク一覧

## 担当ファイル

| ファイル | 担当 |
|---|---|
| `retrieval/vector_store.py` | ChromaDB検索（本来Aさん担当・兼任） |
| `retrieval/graph_search.py` | グラフ検索 + Context Builder |
| `data/graph/nodes.json` | グラフノード（確認済み） |
| `data/graph/edges.json` | グラフエッジ（確認済み） |

---

## タスク詳細

### Phase 1：グラフ構築（graph_search.py）

- [ ] `build_graph()` を実装する
  - `nodes.json` を読み込みノードを追加（`G.add_node(node["id"], **node)`）
  - `edges.json` を読み込みエッジを追加（`G.add_edge(..., relation=...)`）
  - 動作確認：`python retrieval/graph_search.py` でノード数12・エッジ数11が表示される

### Phase 2：ChromaDB検索（vector_store.py）

- [ ] `load_data()` を実装する
  - `external.json` / `internal.json` / `persons.json` を読み込む
  - 各エントリに `"source"` フィールドを付与して1つのリストにまとめる

- [ ] `build_collection()` を実装する
  - `client.get_or_create_collection()` でコレクション取得/作成
  - `model.encode()` でEmbeddingを生成
  - `collection.add()` でデータ投入

- [ ] `search(query, n=5)` を実装する
  - ChromaDBクライアントとモデルを初期化
  - クエリをベクトルに変換して `collection.query()` で検索
  - 結果を `{id, content, score, source}` 形式に整形して返す
  - 動作確認：`python retrieval/vector_store.py` で「ビルエネルギー管理」の検索結果5件が表示される

### Phase 3：隣接ノード取得（graph_search.py）

- [ ] `get_neighbors(node_ids, graph=None)` を実装する
  - `graph` が `None` の場合は `build_graph()` で構築
  - `G.neighbors()` で各ノードの隣接ノードを取得
  - 重複を除去して `{id, label, type, relation}` 形式のリストで返す
  - 動作確認：`tech_001` の隣接ノードが返る（person_001, person_004, market_medical, market_bems）

### Phase 4：Context Builder（graph_search.py） ※最重要

- [ ] `build_context(vector_results, graph=None)` を実装する
  - `vector_results` を `source`（external / internal / persons）ごとに仕分ける
  - 各グループのノードIDで `get_neighbors()` を呼び出す
  - 3軸のテキストを組み立てて返す

  ```python
  # 期待する出力形式（AさんのLLMとCさんのUIが依存する）
  {
    "external_context": "【市場情報】...\n【規制情報】...",
    "internal_context": "【保有技術】...\n【失敗事例】...",
    "org_context":      "【キーマン】..."
  }
  ```

---

## 実装順序

```
① build_graph()
② load_data() → build_collection() → search()
③ get_neighbors()
④ build_context()   ← AさんとCさんへの引き渡し物
```

---

## Day5 インターフェース合意（確認必須）

Week2開始前にチーム全員で以下を確認する。

**① ChromaDB検索結果の形式（→ Bさんが受け取る形式）**
```python
[
  {
    "id": "tech_001",
    "content": "高精度センサー製造技術...",
    "score": 0.91,
    "source": "internal"
  },
  ...
]
```

**② Context Builderの出力形式（→ Aさんに渡す形式）**
```python
{
  "external_context": "【市場情報】...\n【規制情報】...",
  "internal_context": "【保有技術】...\n【失敗事例】...",
  "org_context":      "【キーマン】..."
}
```

---

## 動作確認チェックリスト

- [ ] `python retrieval/graph_search.py` → ノード数12・エッジ数11が表示される
- [ ] `python retrieval/vector_store.py` → 検索結果5件が表示される
- [ ] `get_neighbors(["tech_001"])` → 隣接ノードが正しく返る
- [ ] `build_context(vector_results)` → 3軸テキストが返る
