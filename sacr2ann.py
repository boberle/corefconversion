from __future__ import annotations

import argparse
from argparse import Namespace
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from sacr_parser2 import (
    MentionEnd,
    MentionStart,
    ParagraphEnd,
    SacrParser,
    Spaces,
    Word,
)

DEFAULT_MENTION_TYPE = "Mention"
DEFAULT_RELATION_TYPE = "Coreference"


@dataclass
class Annotation:
    index: int
    kind: str

    def __eq__(self, other: Annotation) -> bool:
        return self.index == other.index and self.kind == other.kind


@dataclass
class TextAnnotation(Annotation):
    start: int
    end: int

    def __eq__(self, other: TextAnnotation) -> bool:
        return (
            super().__eq__(other)
            and self.start == other.start
            and self.end == other.end
        )


@dataclass
class RelationAnnotation(Annotation):
    source: Annotation
    target: Annotation

    def __eq__(self, other: RelationAnnotation) -> bool:
        return (
            super().__eq__(other)
            and self.source == other.source
            and self.target == other.target
        )


class Sacr2AnnConverter:
    def __init__(self, type_property_name: str | None = None):
        self.type_property_name = type_property_name
        self._text: str | None = None
        self._annotations: list[Annotation] | None = None

    def convert(self, source: str | Path) -> None:
        parser = SacrParser(source=source)

        text: str = ""
        annotations: list[Annotation] = []
        text_annotation_count: int = 0
        relation_annotation_count: int = 0

        chains: dict[int, list[TextAnnotation]] = defaultdict(list)
        filo: list[TextAnnotation] = []

        for token in parser.parse():
            start_position = len(text)

            if isinstance(token, (Word, Spaces)):
                text += token.value
            elif isinstance(token, ParagraphEnd):
                text += "\n\n"

            elif isinstance(token, MentionStart):
                text_annotation_count += 1
                if self.type_property_name:
                    kind = token.features.get(
                        self.type_property_name, DEFAULT_MENTION_TYPE
                    )
                else:
                    kind = DEFAULT_MENTION_TYPE
                text_annotation = TextAnnotation(
                    index=text_annotation_count,
                    kind=kind,
                    start=start_position,
                    end=0,
                )
                filo.append(text_annotation)
                annotations.append(text_annotation)

                if token.chain_index in chains:
                    relation_annotation_count += 1
                    relation_annotation = RelationAnnotation(
                        index=relation_annotation_count,
                        kind=DEFAULT_RELATION_TYPE,
                        source=chains[token.chain_index][-1],
                        target=text_annotation,
                    )
                    annotations.append(relation_annotation)

                chains[token.chain_index].append(text_annotation)

            elif isinstance(token, MentionEnd):
                text_annotation = filo.pop()
                text_annotation.end = len(text)

        self._text = text
        self._annotations = annotations

    @property
    def text(self) -> str:
        if self._text is None:
            raise RuntimeError("You need to parse before reading the text property")
        return self._text

    @property
    def annotations(self) -> list[Annotation]:
        if self._annotations is None:
            raise RuntimeError(
                "You need to parse before reading the annotations property"
            )
        return self._annotations

    def write_text_to_file(self, file: Path) -> None:
        file.write_text(self.text)

    @staticmethod
    def _convert_annotations_as_string(text: str, annotations: list[Annotation]) -> str:
        string = ""
        for annotation in annotations:
            if isinstance(annotation, TextAnnotation):
                span = text[annotation.start : annotation.end]
                string += f"T{annotation.index}\t{annotation.kind} {annotation.start} {annotation.end}\t{span}\n"
            elif isinstance(annotation, RelationAnnotation):
                string += f"R{annotation.index}\t{annotation.kind} Arg1:T{annotation.source.index} Arg2:T{annotation.target.index}\n"
            else:
                raise RuntimeError(
                    "unknown annotation type: " + annotation.__class__.__name__
                )
        return string

    @property
    def annotations_as_string(self) -> str:
        return self._convert_annotations_as_string(self.text, self.annotations)

    def write_annotations_to_file(self, file: Path) -> None:
        file.write_text(self.annotations_as_string)


def convert(
    input_file: Path, txt_output: Path, ann_output: Path, type_property_name: str
) -> None:
    converter = Sacr2AnnConverter(type_property_name=type_property_name)
    converter.convert(input_file)
    converter.write_text_to_file(txt_output)
    converter.write_annotations_to_file(ann_output)


def parse_args() -> Namespace:
    parser = argparse.ArgumentParser(
        prog="sacr2add",
        description="convert a sacr file to an ann/txt files (BRAT standoff annotations)",
        # description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input", help="input file")
    parser.add_argument(
        "--txt",
        dest="txt_output",
        default=None,
        help="output file, default is input file name + .txt",
    )
    parser.add_argument(
        "--ann",
        dest="ann_output",
        default=None,
        help="output file, default is input file name + .ann",
    )
    parser.add_argument(
        "--type-property-name",
        default=None,
        help=f"name of the property where to find the type of text annotation. If not given, '{DEFAULT_MENTION_TYPE}' is used as the type",
    )
    args = parser.parse_args()
    return args


def main() -> None:
    args = parse_args()
    convert(
        input_file=Path(args.input),
        txt_output=Path(args.txt_output or (args.input + ".txt")),
        ann_output=Path(args.ann_output or (args.input + ".ann")),
        type_property_name=args.type_property_name,
    )


if __name__ == "__main__":
    main()
