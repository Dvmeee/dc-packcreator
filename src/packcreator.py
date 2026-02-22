"""
dc-packcreator – simple pack creator
Creates a zip archive (pack) from a given source folder.
"""

import argparse
import os
import zipfile
from datetime import datetime


def create_pack(source_dir: str, output_dir: str, pack_name: str | None = None) -> str:
    """
    Zip the contents of *source_dir* into a pack file placed in *output_dir*.

    Args:
        source_dir:  Path to the folder whose contents will be packed.
        output_dir:  Directory where the resulting .zip file will be saved.
        pack_name:   Optional base name for the archive (without extension).
                     Defaults to '<source_folder_name>_<timestamp>'.

    Returns:
        The absolute path of the created pack file.

    Raises:
        FileNotFoundError: If *source_dir* does not exist.
        NotADirectoryError: If *source_dir* is not a directory.
    """
    source_dir = os.path.abspath(source_dir)
    if not os.path.exists(source_dir):
        raise FileNotFoundError(f"Source directory not found: {source_dir}")
    if not os.path.isdir(source_dir):
        raise NotADirectoryError(f"Source path is not a directory: {source_dir}")

    os.makedirs(output_dir, exist_ok=True)

    if pack_name is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pack_name = f"{os.path.basename(source_dir)}_{timestamp}"

    pack_path = os.path.join(output_dir, f"{pack_name}.zip")

    with zipfile.ZipFile(pack_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, start=source_dir)
                zf.write(file_path, arcname)

    return os.path.abspath(pack_path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="dc-packcreator – create a zip pack from a folder"
    )
    parser.add_argument(
        "source",
        help="Path to the source folder to pack",
    )
    parser.add_argument(
        "--output",
        default="output",
        help="Directory where the pack will be saved (default: output/)",
    )
    parser.add_argument(
        "--name",
        default=None,
        help="Base name for the pack file (without .zip extension)",
    )
    args = parser.parse_args()

    pack_path = create_pack(args.source, args.output, args.name)
    print(f"Pack created: {pack_path}")


if __name__ == "__main__":
    main()
