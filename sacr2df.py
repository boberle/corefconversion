"""Convert a corpus of texts annotated with SACR in a series of dataframes or
CSV files.

This dataframes/files model:
- corpus, texts, sentences, tokens
- mentions, chains and relations

Please see the README file for a detail description.

You can use the script in the CLI:

    python3 sacr2df.py text1.sacr text2.sacr ... -o output_file.zip

or as a library, for example in a Jupyter notebook:

    from sacr2df import convert_sacr_files_to_dataframes
    from pathlib import Path

    dfs = convert_sacr_files_to_dataframes(
        Path("testing/aesop.sacr"),
        Path("testing/caesar.sacr"),
        Path("testing/cicero.sacr"),
        Path("testing/pliny.sacr"),
    )

    # then do something with the dfs:
    print(dfs.texts.head())
    print(dfs.paragraphs.head())
    print(dfs.sentences.head())
    print(dfs.tokens.head())
    print(dfs.text_chains.head())
    print(dfs.text_mentions.head())
    print(dfs.text_consecutive_relations.head())
    print(dfs.text_to_first_relations.head())
"""

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
        description=__doc__,
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
