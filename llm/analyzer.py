"""
analyzer.py — GPT-4o-mini を使った Stage1・Stage2 分析モジュール

担当: Aさん（データ＆AI担当）

【このファイルの役割】
- Stage1: 3軸（外部・内部・組織）を個別に分析し、◎○△×スコアを生成する
- Stage2: Stage1の結果を統合し、事業案3つ＋承認者サマリーを生成する
"""

import json
from concurrent.futures import ThreadPoolExecutor
from openai import OpenAI
from config import OPENAI_API_KEY
from llm.prompts import (
    STAGE1_SYSTEM_PROMPT,
    STAGE1_USER_PROMPT_TEMPLATE,
    STAGE2_SYSTEM_PROMPT,
    STAGE2_USER_PROMPT_TEMPLATE,
    AXIS_NAMES,
)

client = OpenAI(api_key=OPENAI_API_KEY)
MODEL = "gpt-4o-mini"

# 軸名とcontextキーのマッピング
AXIS_CONTEXT_KEYS = {
    "external": "external_context",
    "internal": "internal_context",
    "org":      "org_context",
}


def run_stage1(theme: str, context: dict) -> dict:
    """
    Stage1: 3軸を個別に分析してスコアを生成する。

    Args:
        theme (str): ユーザーが入力したテーマ
        context (dict): build_context() が返す3軸のコンテキスト
                        {"external_context": "...", "internal_context": "...", "org_context": "..."}

    Returns:
        dict: 3軸のスコアと根拠
        例:
        {
          "external": {"score": "◎", "reason": "...", "key_points": [...]},
          "internal": {"score": "○", "reason": "...", "key_points": [...]},
          "org":      {"score": "△", "reason": "...", "key_points": [...]}
        }
    """
    def call_gpt(axis: str) -> tuple[str, dict]:
        prompt = STAGE1_USER_PROMPT_TEMPLATE.format(
            theme=theme,
            axis_name=AXIS_NAMES[axis],
            context=context.get(AXIS_CONTEXT_KEYS[axis], "（情報なし）"),
        )
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": STAGE1_SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
            response_format={"type": "json_object"},
        )
        return axis, json.loads(response.choices[0].message.content)

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(call_gpt, axis) for axis in AXIS_CONTEXT_KEYS]
        results = dict(f.result() for f in futures)

    return results


def run_stage2(theme: str, stage1_results: dict, context: dict) -> dict:
    """
    Stage2: Stage1の結果を統合し、事業案3つ＋承認者サマリーを生成する。

    Args:
        theme (str): ユーザーが入力したテーマ
        stage1_results (dict): run_stage1() の返り値
        context (dict): build_context() が返す3軸のコンテキスト

    Returns:
        dict: 事業案3つと承認者サマリー
        例:
        {
          "proposals": [
            {
              "title": "...",
              "summary": "...",
              "timing_score": "◎",
              "timing_reason": "...",
              "tech_fit_score": "○",
              "tech_fit_reason": "...",
              "bottleneck": "...",
              "bottleneck_solution": "...",
              "next_actions": [{"person": "...", "action": "..."}]
            }
          ],
          "approver_summary": "..."
        }
    """
    external = stage1_results.get("external", {})
    internal = stage1_results.get("internal", {})
    org      = stage1_results.get("org", {})

    full_context = "\n\n".join([
        context.get("external_context", ""),
        context.get("internal_context", ""),
        context.get("org_context", ""),
    ])

    prompt = STAGE2_USER_PROMPT_TEMPLATE.format(
        theme=theme,
        external_score=external.get("score", "－"),
        external_reason=external.get("reason", ""),
        external_key_points="、".join(external.get("key_points", [])),
        internal_score=internal.get("score", "－"),
        internal_reason=internal.get("reason", ""),
        internal_key_points="、".join(internal.get("key_points", [])),
        org_score=org.get("score", "－"),
        org_reason=org.get("reason", ""),
        org_key_points="、".join(org.get("key_points", [])),
        full_context=full_context,
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": STAGE2_SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ],
        response_format={"type": "json_object"},
    )

    return json.loads(response.choices[0].message.content)


def analyze(theme: str, context: dict) -> dict:
    """
    Stage1 と Stage2 を順番に実行し、最終結果を返す。
    app.py から呼び出すメイン関数。

    Args:
        theme (str): ユーザーが入力したテーマ
        context (dict): build_context() が返す3軸のコンテキスト

    Returns:
        dict: {
          "stage1": Stage1の結果,
          "stage2": Stage2の結果
        }
    """
    stage1 = run_stage1(theme, context)
    stage2 = run_stage2(theme, stage1, context)
    return {"stage1": stage1, "stage2": stage2}
