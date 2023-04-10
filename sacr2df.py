import argparse
from argparse import Namespace
from pathlib import Path

from annotable import DataFrameSet
from sacr2annotable import Sacr2AnnotableConverter


def convert_sacr_files_to_dataframes(
    *files: Path, output_file: Path | None = None
) -> DataFrameSet:
    conv = Sacr2AnnotableConverter()
    for file in files:
        conv.convert_text(file)
    corpus = conv.corpus

    if output_file:
        corpus.save_csv_as_zip(output_file)

    return corpus.get_dataframes()


def parse_args() -> Namespace:
    parser = argparse.ArgumentParser(
        prog="sacr2df",
        description="convert sacr files to series of dataframes, or write them on disk in csv format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input_files", nargs="+", help="input files")
    parser.add_argument(
        "--output_file",
        "-o",
        required=True,
        help="output file. This is a zip file containing the csv",
    )
    args = parser.parse_args()
    return args


def main() -> None:
    args = parse_args()
    convert_sacr_files_to_dataframes(
        *[Path(f) for f in args.input_files],
        output_file=Path(args.output_file),
    )


if __name__ == "__main__":
    main()
