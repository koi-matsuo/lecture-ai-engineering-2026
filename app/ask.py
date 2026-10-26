"""第1回: 素のLLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする
    uv run python -m app.ask --chat     # 会話履歴を保って続けて質問する

ツールを持たない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse
import time

from google import genai
from google.genai import errors
from google.genai.types import GenerateContentResponse

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def ask(question: str) -> str:
    client = genai.Client(api_key=get_api_key())
    started_at = time.perf_counter()
    response = client.models.generate_content(model=MODEL, contents=question)

    print_response_time(started_at)
    print_usage(response)
    return response.text


def chat() -> None:
    client = genai.Client(api_key=get_api_key())
    conversation = client.chats.create(model=MODEL)
    print("会話を開始します。終了するには :q または exit を入力してください。")

    try:
        while True:
            question = input("あなた> ").strip()
            if question in {":q", "exit"}:
                break
            if not question:
                continue

            started_at = time.perf_counter()
            response = conversation.send_message(question)
            print_response_time(started_at)
            print_usage(response)
            print(f"回答> {response.text}\n")
    except EOFError:
        pass


def print_usage(response: GenerateContentResponse) -> None:
    usage = response.usage_metadata
    if usage is None:
        print("[トークン数] 利用状況を取得できませんでした")
    else:
        print(
            f"[トークン数] 入力: {usage.prompt_token_count}, "
            f"出力: {usage.candidates_token_count}"
        )


def print_response_time(started_at: float) -> None:
    elapsed = time.perf_counter() - started_at
    print(f"[応答時間] {elapsed:.2f}秒")


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?")
    parser.add_argument(
        "--chat",
        action="store_true",
        help="会話履歴を保って続けて質問する",
    )
    args = parser.parse_args()

    if args.chat and args.question is not None:
        parser.error("質問文は --chat と同時に指定できません")

    print(f"[model] {MODEL}")
    try:
        if args.chat:
            chat()
        else:
            question = args.question or DEFAULT_QUESTION
            print(f"[質問] {question}\n")
            print(ask(question))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
