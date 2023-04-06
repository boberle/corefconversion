import pytest

from sacr_parser2 import (
    Comment,
    NewLineInsideParagraph,
    ParagraphEnd,
    ParagraphStart,
    SacrParser,
    Spaces,
    TextID,
    Token,
    Word,
)

text1 = """#textid:abc-123

# my comment
# my other comment

abc def ghi
klm nop
qrs

# comment between

ABC DEF GHI

xyz
XYZ

# end comment"""


tokens1 = [
    TextID(start=0, end=17, text_id="abc-123"),
    Comment(start=17, end=30, value="my comment"),
    Comment(start=30, end=50, value="my other comment"),
    ParagraphStart(start=50, end=50),
    Word(start=50, end=53, value="abc"),
    Spaces(start=53, end=54, value=" "),
    Word(start=54, end=57, value="def"),
    Spaces(start=57, end=58, value=" "),
    Word(start=58, end=61, value="ghi"),
    NewLineInsideParagraph(start=61, end=62, value="\n"),
    Word(start=62, end=65, value="klm"),
    Spaces(start=65, end=66, value=" "),
    Word(start=66, end=69, value="nop"),
    NewLineInsideParagraph(start=69, end=70, value="\n"),
    Word(start=70, end=73, value="qrs"),
    ParagraphEnd(start=73, end=75),
    Comment(start=75, end=94, value="comment between"),
    ParagraphStart(start=94, end=94),
    Word(start=94, end=97, value="ABC"),
    Spaces(start=97, end=98, value=" "),
    Word(start=98, end=101, value="DEF"),
    Spaces(start=101, end=102, value=" "),
    Word(start=102, end=105, value="GHI"),
    ParagraphEnd(start=105, end=107),
    ParagraphStart(start=107, end=107),
    Word(start=107, end=110, value="xyz"),
    NewLineInsideParagraph(start=110, end=111, value="\n"),
    Word(start=111, end=114, value="XYZ"),
    ParagraphEnd(start=114, end=116),
    Comment(start=116, end=129, value="end comment"),
]


text2 = """abc def
ghi"""


tokens2 = [
    ParagraphStart(start=0, end=0),
    Word(start=0, end=3, value="abc"),
    Spaces(start=3, end=4, value=" "),
    Word(start=4, end=7, value="def"),
    NewLineInsideParagraph(start=7, end=8, value="\n"),
    Word(start=8, end=11, value="ghi"),
]


text3 = """#hello
#textid:abc-123
abc def
# not a comment
"""


tokens3 = [
    Comment(start=0, end=7, value="hello"),
    TextID(start=7, end=23, text_id="abc-123"),
    ParagraphStart(start=23, end=23),
    Word(start=23, end=26, value="abc"),
    Spaces(start=26, end=27, value=" "),
    Word(start=27, end=30, value="def"),
    NewLineInsideParagraph(start=30, end=31, value="\n"),
    Word(start=31, end=32, value="#"),
    Spaces(start=32, end=33, value=" "),
    Word(start=33, end=36, value="not"),
    Spaces(start=36, end=37, value=" "),
    Word(start=37, end=38, value="a"),
    Spaces(start=38, end=39, value=" "),
    Word(start=39, end=46, value="comment"),
    NewLineInsideParagraph(start=46, end=47, value="\n"),
]

text4 = """#comment
abc def

# comment
"""

tokens4 = [
    Comment(start=0, end=9, value="comment"),
    ParagraphStart(start=9, end=9),
    Word(start=9, end=12, value="abc"),
    Spaces(start=12, end=13, value=" "),
    Word(start=13, end=16, value="def"),
    ParagraphEnd(start=16, end=18),
    Comment(start=18, end=28, value="comment"),
]


@pytest.mark.parametrize(
    "text, tokens",
    [
        (text1, tokens1),
        (text2, tokens2),
        (text3, tokens3),
        (text4, tokens4),
    ],
)
def test_parse_texts(text: str, tokens: list[Token]) -> None:
    parser = SacrParser(text)
    actual_tokens = list(parser.parse())
    assert len(actual_tokens) == len(tokens)
    for a_t, t in zip(actual_tokens, tokens):
        assert a_t == t
