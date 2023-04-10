import pytest

from sacr2annotable import Sacr2AnnotableConverter


@pytest.fixture
def text1() -> str:
    return (
        "{c1:prop1=a,prop2=b {c2:prop1=cc,prop2=dd abc def} ghi}. jkl {c1:prop1=eee,prop2=fff mno}.\n\n"
        "pqr stu {c1:prop1=gggg,prop2=hhhh vwx}\n\n"
    )


@pytest.fixture
def text2() -> str:
    return (
        "#textid:mytext\n\n"
        "#textmetadata:type=literature\n"
        "#textmetadata:genre=\n"
        "#textmetadata:century=19\n\n"
        "ABC {c2:prop1=A,prop2=B DEF {c2:prop1=CC,prop2=DD GHI}} ! JKL MNO\n\n"
        "PRQ ? {c3:prop1=EEE,prop2=FFF STU}.\n\n"
        "# comment 1\n"
        "# comment 2\n\n"
        "{c2:prop1=GGGG,prop2=HHHH VWX}"
    )


def test_sacr2annotable_converter(text1: str, text2: str) -> None:
    conv = Sacr2AnnotableConverter()
    conv.convert_text(text1)
    conv.convert_text(text2)
    corpus = conv.corpus

    t1 = corpus._texts[0]
    t2 = corpus._texts[1]

    assert t1.name is None
    assert t2.name == "mytext"

    expected_tokens = "abc def ghi . jkl mno . pqr stu vwx".split()
    assert t1.token_count == len(expected_tokens)
    assert [t.value for t in t1.tokens] == expected_tokens

    expected_tokens = "ABC DEF GHI ! JKL MNO PRQ ? STU . VWX".split()
    assert t2.token_count == len(expected_tokens)
    assert [t.value for t in t2.tokens] == expected_tokens

    assert t1.sentence_count == 3
    assert t2.sentence_count == 5
    assert t1.paragraph_count == 2
    assert t2.paragraph_count == 3
    assert t1.mention_count == 4
    assert t2.mention_count == 4
    assert t1.chain_count == 2
    assert t2.chain_count == 2

    mentions = list(corpus.iter_text_mentions_as_dict())
    assert mentions[0]["string"] == "abc def ghi"
    assert mentions[3]["string"] == "abc def"

    assert mentions[4]["string"] == "DEF GHI"
    assert mentions[5]["string"] == "GHI"

    assert mentions[0]["index_of_mention_in_the_text"] == 0
    assert mentions[1]["index_of_mention_in_the_text"] == 2
    assert mentions[2]["index_of_mention_in_the_text"] == 3
    assert mentions[3]["index_of_mention_in_the_text"] == 1
    assert mentions[4]["index_of_mention_in_the_text"] == 0
    assert mentions[5]["index_of_mention_in_the_text"] == 1
    assert mentions[6]["index_of_mention_in_the_text"] == 3
    assert mentions[7]["index_of_mention_in_the_text"] == 2

    assert mentions[1]["prop1"] == "eee"
    assert mentions[1]["prop2"] == "fff"
    assert mentions[5]["prop1"] == "CC"
    assert mentions[5]["prop2"] == "DD"
    assert mentions[7]["is_singleton"] is True

    chains = list(corpus.iter_text_chains_as_dict())
    assert chains[0]["size"] == 3
    assert chains[2]["size"] == 3
    assert chains[3]["size"] == 1


def test_sacr2annotable_text_metadata(text1: str, text2: str) -> None:
    conv = Sacr2AnnotableConverter()
    conv.convert_text(text1)
    conv.convert_text(text2)
    corpus = conv.corpus

    with pytest.raises(KeyError):
        _ = corpus._texts[0].metadata["type"]

    with pytest.raises(KeyError):
        _ = corpus._texts[0].metadata["genre"]

    with pytest.raises(KeyError):
        _ = corpus._texts[0].metadata["century"]

    assert corpus._texts[1].metadata["type"] == "literature"
    assert corpus._texts[1].metadata["genre"] == ""
    assert corpus._texts[1].metadata["century"] == "19"
