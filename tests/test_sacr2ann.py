from sacr2ann import (
    DEFAULT_MENTION_TYPE,
    DEFAULT_RELATION_TYPE,
    Annotation,
    RelationAnnotation,
    Sacr2AnnConverter,
    TextAnnotation,
)


def test_sacr2ann_1_annotation() -> None:
    text = """hello {chain1:a=1,b=2,type=WORD world}!"""
    converter = Sacr2AnnConverter(type_property_name="type")
    converter.convert(text)

    assert converter.text == "hello world!"

    ann = converter.annotations
    assert len(ann) == 1
    assert ann[0] == TextAnnotation(index=1, kind="WORD", start=6, end=11)


def test_sacr2ann_2_annotations_in_1_paragraph_in_2_chains() -> None:
    text = """hello {chain1:a=1,b=2,type=ABC world}! It'{chain2:type=DEF s} sunny"""
    converter = Sacr2AnnConverter(type_property_name="type")
    converter.convert(text)

    assert converter.text == "hello world! It's sunny"

    ann = converter.annotations
    assert len(ann) == 2
    assert ann[0] == TextAnnotation(index=1, kind="ABC", start=6, end=11)
    assert ann[1] == TextAnnotation(index=2, kind="DEF", start=16, end=17)


def test_sacr2ann_2_annotations_in_1_paragraph_in_1_chain() -> None:
    text = "hello {chain1:a=1,b=2,type=ABC world}! " "It'{chain1:type=DEF s} sunny"
    converter = Sacr2AnnConverter(type_property_name="type")
    converter.convert(text)

    assert converter.text == "hello world! It's sunny"

    ann = converter.annotations
    assert len(ann) == 3
    assert ann[0] == TextAnnotation(index=1, kind="ABC", start=6, end=11)
    assert ann[1] == TextAnnotation(index=2, kind="DEF", start=16, end=17)
    assert ann[2] == RelationAnnotation(
        index=1, kind=DEFAULT_RELATION_TYPE, source=ann[0], target=ann[1]
    )


def test_sacr2ann_3_annotations_in_1_paragraph_in_1_chain() -> None:
    text = (
        "hello {chain1:a=1,b=2,type=ABC world}! "
        "It'{chain1:type=DEF s} sunny. "
        "It's not {chain1:type=ABC rainy}"
    )
    converter = Sacr2AnnConverter(type_property_name="type")
    converter.convert(text)

    assert converter.text == "hello world! It's sunny. It's not rainy"

    ann = converter.annotations
    assert len(ann) == 5
    assert ann[0] == TextAnnotation(index=1, kind="ABC", start=6, end=11)
    assert ann[1] == TextAnnotation(index=2, kind="DEF", start=16, end=17)
    assert ann[2] == RelationAnnotation(
        index=1, kind=DEFAULT_RELATION_TYPE, source=ann[0], target=ann[1]
    )
    assert ann[3] == TextAnnotation(index=3, kind="ABC", start=34, end=39)
    assert ann[4] == RelationAnnotation(
        index=2, kind=DEFAULT_RELATION_TYPE, source=ann[1], target=ann[3]
    )


def test_sacr2ann_3_annotations_in_1_paragraph_in_2_chains() -> None:
    text = (
        "hello {chain1:a=1,b=2,type=ABC world}! "
        "It'{chain2:type=DEF s} sunny. "
        "It's not {chain2:type=ABC rainy}"
    )
    converter = Sacr2AnnConverter(type_property_name="type")
    converter.convert(text)

    assert converter.text == "hello world! It's sunny. It's not rainy"

    ann = converter.annotations
    assert len(ann) == 4
    assert ann[0] == TextAnnotation(index=1, kind="ABC", start=6, end=11)
    assert ann[1] == TextAnnotation(index=2, kind="DEF", start=16, end=17)
    assert ann[2] == TextAnnotation(index=3, kind="ABC", start=34, end=39)
    assert ann[3] == RelationAnnotation(
        index=1, kind=DEFAULT_RELATION_TYPE, source=ann[1], target=ann[2]
    )


