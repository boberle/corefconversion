from zipfile import ZipFile

import pytest

from annotable import Corpus, EmptyDataSet, Mention, Paragraph, Sentence, Text, Token


@pytest.fixture
def corpus1() -> Corpus:
    # fmt: off
    corpus = Corpus(
        _texts=[
            Text(_paragraphs=[
                Paragraph(_sentences=[
                    Sentence(_tokens=[
                        Token(0, 1, "ab"),
                        Token(2, 3, "cd"),
                        Token(4, 5, "ef"),
                    ]),
                    Sentence(_tokens=[
                        Token(6, 7, "gh"),
                    ]),
                ]),
                Paragraph(_sentences=[
                    Sentence(_tokens=[
                        Token(8, 9, "ij"),
                        Token(10, 11, "kl"),
                    ]),
                ]),
                Paragraph(_sentences=[
                    Sentence(_tokens=[
                        Token(12, 13, "mn"),
                        Token(14, 15, "op"),
                        Token(16, 17, "qr"),
                    ]),
                    Sentence(_tokens=[
                        Token(18, 19, "st"),
                        Token(20, 21, "uv"),
                    ]),
                ]),
                Paragraph(_sentences=[
                    Sentence(_tokens=[
                        Token(22, 23, "wx"),
                        Token(24, 25, "yz"),
                    ]),
                ]),
            ]),
            Text(_paragraphs=[
                Paragraph(_sentences=[
                    Sentence(_tokens=[
                        Token(0, 1, "AB"),
                        Token(2, 3, "CD"),
                        Token(4, 5, "EF"),
                        Token(6, 7, "GH"),
                    ]),
                    Sentence(_tokens=[
                        Token(8, 9, "IJ"),
                        Token(10, 11, "KL"),
                    ]),
                ]),
                Paragraph(_sentences=[
                    Sentence(_tokens=[
                        Token(12, 13, "MN"),
                        Token(14, 15, "OP"),
                        Token(16, 17, "QR"),
                        Token(18, 19, "ST"),
                        Token(20, 21, "UV"),
                    ]),
                ]),
            ],
                name="my text",
            ),
        ]
    )
    # fmt: on

    def get_tokens(*strings: str) -> list[Token]:
        rv: list[Token] = []
        for string in strings:
            for token in corpus.tokens:
                if token.value == string:
                    rv.append(token)
        assert len(rv) == len(strings)
        return rv

    corpus._texts[0]._paragraphs[0]._sentences[0].add_mention(
        Mention("c1", "ab", get_tokens("ab"))
    )
    corpus._texts[0]._paragraphs[0]._sentences[0].add_mention(
        Mention("c2", "ef", get_tokens("ef"))
    )
    corpus._texts[0]._paragraphs[0]._sentences[1].add_mention(
        Mention("c1", "gh", get_tokens("gh"))
    )
    corpus._texts[0]._paragraphs[2]._sentences[0].add_mention(
        Mention("c3", "mn op", get_tokens("mn", "op"))
    )
    corpus._texts[0]._paragraphs[2]._sentences[1].add_mention(
        Mention("c1", "st", get_tokens("st"), features=dict(a=1, b=2, c=3))
    )
    corpus._texts[0]._paragraphs[3]._sentences[0].add_mention(
        Mention("c2", "yz", get_tokens("yz"))
    )

    corpus._texts[1]._paragraphs[0]._sentences[0].add_mention(
        Mention("c1", "AB", get_tokens("AB"))
    )
    corpus._texts[1]._paragraphs[0]._sentences[0].add_mention(
        Mention("c2", "EF GH", get_tokens("EF", "GH"), features=dict(A=1, B=2, C=3))
    )
    corpus._texts[1]._paragraphs[1]._sentences[0].add_mention(
        Mention("c2", "QR", get_tokens("QR"))
    )

    return corpus


def test_iter_paragraphs_as_dict_indices(corpus1: Corpus) -> None:
    actual = list(corpus1.iter_paragraphs_as_dict())
    expected = [0, 1, 2, 3, 0, 1]
    assert len(actual) == len(expected)
    for i, exp in enumerate(expected):
        assert actual[i]["index_of_paragraph_in_the_text"] == exp


