"""
vector_store.py — ChromaDB によるベクトル検索モジュール

担当: Aさん（データ＆AI担当）

【このファイルの役割】
- data/ 以下の3つのJSONファイルをChromaDBに投入する
- クエリ文字列を受け取り、意味的に近いデータを上位N件返す

【使うライブラリ】
- chromadb: ベクトルデータベース
- sentence-transformers: テキストをベクトルに変換するEmbeddingモデル
"""

import json
import os
import chromadb
from sentence_transformers import SentenceTransformer

# --- 定数 ---
DATA_DIR = os.path.join(os.path.dirname(__file__), "../data")
COLLECTION_NAME = "project_zero"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # 軽量で高速な多言語対応モデル


def load_data() -> list[dict]:
    """
    3つのJSONファイルを読み込み、1つのリストにまとめて返す。

    Returns:
        list[dict]: 全データのリスト。各データに "source" フィールドを付与する。
        例:
        [
          {"id": "ext_001", "content": "...", "source": "external"},
          {"id": "tech_001", "content": "...", "source": "internal"},
          ...
        ]
    """
    # TODO: external.json, internal.json, persons.json を読み込む
    # ヒント: json.load() を使い、各エントリに source フィールドを追加する
    all_data = []
    return all_data


def build_collection(client: chromadb.Client, model: SentenceTransformer) -> chromadb.Collection:
    """
    ChromaDBにデータを投入してコレクションを作成・返す。
    既にコレクションが存在する場合はそのまま返す。

    Args:
        client: ChromaDB クライアント
        model: Embeddingモデル

    Returns:
        chromadb.Collection: データが投入されたコレクション
    """
    # TODO: client.get_or_create_collection() でコレクションを取得/作成する
    # TODO: load_data() でデータを取得し、model.encode() でEmbeddingを生成する
    # TODO: collection.add() でデータを投入する
    pass


def search(query: str, n: int = 5) -> list[dict]:
    """
    クエリ文字列を受け取り、意味的に近いデータを上位N件返す。

    Args:
        query (str): 検索クエリ文字列
        n (int): 返す件数（デフォルト5）

    Returns:
        list[dict]: 検索結果のリスト
        例:
        [
          {
            "id": "tech_001",
            "content": "高精度センサー製造技術...",
            "score": 0.91,
            "source": "internal"
          },
          ...
        ]
    """
    # TODO: ChromaDBクライアントとモデルを初期化する
    # TODO: build_collection() でコレクションを取得する
    # TODO: クエリをベクトルに変換し、collection.query() で検索する
    # TODO: 結果を上記フォーマットに整形して返す
    return []


if __name__ == "__main__":
    # 動作確認用: このファイルを直接実行してテストする
    # 実行: python retrieval/vector_store.py
    results = search("ビルエネルギー管理")
    for r in results:
        print(r)
