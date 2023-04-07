from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Generator


@dataclass
class Token:
    start: int
    end: int

    def __eq__(self, other: Token) -> bool:
        return self.start == other.start and self.end == other.end


@dataclass
class TextID(Token):
    text_id: str

    def __eq__(self, other: TextID) -> bool:
        return super().__eq__(other) and self.text_id == other.text_id


@dataclass
class Comment(Token):
    value: str

    def __eq__(self, other: Comment) -> bool:
        return super().__eq__(other) and self.value == other.value


@dataclass
class ParagraphStart(Token):
    ...


@dataclass
class ParagraphEnd(Token):
    ...


@dataclass
class MentionStart(Token):
    chain_index: int
    chain_name: str
    features: dict[str, str]

    def __eq__(self, other: MentionStart) -> bool:
        return (
            super().__eq__(other)
            and self.chain_index == other.chain_index
            and self.chain_name == other.chain_name
            and self.features == other.features
        )


@dataclass
class MentionEnd(Token):
    ...


@dataclass
class Spaces(Token):
    value: str

    def __eq__(self, other: Spaces) -> bool:
        return super().__eq__(other) and self.value == other.value


@dataclass
class NewLineInsideParagraph(Token):
    value: str

    def __eq__(self, other: NewLineInsideParagraph) -> bool:
        return super().__eq__(other) and self.value == other.value


@dataclass
class Word(Token):
    value: str

    def __eq__(self, other: Word) -> bool:
        return super().__eq__(other) and self.value == other.value


@dataclass
class SentenceChange(Token):
    ...


def escape_regex(string: str) -> str:
    """Escape a string so it can be literally searched for in a regex.

    Used for `additional_tokens`.
    """
    return re.sub(r"([-{}\[\]().])", r"\\\1", string)


class SacrParser:
    """Parse a file in the SACR format."""

    def __init__(self, source: str | Path):
        if isinstance(source, str):
            self.content = source
        else:
            self.content = source.read_text()

    @staticmethod
    def get_word_pattern(additional_tokens: list[str] | None = None) -> re.Pattern[str]:
        """Compute the regex to match words, including additional_tokens."""
        if not additional_tokens:
            additional_tokens = []
        additional_tokens = sorted(
            [escape_regex(w) for w in additional_tokens], key=lambda x: len(x)
        )
        token_str = "[a-zßàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿœα-ω0-9_]+'?|[-+±]?[.,]?[0-9]+"
        if additional_tokens:
            return re.compile(
                "(%s|%s)" % (token_str, "|".join(additional_tokens)), re.IGNORECASE
            )
        else:
            return re.compile("(%s)" % token_str, re.IGNORECASE)

    def parse(self) -> Generator[Token, None, None]:
        """Parse the file and yields elements."""
        content = self.content
        additional_tokens: list[str] = []
        pos = 0
        chains: dict[str, int] = dict()
        open_mention_counter = 0

        # patterns
        additional_tokens_pattern = re.compile(r"#additional_?token:\s*(.+)\s*\n\n+")
        text_id_pattern = re.compile(r"#text_?id:\s*(.+)\s*\n\n*")
        comment_pattern = re.compile(r"(?:#(.*)(?:\n+|$)|\*{5,})")
        end_par_pattern = re.compile(r"\n\n+")
        space_pattern = re.compile(r"\s+")
        new_line_pattern = re.compile(r"\n")
        open_mention_pattern = re.compile(r"\{(\w+)(:| )")
        feature_pattern = re.compile(r'(\w+)=(?:(\w+)|"([^"]*)")(,| )')
        close_mention_pattern = re.compile(r"\}")
        sentence_end_pattern = re.compile(r'(?:\.+"?|\!|\?)')
        word_pattern = self.get_word_pattern(additional_tokens)

        # eat leading blank lines
        if m := re.compile(r"\s+").match(content, pos):
            pos += len(m.group(0))

        while pos < len(content):
            if m := additional_tokens_pattern.match(content, pos):
                pos += len(m.group(0))
                additional_tokens.append(m.group(1))
                word_pattern = SacrParser.get_word_pattern(additional_tokens)
                continue

            if m := text_id_pattern.match(content, pos):
                length = len(m.group(0))
                yield TextID(pos, pos + length, m.group(1))
                pos += length
                continue

            if m := comment_pattern.match(content, pos):
                length = len(m.group(0))
                if m.group(1):  # no group 0 if ******
                    comment = m.group(1).strip()
                    if comment:
                        yield Comment(pos, pos + length, comment)
                pos += length
                continue

            # parsing a paragraph

            yield ParagraphStart(pos, pos)

            while pos < len(content):
                if m := end_par_pattern.match(content, pos):
                    length = len(m.group(0))
                    yield ParagraphEnd(pos, pos + length)
                    pos += length
                    break

                if m := new_line_pattern.match(content, pos):
                    length = len(m.group(0))
                    yield NewLineInsideParagraph(pos, pos + length, m.group(0))
                    pos += length
                    continue

                if m := space_pattern.match(content, pos):
                    length = len(m.group(0))
                    yield Spaces(pos, pos + length, m.group(0))
                    pos += length
                    continue

                if m := open_mention_pattern.match(content, pos):
                    start = pos
                    pos += len(m.group(0))
                    open_mention_counter += 1

                    if m.group(1) not in chains:
                        chains[m.group(1)] = len(chains)
                    chain_index = chains[m.group(1)]
                    chain_name = m.group(1)

                    features = dict()
                    if m.group(2) == ":":
                        while pos < len(content):
                            if m := feature_pattern.match(content, pos):
                                key = m.group(1)
                                value = (
                                    m.group(2) if m.group(2) is not None else m.group(3)
                                )
                                features[key] = value
                                pos += len(m.group(0))
                                if m.group(4) == " ":
                                    break
                            else:
                                raise SyntaxError(
                                    "can't understand '%s' near %d" % (content, pos)
                                )
                    yield MentionStart(
                        start,
                        pos,
                        chain_index=chain_index,
                        chain_name=chain_name,
                        features=features,
                    )
                    continue

                if m := close_mention_pattern.match(content, pos):
                    length = len(m.group(0))
                    yield MentionEnd(pos, pos + length)
                    pos += length
                    open_mention_counter -= 1
                    continue

                if m := word_pattern.match(content, pos):
                    length = len(m.group(0))
                    yield Word(pos, pos + length, m.group(0))
                    pos += length
                    continue

                if open_mention_counter == 0:
                    if m := sentence_end_pattern.match(content, pos):
                        length = len(m.group(0))
                        yield Word(pos, pos + length, m.group(0))
                        yield SentenceChange(pos, pos + length)
                        pos += length
                        continue

                if m := re.compile(r".").match(content, pos):
                    length = len(m.group(0))
                    yield Word(pos, pos + length, m.group(0))
                    pos += length
                    continue
                assert False