def test_iter_sentences_as_dict_indices(corpus1: Corpus) -> None:
    actual = list(corpus1.iter_sentences_as_dict())
    expected = [
        [0, 0, 1, 2, 2, 3, 0, 0, 1],
        [0, 1, 0, 0, 1, 0, 0, 1, 0],
        [0, 1, 2, 3, 4, 5, 0, 1, 2],
    ]
    for i in range(len(expected)):
        assert len(actual) == len(expected[i])
    for i, (par_in_text, sent_in_par, sent_in_text) in enumerate(zip(*expected)):
        assert actual[i]["index_of_paragraph_in_the_text"] == par_in_text
        assert actual[i]["index_of_sentence_in_the_paragraph"] == sent_in_par
        assert actual[i]["index_of_sentence_in_the_text"] == sent_in_text


def test_iter_tokens_as_dict_indices(corpus1: Corpus) -> None:
    actual = list(corpus1.iter_tokens_as_dict())
    expected = [
        [0, 0, 0, 0, 1, 1, 2, 2, 2, 2, 2, 3, 3, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1],
        [0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 2, 2, 3, 3, 3, 4, 4, 5, 5, 0, 0, 0, 0, 1, 1, 2, 2, 2, 2, 2],
        [0, 1, 2, 0, 0, 1, 0, 1, 2, 0, 1, 0, 1, 0, 1, 2, 3, 0, 1, 0, 1, 2, 3, 4],
        [0, 1, 2, 3, 0, 1, 0, 1, 2, 3, 4, 0, 1, 0, 1, 2, 3, 4, 5, 0, 1, 2, 3, 4],
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    ]
    for i in range(len(expected)):
        assert len(actual) == len(expected[i])
    for i, (
        par_in_text,
        sent_in_par,
        sent_in_text,
        token_in_sent,
        token_in_par,
        token_in_text,
    ) in enumerate(zip(*expected)):
        assert actual[i]["index_of_paragraph_in_the_text"] == par_in_text
        assert actual[i]["index_of_sentence_in_the_paragraph"] == sent_in_par
        assert actual[i]["index_of_sentence_in_the_text"] == sent_in_text
        assert actual[i]["index_of_token_in_the_sentence"] == token_in_sent
        assert actual[i]["index_of_token_in_the_paragraph"] == token_in_par
        assert actual[i]["index_of_token_in_the_text"] == token_in_text


def test_iter_text_mentions_as_dict_indices(corpus1: Corpus) -> None:
    actual = list(corpus1.iter_text_mentions_as_dict())
    expected = [
        [0, 0, 2, 0, 3, 2, 0, 0, 1],
        [0, 1, 1, 0, 0, 0, 0, 0, 0],
        [0, 1, 4, 0, 5, 3, 0, 0, 2],
        [0, 0, 0, 1, 0, 0, 0, 1, 0],
        [0, 2, 1, 1, 0, 0, 0, 1, 0],
        [0, 2, 4, 1, 5, 3, 0, 1, 2],
        [0, 1, 2, 0, 1, 0, 0, 0, 1],
    ]
    for i in range(len(expected)):
        assert len(actual) == len(expected[i])
    for i, (
        par_in_text,
        sent_in_par,
        sent_in_text,
        mention_in_sent,
        mention_in_par,
        mention_in_text,
        mention_in_chain,
    ) in enumerate(zip(*expected)):
        assert actual[i]["index_of_paragraph_in_the_text"] == par_in_text
        assert actual[i]["index_of_sentence_in_the_paragraph"] == sent_in_par
        assert actual[i]["index_of_sentence_in_the_text"] == sent_in_text
        assert actual[i]["index_of_mention_in_the_sentence"] == mention_in_sent
        assert actual[i]["index_of_mention_in_the_paragraph"] == mention_in_par
        assert actual[i]["index_of_mention_in_the_text"] == mention_in_text
        assert actual[i]["index_of_mention_in_the_chain"] == mention_in_chain


def test_iter_text_chains_as_dict_indices(corpus1: Corpus) -> None:
    actual = list(corpus1.iter_text_chains_as_dict())
    expected = [
        [0, 1, 2, 0, 1],
    ]
    for i in range(len(expected)):
        assert len(actual) == len(expected[i])
    for i, (chain_in_text,) in enumerate(zip(*expected)):
        assert actual[i]["index_of_chain_in_the_text"] == chain_in_text


