"""
graph_search.py — NetworkX によるグラフ検索モジュール

担当: Bさん（グラフ＆ロジック担当）

【このファイルの役割】
- nodes.json / edges.json を読み込んでNetworkXグラフを構築する
- ノードIDのリストを受け取り、depth=1 で隣接ノードを返す
- ChromaDB検索結果と組み合わせて、3軸のコンテキストテキストを生成する（Context Builder）

【使うライブラリ】
- networkx: グラフ構造の構築と検索
"""

import json
import os
import networkx as nx

# --- 定数 ---
GRAPH_DIR = os.path.join(os.path.dirname(__file__), "../data/graph")
DATA_DIR = os.path.join(os.path.dirname(__file__), "../data")


def build_graph() -> nx.Graph:
    """
    nodes.json と edges.json を読み込み、NetworkX グラフを構築して返す。

    Returns:
        nx.Graph: 構築済みのグラフ
    """
    # TODO: nodes.json を読み込み、グラフにノードを追加する
    #        ヒント: G.add_node(node["id"], **node) で属性ごと追加できる
    # TODO: edges.json を読み込み、グラフにエッジを追加する
    #        ヒント: G.add_edge(edge["source"], edge["target"], relation=edge["relation"])
    G = nx.Graph()
    return G


def get_neighbors(node_ids: list[str], graph: nx.Graph = None) -> list[dict]:
    """
    ノードIDのリストを受け取り、depth=1 で隣接する全ノードの情報を返す。

    Args:
        node_ids (list[str]): 起点となるノードIDのリスト
        graph (nx.Graph): グラフ（省略時は自動構築）

    Returns:
        list[dict]: 隣接ノードの情報リスト
        例:
        [
          {"id": "person_001", "label": "田中 誠", "type": "person", "relation": "担当できる"},
          ...
        ]
    """
    # TODO: graph が None の場合は build_graph() で構築する
    # TODO: node_ids の各ノードについて G.neighbors() で隣接ノードを取得する
    # TODO: 重複を除去して返す
    return []


def build_context(vector_results: list[dict], graph: nx.Graph = None) -> dict:
    """
    ChromaDB の検索結果を受け取り、グラフ検索で拡張して3軸のコンテキストを返す。
    （Context Builder）

    Args:
        vector_results (list[dict]): vector_store.search() の返り値
        graph (nx.Graph): グラフ（省略時は自動構築）

    Returns:
        dict: 3軸のコンテキストテキスト
        例:
        {
          "external_context": "【市場情報】...\n【規制情報】...",
          "internal_context": "【保有技術】...\n【失敗事例】...",
          "org_context":      "【キーマン】..."
        }
    """
    # TODO: vector_results を source（external/internal/persons）ごとに仕分ける
    # TODO: 各グループのノードIDをもとに get_neighbors() で関連ノードを取得する
    # TODO: 各軸のテキストを組み立てて返す
    return {
        "external_context": "",
        "internal_context": "",
        "org_context": ""
    }


if __name__ == "__main__":
    # 動作確認用: このファイルを直接実行してテストする
    # 実行: python retrieval/graph_search.py
    G = build_graph()
    print(f"ノード数: {G.number_of_nodes()}, エッジ数: {G.number_of_edges()}")

    neighbors = get_neighbors(["tech_001"])
    print("tech_001 の隣接ノード:", neighbors)
