import os

# OpenAI APIキーを環境変数から読み込む
# 事前に環境変数 OPENAI_API_KEY をセットしておくこと
# 例: export OPENAI_API_KEY="sk-..."
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

if not OPENAI_API_KEY:
    raise ValueError("環境変数 OPENAI_API_KEY が設定されていません。")