def test_iter_texts_as_dict_counts(corpus1: Corpus) -> None:
    actual = list(corpus1.iter_texts_as_dict())
    assert actual[0]["token_count"] == 13
    assert actual[0]["sentence_count"] == 6
    assert actual[0]["paragraph_count"] == 4
    assert actual[0]["mention_count"] == 6
    assert actual[0]["chain_count"] == 3

    assert actual[1]["token_count"] == 11
    assert actual[1]["sentence_count"] == 3
    assert actual[1]["paragraph_count"] == 2
    assert actual[1]["mention_count"] == 3
    assert actual[1]["chain_count"] == 2


def test_iter_paragraphs_as_dict_counts(corpus1: Corpus) -> None:
    actual = list(corpus1.iter_paragraphs_as_dict())
    expected = [
        [4, 2, 5, 2, 6, 5],
        [2, 1, 2, 1, 2, 1],
        [3, 0, 2, 1, 2, 1],
    ]
    for i, (token_count, sentence_count, mention_count) in enumerate(zip(*expected)):
        assert actual[i]["token_count"] == token_count
        assert actual[i]["sentence_count"] == sentence_count
        assert actual[i]["mention_count"] == mention_count


def test_iter_sentences_as_dict_counts(corpus1: Corpus) -> None:
    actual = list(corpus1.iter_sentences_as_dict())
    expected = [
        [3, 1, 2, 3, 2, 2, 4, 2, 5],
        [2, 1, 0, 1, 1, 1, 2, 0, 1],
    ]
    for i, (token_count, mention_count) in enumerate(zip(*expected)):
        assert actual[i]["token_count"] == token_count
        assert actual[i]["mention_count"] == mention_count


def test_iter_text_mentions_as_dict_counts(corpus1: Corpus) -> None:
    actual = list(corpus1.iter_text_mentions_as_dict())
    expected = [
        [1, 1, 1, 1, 1, 2, 1, 2, 1],
    ]
    for i, (token_count,) in enumerate(zip(*expected)):
        assert actual[i]["token_count"] == token_count


def test_iter_texts_as_dict_ids_and_names(corpus1: Corpus) -> None:
    actual = list(corpus1.iter_texts_as_dict())
    assert actual[0]["id"] == 0
    assert actual[0]["name"] is None
    assert actual[1]["id"] == 1
    assert actual[1]["name"] == "my text"


def test_iter_paragraphs_as_dict_ids_and_names(corpus1: Corpus) -> None:
    actual = list(corpus1.iter_paragraphs_as_dict())
    expected = [
        [0] * 4 + [1] * 2,
        [None] * 4 + ["my text"] * 2,
    ]
    for i, (text_id, text_name) in enumerate(zip(*expected)):  # type: ignore
        assert actual[i]["id"] == i
        assert actual[i]["text_id"] == text_id
        assert actual[i]["text_name"] == text_name


def test_iter_sentences_as_dict_ids_and_names(corpus1: Corpus) -> None:
    actual = list(corpus1.iter_sentences_as_dict())
    expected = [
        [0, 0, 1, 2, 2, 3, 4, 4, 5],
        [0] * 6 + [1] * 3,
        [None] * 6 + ["my text"] * 3,
    ]
    for i, (paragraph_id, text_id, text_name) in enumerate(zip(*expected)):  # type: ignore
        assert actual[i]["id"] == i
        assert actual[i]["paragraph_id"] == paragraph_id
        assert actual[i]["text_id"] == text_id
        assert actual[i]["text_name"] == text_name


def test_iter_tokens_as_dict_ids_and_names(corpus1: Corpus) -> None:
    actual = list(corpus1.iter_tokens_as_dict())
    expected = [
        [0, 0, 0, 1, 2, 2, 3, 3, 3, 4, 4, 5, 5, 6, 6, 6, 6, 7, 7, 8, 8, 8, 8, 8],
        [0, 0, 0, 0, 1, 1, 2, 2, 2, 2, 2, 3, 3, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5],
        [0] * 13 + [1] * 11,
        [None] * 13 + ["my text"] * 11,
    ]
    for i, (sentence_id, paragraph_id, text_id, text_name) in enumerate(zip(*expected)):  # type: ignore
        assert actual[i]["id"] == i
        assert actual[i]["sentence_id"] == sentence_id
        assert actual[i]["paragraph_id"] == paragraph_id
        assert actual[i]["text_id"] == text_id
        assert actual[i]["text_name"] == text_name


