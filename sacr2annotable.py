"""Convert a corpus of SACR texts into a Corpus (from annotable.py) that can be
used to output dataframes.

It is a class which should be used as follows:

files = [
    Path("file1.sacr"),
    Path("file2.sacr"),
    Path("file3.sacr"),
    # ...
]

converter = Sacr2AnnotableConverter()
for file in files:
    converter.convert_text(file)
corpus = converter.corpus

dataframes = corpus.get_dataframes()
"""

from __future__ import annotations

import re
from pathlib import Path

from annotable import Corpus, Mention, Paragraph, Sentence, Text, Token
from sacr_parser2 import (
    Comment,
    MentionEnd,
    MentionStart,
    ParagraphEnd,
    SacrParser,
    SentenceChange,
    Spaces,
    TextID,
    Word,
)

TEXT_METADATA_PATTERN = re.compile(r"textmetadata\s*:\s*(\w+)\s*=\s*(.*)")


class Sacr2AnnotableConverter:
    def __init__(self) -> None:
        self.corpus: Corpus = Corpus()

    def convert_text(self, source: str | Path) -> None:
        parser = SacrParser(source=source)

        text: Text = Text()
        current_paragraph: Paragraph = Paragraph()
        current_sentence: Sentence = Sentence()
        filo: list[Mention] = []

        for token in parser.parse():
            if isinstance(token, Spaces):
                for mention in filo:
                    mention.string += token.value

            elif isinstance(token, Word):
                t = Token(token.start, token.end, token.value)
                for mention in filo:
                    mention.add_token(t)
                    mention.string += token.value
                current_sentence.add_token(t)

            elif isinstance(token, TextID):
                text.name = token.text_id

            elif isinstance(token, ParagraphEnd):
                if current_sentence.token_count:
                    current_paragraph.add_sentence(current_sentence)
                    current_sentence = Sentence()
                text.add_paragraph(current_paragraph)
                current_paragraph = Paragraph()

            elif isinstance(token, SentenceChange):
                if current_sentence.token_count:
                    current_paragraph.add_sentence(current_sentence)
                    current_sentence = Sentence()

            elif isinstance(token, MentionStart):
                mention = Mention(chain_name=token.chain_name, string="")
                for k, v in token.features.items():
                    mention[k] = v
                current_sentence.add_mention(mention)
                filo.append(mention)

            elif isinstance(token, MentionEnd):
                filo.pop()

            elif isinstance(token, Comment):
                if m := TEXT_METADATA_PATTERN.fullmatch(token.value):
                    text.metadata[m.group(1)] = m.group(2)

        if current_sentence.token_count:
            current_paragraph.add_sentence(current_sentence)
        if current_paragraph.sentence_count:
            text.add_paragraph(current_paragraph)

        self.corpus.add_text(text)
