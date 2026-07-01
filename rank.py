import argparse
import csv
from pathlib import Path

from src.loader import load_jsonl, load_docx_text
from src.jd_parser import build_hiring_blueprint
from src.ranker import rank_candidates
from src.fast_ranker import fast_rank_candidates_from_jsonl
from src.reasoning import generate_reasoning


def write_submission(results, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    top_100 = results[:100]

    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])

        for rank, result in enumerate(top_100, start=1):
            candidate = result["candidate"]
            reasoning = generate_reasoning(candidate, result)

            writer.writerow([
                result["candidate_id"],
                rank,
                f"{result['score']:.6f}",
                reasoning,
            ])


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--candidates",
        default="data/candidates.jsonl",
        help="Path to candidates.jsonl"
    )

    parser.add_argument(
        "--jd",
        default="data/job_description.docx",
        help="Path to job_description.docx"
    )

    parser.add_argument(
        "--out",
        default="outputs/submission.csv",
        help="Output CSV path"
    )

    parser.add_argument(
        "--mode",
        choices=["fast", "full"],
        default="fast",
        help="fast = two-stage ranker, full = full HireFormer on all candidates"
    )

    parser.add_argument(
        "--shortlist-size",
        type=int,
        default=5000,
        help="Number of candidates passed from Stage 1 to full HireFormer"
    )

    args = parser.parse_args()

    print("Loading job description...")
    jd_text = load_docx_text(args.jd)
    blueprint = build_hiring_blueprint(jd_text)

    if args.mode == "fast":
        print(f"Running fast two-stage ranking with shortlist size {args.shortlist_size}...")
        results = fast_rank_candidates_from_jsonl(
            args.candidates,
            blueprint,
            shortlist_size=args.shortlist_size
        )
    else:
        print("Running full ranking on all candidates...")
        candidates = load_jsonl(args.candidates)
        print(f"Loaded {len(candidates)} candidates")
        results = rank_candidates(candidates, blueprint)

    print("Writing submission...")
    write_submission(results, args.out)

    print(f"Done: {args.out}")


if __name__ == "__main__":
    main()