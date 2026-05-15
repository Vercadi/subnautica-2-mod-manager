from __future__ import annotations

import argparse
from pathlib import Path

from ..core.release_metadata import write_release_metadata


def main() -> None:
    parser = argparse.ArgumentParser(description="Write Subnautica 2 Mod Manager release metadata.")
    parser.add_argument("--output", default="release-metadata.json", help="Output JSON path.")
    args = parser.parse_args()
    metadata = write_release_metadata(Path(args.output))
    print(f"Wrote {args.output} for {metadata['app_name']} {metadata['version']}")


if __name__ == "__main__":
    main()