def test_iter_text_mentions_as_dict_ids_and_names(corpus1: Corpus) -> None:
    actual = list(corpus1.iter_text_mentions_as_dict())
    expected = [
        [0, 0, 0, 1, 1, 2, 3, 4, 4],
        ["c1", "c1", "c1", "c2", "c2", "c3", "c1", "c2", "c2"],
        [0, 1, 4, 0, 5, 3, 6, 6, 8],
        [0, 0, 2, 0, 3, 2, 4, 4, 5],
        [0] * 6 + [1] * 3,
        [None] * 6 + ["my text"] * 3,
    ]
    for i, (chain_id, chain_name, sentence_id, paragraph_id, text_id, text_name) in enumerate(zip(*expected)):  # type: ignore
        assert actual[i]["id"] == i
        assert actual[i]["chain_id"] == chain_id
        assert actual[i]["chain_name"] == chain_name
        assert actual[i]["sentence_id"] == sentence_id
        assert actual[i]["paragraph_id"] == paragraph_id
        assert actual[i]["text_id"] == text_id
        assert actual[i]["text_name"] == text_name


def test_iter_text_chains_as_dict_ids_and_names(corpus1: Corpus) -> None:
    actual = list(corpus1.iter_text_chains_as_dict())
    expected = [
        [0] * 3 + [1] * 2,
        [None] * 3 + ["my text"] * 2,
    ]
    for i, (text_id, text_name) in enumerate(zip(*expected)):  # type: ignore
        assert actual[i]["id"] == i
        assert actual[i]["text_id"] == text_id
        assert actual[i]["text_name"] == text_name


def test_iter_text_to_first_relations_as_dict_ids_and_names(corpus1: Corpus) -> None:
    actual = list(corpus1.iter_text_to_first_relations_as_dict())
    expected = [
        [0, 0, 1, 4],
        ["c1", "c1", "c2", "c2"],
        [0, 0, 0, 1],
        [None, None, None, "my text"],
        [0, 0, 3, 7],
        [1, 2, 4, 8],
    ]
    for i, (chain_id, chain_name, text_id, text_name, m1_id, m2_id) in enumerate(zip(*expected)):  # type: ignore
        assert actual[i]["id"] == i
        assert actual[i]["chain_id"] == chain_id
        assert actual[i]["chain_name"] == chain_name
        assert actual[i]["text_id"] == text_id
        assert actual[i]["text_name"] == text_name
        assert actual[i]["m1_id"] == m1_id
        assert actual[i]["m2_id"] == m2_id


def test_iter_text_consecutive_relations_as_dict_ids_and_names(corpus1: Corpus) -> None:
    actual = list(corpus1.iter_text_consecutive_relations_as_dict())
    expected = [
        [0, 0, 1, 4],
        ["c1", "c1", "c2", "c2"],
        [0, 0, 0, 1],
        [None, None, None, "my text"],
        [0, 1, 3, 7],
        [1, 2, 4, 8],
    ]
    for i, (chain_id, chain_name, text_id, text_name, m1_id, m2_id) in enumerate(zip(*expected)):  # type: ignore
        assert actual[i]["id"] == i
        assert actual[i]["chain_id"] == chain_id
        assert actual[i]["chain_name"] == chain_name
        assert actual[i]["text_id"] == text_id
        assert actual[i]["text_name"] == text_name
        assert actual[i]["m1_id"] == m1_id
        assert actual[i]["m2_id"] == m2_id