def test_sacr2ann_4_annotations_in_1_paragraph_in_2_chains() -> None:
    text = (
        "hello {chain1:a=1,b=2,type=ABC world}! "
        "It'{chain2:type=DEF s} sunny. "
        "It's not {chain2:type=ABC rainy}. "
        "{chain1:type=GHI It}'s hot"
    )
    converter = Sacr2AnnConverter(type_property_name="type")
    converter.convert(text)

    assert converter.text == "hello world! It's sunny. It's not rainy. It's hot"

    ann = converter.annotations
    assert len(ann) == 6
    assert ann[0] == TextAnnotation(index=1, kind="ABC", start=6, end=11)
    assert ann[1] == TextAnnotation(index=2, kind="DEF", start=16, end=17)
    assert ann[2] == TextAnnotation(index=3, kind="ABC", start=34, end=39)
    assert ann[3] == RelationAnnotation(
        index=1, kind=DEFAULT_RELATION_TYPE, source=ann[1], target=ann[2]
    )
    assert ann[4] == TextAnnotation(index=4, kind="GHI", start=41, end=43)
    assert ann[5] == RelationAnnotation(
        index=2, kind=DEFAULT_RELATION_TYPE, source=ann[0], target=ann[4]
    )


def test_sacr2ann_2_annotations_in_2_paragraphs_in_2_chains() -> None:
    text = (
        "hello {chain1:a=1,b=2,type=ABC world}!\n\n\n\n" "It'{chain2:type=DEF s} sunny"
    )
    converter = Sacr2AnnConverter(type_property_name="type")
    converter.convert(text)

    assert converter.text == "hello world!\n\nIt's sunny"

    ann = converter.annotations
    assert len(ann) == 2
    assert ann[0] == TextAnnotation(index=1, kind="ABC", start=6, end=11)
    assert ann[1] == TextAnnotation(index=2, kind="DEF", start=17, end=18)


def test_sacr2ann_3_annotations_in_3_paragraphs_in_3_chains() -> None:
    text = (
        "hello {chain1:a=1,b=2,type=ABC world}!\n\n\n\n"
        "It'{chain2:type=DEF s} sunny.\n\n"
        "It's not {chain3:type=ABC rainy}"
    )
    converter = Sacr2AnnConverter(type_property_name="type")
    converter.convert(text)

    assert converter.text == "hello world!\n\nIt's sunny.\n\nIt's not rainy"

    ann = converter.annotations
    assert len(ann) == 3
    assert ann[0] == TextAnnotation(index=1, kind="ABC", start=6, end=11)
    assert ann[1] == TextAnnotation(index=2, kind="DEF", start=17, end=18)
    assert ann[2] == TextAnnotation(index=3, kind="ABC", start=36, end=41)


def test_sacr2ann_2_nested_annotations() -> None:
    text = "{c1:type=ABC {c1:type=DEF abc} def} ghi jkl mno"
    converter = Sacr2AnnConverter(type_property_name="type")
    converter.convert(text)

    assert converter.text == "abc def ghi jkl mno"

    ann = converter.annotations
    assert len(ann) == 3
    assert ann[0] == TextAnnotation(index=1, kind="ABC", start=0, end=7)
    assert ann[1] == TextAnnotation(index=2, kind="DEF", start=0, end=3)
    assert ann[2] == RelationAnnotation(
        index=1, kind=DEFAULT_RELATION_TYPE, source=ann[0], target=ann[1]
    )


def test_sacr2ann_3_nested_annotations() -> None:
    text = "{c1:type=ABC {c1:type=DEF abc def {c1:type=GHI ghi}}} jkl mno"
    converter = Sacr2AnnConverter(type_property_name="type")
    converter.convert(text)

    assert converter.text == "abc def ghi jkl mno"

    ann = converter.annotations
    assert len(ann) == 5
    assert ann[0] == TextAnnotation(index=1, kind="ABC", start=0, end=11)
    assert ann[1] == TextAnnotation(index=2, kind="DEF", start=0, end=11)
    assert ann[2] == RelationAnnotation(
        index=1, kind=DEFAULT_RELATION_TYPE, source=ann[0], target=ann[1]
    )
    assert ann[3] == TextAnnotation(index=3, kind="GHI", start=8, end=11)
    assert ann[4] == RelationAnnotation(
        index=2, kind=DEFAULT_RELATION_TYPE, source=ann[1], target=ann[3]
    )


