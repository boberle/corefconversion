import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Generator, Iterable
from zipfile import ZipFile

import pandas as pd  # type: ignore


@dataclass
class Token:
    start: int
    end: int
    value: str


class Annotable:
    ...


@dataclass
class Mention(Annotable):
    chain_name: str
    string: str
    _tokens: list[Token] = field(default_factory=list)
    features: dict[str, Any] = field(default_factory=dict)

    @property
    def tokens(self) -> Generator[Token, None, None]:
        for token in self._tokens:
            yield token

    @property
    def token_count(self) -> int:
        return len(self._tokens)

    def add_token(self, token: Token) -> None:
        self._tokens.append(token)

    def __contains__(self, item: Any) -> bool:
        return item in self.features

    def __setitem__(self, key: str, value: Any) -> None:
        self.features[key] = value

    def __getitem__(self, item: str) -> Any:
        return self.features[item]

    def __len__(self) -> int:
        return self.token_count

    @property
    def start(self) -> int:
        return self._tokens[0].start

    @property
    def end(self) -> int:
        return self._tokens[-1].end

    @property
    def character_count(self) -> int:
        return self.end - self.start + 1


@dataclass
class Chain:
    name: str
    _mentions: list[Mention] = field(default_factory=list)

    @property
    def mentions(self) -> Generator[Mention, None, None]:
        for mention in self._mentions:
            yield mention

    @property
    def mention_count(self) -> int:
        return len(self._mentions)

    def add_mention(self, mention: Mention) -> None:
        self._mentions.append(mention)


def _iter_chains(mentions: Iterable[Mention]) -> Generator[Chain, None, None]:
    chains: dict[str, Chain] = dict()
    for mention in mentions:
        if mention.chain_name not in chains:
            chains[mention.chain_name] = Chain(mention.chain_name)
        chains[mention.chain_name].add_mention(mention)
    for chain in chains.values():
        yield chain


@dataclass
class Sentence(Annotable):
    _tokens: list[Token] = field(default_factory=list)
    _mentions: list[Mention] = field(default_factory=list)

    def add_mention(self, mention: Mention) -> None:
        self._mentions.append(mention)

    @property
    def mentions(self) -> Generator[Mention, None, None]:
        for mention in self._mentions:
            yield mention

    @property
    def mention_count(self) -> int:
        return len(self._mentions)

    @property
    def tokens(self) -> Generator[Token, None, None]:
        for token in self._tokens:
            yield token

    @property
    def token_count(self) -> int:
        return len(self._tokens)

    def add_token(self, token: Token) -> None:
        self._tokens.append(token)

    @property
    def chains(self) -> Generator[Chain, None, None]:
        yield from _iter_chains(self._mentions)

    @property
    def chain_count(self) -> int:
        return len(list(self.chains))


@dataclass
class Paragraph(Annotable):
    _sentences: list[Sentence] = field(default_factory=list)

    @property
    def sentences(self) -> Generator[Sentence, None, None]:
        for sentence in self._sentences:
            yield sentence

    @property
    def sentence_count(self) -> int:
        return len(self._sentences)

    def add_sentence(self, sentence: Sentence) -> None:
        self._sentences.append(sentence)

    @property
    def mentions(self) -> Generator[Mention, None, None]:
        for sentence in self._sentences:
            yield from sentence.mentions

    @property
    def mention_count(self) -> int:
        return sum(sentence.mention_count for sentence in self._sentences)

    @property
    def chains(self) -> Generator[Chain, None, None]:
        yield from _iter_chains(self.mentions)

    @property
    def chain_count(self) -> int:
        return len(list(self.chains))

    @property
    def sentence_chains(self) -> Generator[Chain, None, None]:
        for sentence in self.sentences:
            yield from _iter_chains(sentence.mentions)

    @property
    def sentence_chain_count(self) -> int:
        return len(list(self.sentence_chains))

    @property
    def tokens(self) -> Generator[Token, None, None]:
        for sentence in self._sentences:
            yield from sentence.tokens

    @property
    def token_count(self) -> int:
        return sum(sentence.token_count for sentence in self._sentences)