def test_iter_tokens_as_dict_other(corpus1: Corpus) -> None:
    actual = list(corpus1.iter_tokens_as_dict())
    expected = [
        [
            0,
            2,
            4,
            6,
            8,
            10,
            12,
            14,
            16,
            18,
            20,
            22,
            24,
            0,
            2,
            4,
            6,
            8,
            10,
            12,
            14,
            16,
            18,
            20,
        ],
        [
            1,
            3,
            5,
            7,
            9,
            11,
            13,
            15,
            17,
            19,
            21,
            23,
            25,
            1,
            3,
            5,
            7,
            9,
            11,
            13,
            15,
            17,
            19,
            21,
        ],
        [2] * 24,
        [
            "ab",
            "cd",
            "ef",
            "gh",
            "ij",
            "kl",
            "mn",
            "op",
            "qr",
            "st",
            "uv",
            "wx",
            "yz",
            "AB",
            "CD",
            "EF",
            "GH",
            "IJ",
            "KL",
            "MN",
            "OP",
            "QR",
            "ST",
            "UV",
        ],
    ]
    for i, (start, end, length, string) in enumerate(zip(*expected)):  # type: ignore
        assert actual[i]["start"] == start
        assert actual[i]["end"] == end
        assert actual[i]["length"] == length
        assert actual[i]["string"] == string


def test_iter_text_mentions_as_dict_other(corpus1: Corpus) -> None:
    actual = list(corpus1.iter_text_mentions_as_dict())
    expected = [
        [False, False, False, False, False, True, True, False, False],
        [3, 3, 3, 2, 2, 1, 1, 2, 2],
        [0, 6, 18, 4, 24, 12, 0, 4, 16],
        [1, 7, 19, 5, 25, 15, 1, 7, 17],
        [2, 2, 2, 2, 2, 4, 2, 4, 2],
        ["ab", "gh", "st", "ef", "yz", "mn op", "AB", "EF GH", "QR"],
    ]
    for i, (is_singleton, chain_size, start, end, length, string) in enumerate(zip(*expected)):  # type: ignore
        assert actual[i]["is_singleton"] == is_singleton
        assert actual[i]["chain_size"] == chain_size
        assert actual[i]["start"] == start
        assert actual[i]["end"] == end
        assert actual[i]["length"] == length
        assert actual[i]["string"] == string


def test_iter_text_chains_as_dict_other(corpus1: Corpus) -> None:
    actual = list(corpus1.iter_text_chains_as_dict())
    expected = [
        [3, 2, 1, 1, 2],
    ]
    for i, (size,) in enumerate(zip(*expected)):
        assert actual[i]["size"] == size


def test_iter_text_mentions_as_dict_features(corpus1: Corpus) -> None:
    mentions = list(corpus1.iter_text_mentions_as_dict())
    assert mentions[2]["a"] == 1
    assert mentions[2]["b"] == 2
    assert mentions[2]["c"] == 3

    assert mentions[7]["A"] == 1
    assert mentions[7]["B"] == 2
    assert mentions[7]["C"] == 3


def test_get_dataframes(corpus1: Corpus) -> None:
    dfs = corpus1.get_dataframes()
    assert list(dfs.texts.columns) == [
        "name",
        "token_count",
        "sentence_count",
        "paragraph_count",
        "mention_count",
        "chain_count",
    ]
    assert list(dfs.texts.index) == [i for i in range(2)]

    assert list(dfs.paragraphs.columns) == [
        "text_id",
        "text_name",
        "token_count",
        "sentence_count",
        "mention_count",
        "index_of_paragraph_in_the_text",
    ]
    assert list(dfs.paragraphs.index) == [i for i in range(6)]

    assert list(dfs.sentences.columns) == [
        "paragraph_id",
        "text_id",
        "text_name",
        "token_count",
        "mention_count",
        "index_of_paragraph_in_the_text",
        "index_of_sentence_in_the_paragraph",
        "index_of_sentence_in_the_text",
    ]
    assert list(dfs.sentences.index) == [i for i in range(9)]

    assert list(dfs.tokens.columns) == [
        "sentence_id",
        "paragraph_id",
        "text_id",
        "text_name",
        "start",
        "end",
        "length",
        "string",
        "index_of_paragraph_in_the_text",
        "index_of_sentence_in_the_paragraph",
        "index_of_sentence_in_the_text",
        "index_of_token_in_the_sentence",
        "index_of_token_in_the_paragraph",
        "index_of_token_in_the_text",
    ]
    assert list(dfs.tokens.index) == [i for i in range(24)]

    assert list(dfs.text_mentions.columns) == [
        "chain_name",
        "chain_id",
        "sentence_id",
        "paragraph_id",
        "text_id",
        "text_name",
        "is_singleton",
        "chain_size",
        "start",
        "end",
        "length",
        "string",
        "token_count",
        "index_of_mention_in_the_chain",
        "index_of_paragraph_in_the_text",
        "index_of_sentence_in_the_paragraph",
        "index_of_sentence_in_the_text",
        "index_of_mention_in_the_sentence",
        "index_of_mention_in_the_paragraph",
        "index_of_mention_in_the_text",
        "a",
        "b",
        "c",
        "A",
        "B",
        "C",
    ]
    assert list(dfs.text_mentions.index) == [i for i in range(9)]

    assert list(dfs.text_chains.columns) == [
        "text_id",
        "text_name",
        "name",
        "size",
        "index_of_chain_in_the_text",
    ]
    assert list(dfs.text_chains.index) == [i for i in range(5)]

    assert list(dfs.text_to_first_relations.columns) == [
        "chain_id",
        "chain_name",
        "text_id",
        "text_name",
        "m1_id",
        "m2_id",
    ]
    assert list(dfs.text_to_first_relations.index) == [i for i in range(4)]

    assert list(dfs.text_consecutive_relations.columns) == [
        "chain_id",
        "chain_name",
        "text_id",
        "text_name",
        "m1_id",
        "m2_id",
    ]
    assert list(dfs.text_consecutive_relations.index) == [i for i in range(4)]