def test_sacr2ann_annotations_with_leading_comments() -> None:
    text = "# my comment\n\n# my other comment\n\n\n" "abc {c1 def}\n\n" "{c2 ghi}"
    converter = Sacr2AnnConverter(type_property_name="type")
    converter.convert(text)

    assert converter.text == "abc def\n\nghi"

    ann = converter.annotations
    assert len(ann) == 2
    assert ann[0] == TextAnnotation(index=1, kind=DEFAULT_MENTION_TYPE, start=4, end=7)
    assert ann[1] == TextAnnotation(index=2, kind=DEFAULT_MENTION_TYPE, start=9, end=12)


def test_sacr2ann_annotations_with_middle_comments() -> None:
    text = (
        "# my comment\n\n# my other comment\n\n\n"
        "abc {c1 def}\n\n"
        "# the middle comment\n\n"
        "{c2 ghi}"
    )
    converter = Sacr2AnnConverter(type_property_name="type")
    converter.convert(text)

    assert converter.text == "abc def\n\nghi"

    ann = converter.annotations
    assert len(ann) == 2
    assert ann[0] == TextAnnotation(index=1, kind=DEFAULT_MENTION_TYPE, start=4, end=7)
    assert ann[1] == TextAnnotation(index=2, kind=DEFAULT_MENTION_TYPE, start=9, end=12)


def test_sacr2ann_annotations_with_trailing_comments() -> None:
    text = (
        "# my comment\n\n# my other comment\n\n\n"
        "abc {c1 def}\n\n"
        "# the middle comment\n\n"
        "{c2 ghi}\n\n"
        "# end of text"
    )
    converter = Sacr2AnnConverter(type_property_name="type")
    converter.convert(text)

    assert converter.text == "abc def\n\nghi\n\n"

    ann = converter.annotations
    assert len(ann) == 2
    assert ann[0] == TextAnnotation(index=1, kind=DEFAULT_MENTION_TYPE, start=4, end=7)
    assert ann[1] == TextAnnotation(index=2, kind=DEFAULT_MENTION_TYPE, start=9, end=12)


def test_sacr2ann_annotations_with_spaces() -> None:
    text = "# my comment\n\n# my other comment\n\n\n" "  abc  {c1 def  ghi}"
    converter = Sacr2AnnConverter(type_property_name="type")
    converter.convert(text)

    assert converter.text == "  abc  def  ghi"

    ann = converter.annotations
    assert len(ann) == 1
    assert ann[0] == TextAnnotation(index=1, kind=DEFAULT_MENTION_TYPE, start=7, end=15)


def test_sacr2ann_type_property_name() -> None:
    text = "abc {c1:type=foo def}"
    converter = Sacr2AnnConverter(type_property_name="type")
    converter.convert(text)

    assert converter.text == "abc def"

    ann = converter.annotations
    assert len(ann) == 1
    assert ann[0] == TextAnnotation(index=1, kind="foo", start=4, end=7)


def test_convert_annotations() -> None:
    text = "hello world! It's sunny. It's not rainy. It's hot"

    annotations: list[Annotation] = []
    annotations.append(TextAnnotation(index=1, kind="ABC", start=6, end=11))
    annotations.append(TextAnnotation(index=2, kind="DEF", start=16, end=17))
    annotations.append(TextAnnotation(index=3, kind="ABC", start=34, end=39))
    annotations.append(
        RelationAnnotation(
            index=1,
            kind=DEFAULT_RELATION_TYPE,
            source=annotations[1],
            target=annotations[2],
        )
    )
    annotations.append(TextAnnotation(index=4, kind="GHI", start=41, end=43))
    annotations.append(
        RelationAnnotation(
            index=2,
            kind=DEFAULT_RELATION_TYPE,
            source=annotations[0],
            target=annotations[4],
        )
    )

    string = Sacr2AnnConverter._convert_annotations_as_string(text, annotations)
    assert string == (
        "T1\tABC 6 11\tworld\n"
        "T2\tDEF 16 17\ts\n"
        "T3\tABC 34 39\trainy\n"
        f"R1\t{DEFAULT_RELATION_TYPE} Arg1:T2 Arg2:T3\n"
        "T4\tGHI 41 43\tIt\n"
        f"R2\t{DEFAULT_RELATION_TYPE} Arg1:T1 Arg2:T4\n"
    )