@dataclass
class Text(Annotable):
    name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    _paragraphs: list[Paragraph] = field(default_factory=list)

    @property
    def paragraphs(self) -> Generator[Paragraph, None, None]:
        for paragraph in self._paragraphs:
            yield paragraph

    @property
    def paragraph_count(self) -> int:
        return len(self._paragraphs)

    def add_paragraph(self, paragraph: Paragraph) -> None:
        self._paragraphs.append(paragraph)

    @property
    def sentences(self) -> Generator[Sentence, None, None]:
        for paragraph in self._paragraphs:
            yield from paragraph.sentences

    @property
    def sentence_count(self) -> int:
        return sum(paragraph.sentence_count for paragraph in self._paragraphs)

    @property
    def mentions(self) -> Generator[Mention, None, None]:
        for paragraph in self._paragraphs:
            yield from paragraph.mentions

    @property
    def mention_count(self) -> int:
        return sum(paragraph.mention_count for paragraph in self._paragraphs)

    @property
    def chains(self) -> Generator[Chain, None, None]:
        yield from _iter_chains(self.mentions)

    @property
    def chain_count(self) -> int:
        return len(list(self.chains))

    @property
    def paragraph_chains(self) -> Generator[Chain, None, None]:
        for paragraph in self.paragraphs:
            yield from _iter_chains(paragraph.mentions)

    @property
    def paragraph_chain_count(self) -> int:
        return len(list(self.paragraph_chains))

    @property
    def sentence_chains(self) -> Generator[Chain, None, None]:
        for sentence in self.sentences:
            yield from _iter_chains(sentence.mentions)

    @property
    def sentence_chain_count(self) -> int:
        return len(list(self.sentence_chains))

    @property
    def tokens(self) -> Generator[Token, None, None]:
        for paragraph in self._paragraphs:
            yield from paragraph.tokens

    @property
    def token_count(self) -> int:
        return sum(paragraph.token_count for paragraph in self._paragraphs)


@dataclass
class DataFrameSet:
    texts: pd.DataFrame
    paragraphs: pd.DataFrame
    sentences: pd.DataFrame
    tokens: pd.DataFrame
    text_mentions: pd.DataFrame
    text_chains: pd.DataFrame
    text_to_first_relations: pd.DataFrame
    text_consecutive_relations: pd.DataFrame


class EmptyDataSet(Exception):
    pass