def test_zipfile(corpus1: Corpus) -> None:
    buf = corpus1._create_csv_as_zip()
    zf = ZipFile(buf, "r")
    texts_csv = zf.read("texts")
    assert texts_csv.decode() == (
        ",name,token_count,sentence_count,paragraph_count,mention_count,chain_count\n"
        "0,,13,6,4,6,3\n"
        "1,my text,11,3,2,3,2\n"
    )


def test_text_metadata__no_metadata() -> None:
    corpus = Corpus(
        _texts=[
            Text(),
            Text(),
            Text(),
        ]
    )
    texts = list(corpus.iter_texts_as_dict())
    expected = [
        "id",
        "name",
        "token_count",
        "sentence_count",
        "paragraph_count",
        "mention_count",
        "chain_count",
    ]
    assert list(texts[0].keys()) == expected
    assert list(texts[1].keys()) == expected
    assert list(texts[2].keys()) == expected


def test_text_metadata__1_text_with_metadata() -> None:
    corpus = Corpus(
        _texts=[
            Text(metadata=dict(a="1", b=2)),
            Text(),
            Text(),
        ]
    )
    texts = list(corpus.iter_texts_as_dict())
    expected = [
        "id",
        "name",
        "token_count",
        "sentence_count",
        "paragraph_count",
        "mention_count",
        "chain_count",
    ]
    assert list(texts[0].keys()) == expected + ["a", "b"]
    assert list(texts[1].keys()) == expected
    assert list(texts[2].keys()) == expected

    assert texts[0]["a"] == "1"
    assert texts[0]["b"] == 2


def test_text_metadata__2_texts_with_metadata() -> None:
    corpus = Corpus(
        _texts=[
            Text(metadata=dict(a="1", b=2)),
            Text(),
            Text(metadata=dict(A="3", B=4)),
        ]
    )
    texts = list(corpus.iter_texts_as_dict())
    expected = [
        "id",
        "name",
        "token_count",
        "sentence_count",
        "paragraph_count",
        "mention_count",
        "chain_count",
    ]
    assert list(texts[0].keys()) == expected + ["a", "b"]
    assert list(texts[1].keys()) == expected
    assert list(texts[2].keys()) == expected + ["A", "B"]

    assert texts[0]["a"] == "1"
    assert texts[0]["b"] == 2
    assert texts[2]["A"] == "3"
    assert texts[2]["B"] == 4


def test_empty_dataset() -> None:
    corpus = Corpus(
        _texts=[
            Text(),
            Text(),
            Text(),
        ]
    )
    with pytest.raises(EmptyDataSet):
        corpus.get_dataframes()


def test_text_metadata_in_dataframe__2_texts_with_metadata(corpus1: Corpus) -> None:
    corpus1._texts[0].metadata = dict(a="1", b=2)
    corpus1._texts[1].metadata = dict(A="3", B=4)
    dfs = corpus1.get_dataframes()
    assert list(dfs.texts.columns) == [
        "name",
        "token_count",
        "sentence_count",
        "paragraph_count",
        "mention_count",
        "chain_count",
        "a",
        "b",
        "A",
        "B",
    ]
