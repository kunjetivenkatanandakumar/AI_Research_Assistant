from __future__ import annotations

import argparse

from dotenv import load_dotenv

from research_assistant.graph import build_research_graph


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Generate a PDF research report from a topic.")
    parser.add_argument("topic", help="Research topic or question.")
    parser.add_argument("--output", help="Path for the generated PDF.")
    parser.add_argument("--offline-demo", action="store_true", help="Run without OpenAI or Tavily API calls.")
    args = parser.parse_args()

    graph = build_research_graph()
    result = graph.invoke(
        {
            "topic": args.topic,
            "output_path": args.output,
            "offline_demo": args.offline_demo,
        }
    )
    print(f"Generated report: {result['output_path']}")


if __name__ == "__main__":
    main()