@dataclass
class Corpus(Annotable):
    _texts: list[Text] = field(default_factory=list)

    @property
    def texts(self) -> Generator[Text, None, None]:
        for text in self._texts:
            yield text

    @property
    def text_count(self) -> int:
        return len(self._texts)

    def add_text(self, text: Text) -> None:
        self._texts.append(text)

    @property
    def paragraphs(self) -> Generator[Paragraph, None, None]:
        for text in self._texts:
            yield from text.paragraphs

    @property
    def paragraph_count(self) -> int:
        return sum(text.paragraph_count for text in self._texts)

    @property
    def sentences(self) -> Generator[Sentence, None, None]:
        for text in self._texts:
            yield from text.sentences

    @property
    def sentence_count(self) -> int:
        return sum(text.sentence_count for text in self._texts)

    @property
    def mentions(self) -> Generator[Mention, None, None]:
        for text in self._texts:
            yield from text.mentions

    @property
    def mention_count(self) -> int:
        return sum(text.mention_count for text in self._texts)

    @property
    def chains(self) -> Generator[Chain, None, None]:
        yield from _iter_chains(self.mentions)

    @property
    def chain_count(self) -> int:
        return len(list(self.chains))

    @property
    def text_chains(self) -> Generator[Chain, None, None]:
        for text in self._texts:
            yield from _iter_chains(text.mentions)

    @property
    def text_chain_count(self) -> int:
        return len(list(self.text_chains))

    @property
    def paragraph_chains(self) -> Generator[Chain, None, None]:
        for paragraph in self.paragraphs:
            yield from _iter_chains(paragraph.mentions)

    @property
    def paragraph_chain_count(self) -> int:
        return len(list(self.paragraph_chains))

    @property
    def sentence_chains(self) -> Generator[Chain, None, None]:
        for sentence in self.sentences:
            yield from _iter_chains(sentence.mentions)

    @property
    def sentence_chain_count(self) -> int:
        return len(list(self.sentence_chains))

    @property
    def tokens(self) -> Generator[Token, None, None]:
        for text in self._texts:
            yield from text.tokens

    @property
    def token_count(self) -> int:
        return sum(text.token_count for text in self._texts)

    def iter_texts_as_dict(self) -> Generator[dict[str, Any], None, None]:
        for i, text in enumerate(self._texts):
            data = dict(
                id=i,
                name=text.name,
                token_count=text.token_count,
                sentence_count=text.sentence_count,
                paragraph_count=text.paragraph_count,
                mention_count=text.mention_count,
                chain_count=text.chain_count,
            )
            for k, v in text.metadata.items():
                data[k] = v
            yield data

    def iter_paragraphs_as_dict(self) -> Generator[dict[str, Any], None, None]:
        paragraph_index = 0
        for text_index, text in enumerate(self._texts):
            index_of_paragraph_in_the_text = 0
            for paragraph in text.paragraphs:
                yield dict(
                    id=paragraph_index,
                    text_id=text_index,
                    text_name=text.name,
                    token_count=paragraph.token_count,
                    sentence_count=paragraph.sentence_count,
                    mention_count=paragraph.mention_count,
                    index_of_paragraph_in_the_text=index_of_paragraph_in_the_text,
                )
                paragraph_index += 1
                index_of_paragraph_in_the_text += 1

    def iter_sentences_as_dict(self) -> Generator[dict[str, Any], None, None]:
        paragraph_index = 0
        sentence_index = 0
        for text_index, text in enumerate(self._texts):
            index_of_paragraph_in_the_text = 0
            index_of_sentence_in_the_text = 0
            for paragraph in text.paragraphs:
                index_of_sentence_in_the_paragraph = 0
                for sentence in paragraph.sentences:
                    yield dict(
                        id=sentence_index,
                        paragraph_id=paragraph_index,
                        text_id=text_index,
                        text_name=text.name,
                        token_count=sentence.token_count,
                        mention_count=sentence.mention_count,
                        index_of_paragraph_in_the_text=index_of_paragraph_in_the_text,
                        index_of_sentence_in_the_paragraph=index_of_sentence_in_the_paragraph,
                        index_of_sentence_in_the_text=index_of_sentence_in_the_text,
                    )
                    index_of_sentence_in_the_paragraph += 1
                    index_of_sentence_in_the_text += 1
                    sentence_index += 1
                index_of_paragraph_in_the_text += 1
                paragraph_index += 1

    def iter_tokens_as_dict(self) -> Generator[dict[str, Any], None, None]:
        token_index = 0
        paragraph_index = 0
        sentence_index = 0
        for text_index, text in enumerate(self._texts):
            index_of_paragraph_in_the_text = 0
            index_of_sentence_in_the_text = 0
            index_of_token_in_the_text = 0
            for paragraph in text.paragraphs:
                index_of_sentence_in_the_paragraph = 0
                index_of_token_in_the_paragraph = 0
                for sentence in paragraph.sentences:
                    index_of_token_in_the_sentence = 0
                    for token in sentence.tokens:
                        yield dict(
                            id=token_index,
                            sentence_id=sentence_index,
                            paragraph_id=paragraph_index,
                            text_id=text_index,
                            text_name=text.name,
                            start=token.start,
                            end=token.end,
                            length=token.end - token.start + 1,
                            string=token.value,
                            index_of_paragraph_in_the_text=index_of_paragraph_in_the_text,
                            index_of_sentence_in_the_paragraph=index_of_sentence_in_the_paragraph,
                            index_of_sentence_in_the_text=index_of_sentence_in_the_text,
                            index_of_token_in_the_sentence=index_of_token_in_the_sentence,
                            index_of_token_in_the_paragraph=index_of_token_in_the_paragraph,
                            index_of_token_in_the_text=index_of_token_in_the_text,
                        )
                        index_of_token_in_the_sentence += 1
                        index_of_token_in_the_paragraph += 1
                        index_of_token_in_the_text += 1
                        token_index += 1
                    index_of_sentence_in_the_paragraph += 1
                    index_of_sentence_in_the_text += 1
                    sentence_index += 1
                index_of_paragraph_in_the_text += 1
                paragraph_index += 1

    def iter_text_mentions_as_dict(self) -> Generator[dict[str, Any], None, None]:
        mention_indices_in_texts: dict[int, int] = dict()
        mention_indices_in_paragraphs: dict[int, int] = dict()
        mention_indices_in_sentences: dict[int, int] = dict()
        paragraph_indices_in_text: dict[int, int] = dict()
        sentence_indices_in_text: dict[int, int] = dict()
        sentence_indices_in_paragraph: dict[int, int] = dict()
        paragraph_indices: dict[int, int] = dict()
        sentence_indices: dict[int, int] = dict()

        paragraph_index = 0
        sentence_index = 0
        for text in self._texts:
            index_of_mention_in_text = 0
            index_of_paragraph_in_the_text = 0
            index_of_sentence_in_the_text = 0
            for paragraph in text.paragraphs:
                index_of_mention_in_paragraph = 0
                index_of_sentence_in_the_paragraph = 0
                for sentence in paragraph.sentences:
                    index_of_mention_in_sentence = 0
                    for mention in sentence.mentions:
                        mention_indices_in_sentences[
                            id(mention)
                        ] = index_of_mention_in_sentence
                        mention_indices_in_paragraphs[
                            id(mention)
                        ] = index_of_mention_in_paragraph
                        mention_indices_in_texts[id(mention)] = index_of_mention_in_text
                        sentence_indices_in_paragraph[
                            id(mention)
                        ] = index_of_sentence_in_the_paragraph
                        sentence_indices_in_text[
                            id(mention)
                        ] = index_of_sentence_in_the_text
                        paragraph_indices_in_text[
                            id(mention)
                        ] = index_of_paragraph_in_the_text
                        sentence_indices[id(mention)] = sentence_index
                        paragraph_indices[id(mention)] = paragraph_index
                        index_of_mention_in_sentence += 1
                        index_of_mention_in_paragraph += 1
                        index_of_mention_in_text += 1
                    index_of_sentence_in_the_text += 1
                    index_of_sentence_in_the_paragraph += 1
                    sentence_index += 1
                index_of_paragraph_in_the_text += 1
                paragraph_index += 1

        mention_index = 0
        chain_id = 0
        for text_index, text in enumerate(self._texts):
            for chain in text.chains:
                for mention in chain.mentions:
                    data = dict(
                        id=mention_index,
                        chain_name=chain.name,
                        chain_id=chain_id,
                        sentence_id=sentence_indices[id(mention)],
                        paragraph_id=paragraph_indices[id(mention)],
                        text_id=text_index,
                        text_name=text.name,
                        is_singleton=chain.mention_count == 1,
                        chain_size=chain.mention_count,
                        start=mention.start,
                        end=mention.end,
                        length=mention.end - mention.start + 1,
                        string=mention.string,
                        token_count=mention.token_count,
                        index_of_paragraph_in_the_text=paragraph_indices_in_text[
                            id(mention)
                        ],
                        index_of_sentence_in_the_paragraph=sentence_indices_in_paragraph[
                            id(mention)
                        ],
                        index_of_sentence_in_the_text=sentence_indices_in_text[
                            id(mention)
                        ],
                        index_of_mention_in_the_sentence=mention_indices_in_sentences[
                            id(mention)
                        ],
                        index_of_mention_in_the_paragraph=mention_indices_in_paragraphs[
                            id(mention)
                        ],
                        index_of_mention_in_the_text=mention_indices_in_texts[
                            id(mention)
                        ],
                    )
                    for k, v in mention.features.items():
                        data[k] = v
                    yield data
                    mention_index += 1
                chain_id += 1

    def iter_text_chains_as_dict(self) -> Generator[dict[str, Any], None, None]:
        chain_index = 0
        for text_index, text in enumerate(self._texts):
            index_of_chain_in_the_text = 0
            for chain in text.chains:
                yield dict(
                    id=chain_index,
                    text_id=text_index,
                    text_name=text.name,
                    name=chain.name,
                    size=chain.mention_count,
                    index_of_chain_in_the_text=index_of_chain_in_the_text,
                )
                index_of_chain_in_the_text += 1
                chain_index += 1

    def iter_text_to_first_relations_as_dict(
        self,
    ) -> Generator[dict[str, Any], None, None]:
        chain_index = 0
        relation_index = 0
        mention_index = 0
        for text_index, text in enumerate(self._texts):
            for chain in text.chains:
                first_mention_index: int | None = None
                for i, mention in enumerate(chain.mentions):
                    if i == 0:
                        first_mention_index = mention_index
                    else:
                        yield dict(
                            id=relation_index,
                            chain_id=chain_index,
                            chain_name=chain.name,
                            text_id=text_index,
                            text_name=text.name,
                            m1_id=first_mention_index,
                            m2_id=mention_index,
                        )
                        relation_index += 1
                    mention_index += 1
                chain_index += 1

    def iter_text_consecutive_relations_as_dict(
        self,
    ) -> Generator[dict[str, Any], None, None]:
        chain_index = 0
        relation_index = 0
        mention_index = 0
        for text_index, text in enumerate(self._texts):
            for chain in text.chains:
                for i, mention in enumerate(chain.mentions):
                    if i == 0:
                        pass
                    else:
                        yield dict(
                            id=relation_index,
                            chain_id=chain_index,
                            chain_name=chain.name,
                            text_id=text_index,
                            text_name=text.name,
                            m1_id=mention_index - 1,
                            m2_id=mention_index,
                        )
                        relation_index += 1
                    mention_index += 1
                chain_index += 1

    def get_dataframes(self) -> DataFrameSet:
        def get_df(data: Iterable[dict[str, Any]], name: str) -> pd.DataFrame:
            try:
                index, dicts = zip(
                    *map(
                        lambda d: (d["id"], {k: v for k, v in d.items() if k != "id"}),
                        data,
                    )
                )
            except ValueError:
                raise EmptyDataSet(f"Empty data set: '{name}'")
            else:
                return pd.DataFrame(data=dicts, index=index)

        return DataFrameSet(
            texts=get_df(self.iter_texts_as_dict(), "texts"),
            paragraphs=get_df(self.iter_paragraphs_as_dict(), "paragraphs"),
            sentences=get_df(self.iter_sentences_as_dict(), "sentences"),
            tokens=get_df(self.iter_tokens_as_dict(), "tokens"),
            text_mentions=get_df(self.iter_text_mentions_as_dict(), "text_mentions"),
            text_chains=get_df(self.iter_text_chains_as_dict(), "text_chains"),
            text_to_first_relations=get_df(
                self.iter_text_to_first_relations_as_dict(), "text_to_first_relations"
            ),
            text_consecutive_relations=get_df(
                self.iter_text_consecutive_relations_as_dict(),
                "text_consecutive_relations",
            ),
        )

    def _create_csv_as_zip(self) -> io.BytesIO:
        dfs = self.get_dataframes()

        buf = io.BytesIO()
        zf = ZipFile(buf, "w")
        zf.writestr("texts", dfs.texts.to_csv())
        zf.writestr("paragraphs", dfs.paragraphs.to_csv())
        zf.writestr("sentences", dfs.sentences.to_csv())
        zf.writestr("tokens", dfs.tokens.to_csv())
        zf.writestr("text_mentions", dfs.text_mentions.to_csv())
        zf.writestr("text_chains", dfs.text_chains.to_csv())
        zf.writestr("text_to_first_relations", dfs.text_to_first_relations.to_csv())
        zf.writestr(
            "text_consecutive_relations", dfs.text_consecutive_relations.to_csv()
        )
        zf.close()

        buf.seek(0)
        return buf

    def save_csv_as_zip(self, file: Path) -> None:
        buf = self._create_csv_as_zip()
        file.write_bytes(buf.read())
