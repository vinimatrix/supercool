#!/usr/bin/env python3
"""
Standalone video analyzer for testing.
Usage: python analizador_video_qwen2_vl.py <video_path> [--reference <ref_image>] [--context "context"] [--output result.json]
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.local.coordinator import LocalVideoCoordinator


def get_duration(video_path: str) -> float:
    """Get video duration using ffprobe."""
    import subprocess
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", video_path],
            capture_output=True, text=True
        )
        info = json.loads(result.stdout)
        return float(info["format"]["duration"])
    except Exception:
        return 10.0


def main():
    parser = argparse.ArgumentParser(description="Analyze a video shot locally")
    parser.add_argument("video", help="Path to video file")
    parser.add_argument("--reference", help="Reference image path")
    parser.add_argument("--context", default="", help="Scene context")
    parser.add_argument("--output", help="Output JSON file")
    args = parser.parse_args()

    video_path = args.video
    if not Path(video_path).exists():
        print(f"Error: Video file not found: {video_path}")
        sys.exit(1)

    print(f"Analyzing: {video_path}")
    print("=" * 50)

    coordinator = LocalVideoCoordinator()

    shot = {
        "id": Path(video_path).stem,
        "prompt_text": Path(video_path).stem,
        "duration": get_duration(video_path),
        "video_path": video_path,
    }

    # Add reference if provided
    if args.reference:
        ref_path = Path(args.reference)
        if ref_path.exists():
            shot["reference_path"] = str(ref_path)
            print(f"Reference: {args.reference}")

    print("\nRunning two-layer analysis...")
    result = coordinator.analyze_shot(shot, args.context)

    # Print summary
    print("\n" + "=" * 50)
    print("ANALYSIS RESULT")
    print("=" * 50)
    print(f"Status: {result['decision']['status']}")
    print(f"Similarity: {result['decision'].get('similarity_score', 'N/A')}")
    print(f"Threshold: {result['decision'].get('threshold', 'N/A')}")

    if result["layer2"].get("narrative_analysis"):
        print(f"\nNarrative: {result['layer2']['narrative_analysis']}")
        print(f"Lighting: {result['layer2'].get('lighting_assessment', 'N/A')}")
        print(f"Mood: {result['layer2'].get('mood_suggestion', 'N/A')}")

    # Save output
    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nSaved to: {args.output}")
    else:
        print("\nFull result:")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
