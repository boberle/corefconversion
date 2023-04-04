"""
This module offers a parser for the SACR ("Script d'Annotation des Chaînes de
Référence") format.

Synopsis
--------

The parser yields the following elements:
* ('text_id', <TEXT_ID from the directive #textid>)
* ('comment', <COMMENT TEXT, stripped) NOTE: only if there is a text
* ('par_start', None)
* ('par_end', None)
* ('mention_start', (<CHAIN_INDEX>, <CHAIN_NAME>, <FEATURES>))
* ('mention_end', None)
* ('token', <STRING>)
* ('sentence_change', None)

Note that spaces are not yielded as token.

    import sacr_parser
    import annotable

    corpus = annotatble.Corpus()

    for fpath in fpaths:
        parser = sacr_parser.SacrParser(
            fpath=fpath,
            tokenization_mode=sacr_parser.WORD_TOKENIZATION,
        )
        text = annotable.Text(id_=fpath)
        self.corpus.add_text(text)
        for item, params in parser.parse():
            if item == 'text_id':
                text.id_ = params
            elif item == 'par_start':
                ...
            elif item == 'par_end':
                ...
            elif item == 'sentence_change':
                ...
            elif item == 'mention_start':
                ...
            elif item == 'token':
                ...
            elif item == 'mention_end':
                ...
"""

__version__ = "1.0.0"

import re

WORD_TOKENIZATION = 1
CHAR_TOKENIZATION = 2


def escape_regex(string):
    """Escape a string so it can be literally search for in a regex.

    Used for additional_tokens.
    """
    return re.sub(r"([-{}\[\]().])", r"\\\1", string)


class SacrParser:
    """Parse a file in the SACR format.

    Attribute
    ---------
    tokenization_mode: int
        The tokenization mode, use the constants: `WORD_TOKENIZATION` and
        `CHAR_TOKENIZATION`
    fpath: str
        Path of the file to parse.
    """

    @staticmethod
    def get_word_regex(additional_tokens=None):
        """Compute the regex to match words, including additional_tokens."""
        if not additional_tokens:
            addtional_tokens = []
        additional_tokens = sorted(
            [escape_regex(w) for w in additional_tokens], key=lambda x: len(x)
        )
        token_str = "[a-zßàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿœα-ω0-9_]+'?|[-+±]?[.,]?[0-9]+"
        if additional_tokens:
            return re.compile(
                "([%d]+|%s)" % (token_str, "|".join(additional_tokens)), re.I
            )
        else:
            return re.compile("(%s)" % token_str, re.I)

    def __init__(self, fpath, tokenization_mode=WORD_TOKENIZATION):
        self.tokenization_mode = tokenization_mode
        self.fpath = fpath

    def parse(self):
        """Parse the file and yields elements.  See the module description."""
        content = open(self.fpath).read()
        additional_tokens = []
        pos = 0
        chains = dict()
        open_mention_counter = 0
        # patterns:
        additional_tokens_pattern = re.compile(r"#additional_?token:\s*(.+)\s*\n\n+")
        text_id_pattern = re.compile(r"#text_?id:\s*(.+)\s*\n\n*")
        comment_pattern = re.compile(r"(?:#(.*)\n+|\*{5,})")
        end_par_pattern = re.compile(r"\n\n+")
        space_pattern = re.compile(r"\s+")
        new_line_pattern = re.compile(r"\n")
        open_mention_pattern = re.compile(r"\{(\w+)(:| )")
        feature_pattern = re.compile(r'(\w+)=(?:(\w+)|"([^"]*)")(,| )')
        close_mention_pattern = re.compile(r"\}")
        sentence_end_pattern = re.compile(r'(?:\.+"?|\!|\?)')
        if self.tokenization_mode == WORD_TOKENIZATION:
            word_pattern = self.__class__.get_word_regex(additional_tokens)
        else:
            word_pattern = re.compile(r".")
        # eat leading blank lines
        m = re.compile(r"\s+").match(content, pos)
        if m:
            # print('eat leading spaces')
            pos += len(m.group(0))
        while pos < len(content):
            m = additional_tokens_pattern.match(content, pos)
            if m:
                # print('add word')
                pos += len(m.group(0))
                additional_tokens.append(m.group(1))
                word_pattern = SacrParser.get_word_regex(additional_tokens)
                continue
            m = text_id_pattern.match(content, pos)
            if m:
                # print('textid')
                pos += len(m.group(0))
                yield "text_id", m.group(1)
                continue
            m = comment_pattern.match(content, pos)
            if m:
                # print('comment', m.group(0))
                pos += len(m.group(0))
                comment = m.group(1).strip()
                if comment:
                    yield "comment", comment
                continue
            # paragraph of text
            yield "par_start", None
            while pos < len(content):
                # print("%d, %d" % (pos, len(content)))
                # print(content[pos])
                m = end_par_pattern.match(content, pos)
                if m:
                    # print('end par')
                    pos += len(m.group(0))
                    yield "par_end", None
                    break
                m = space_pattern.match(content, pos)
                if m:
                    # print('space')
                    pos += len(m.group(0))
                    continue
                m = new_line_pattern.match(content, pos)
                if m:
                    # print('newline')
                    pos += len(m.group(0))
                    continue
                m = open_mention_pattern.match(content, pos)
                if m:
                    # print('mention')
                    pos += len(m.group(0))
                    open_mention_counter += 1
                    if m.group(1) not in chains:
                        chains[m.group(1)] = len(chains)
                    chain_index = chains[m.group(1)]
                    chain_name = m.group(1)
                    features = dict()
                    if m.group(2) == ":":
                        while pos < len(content):
                            m = feature_pattern.match(content, pos)
                            if m:
                                key = m.group(1)
                                value = m.group(2) if m.group(2) is not None else m.group(3)
                                features[key] = value
                                pos += len(m.group(0))
                                if m.group(4) == " ":
                                    break
                            else:
                                raise SyntaxError(
                                    "can't understand '%s' near %d" % (content, pos)
                                )
                    yield "mention_start", (chain_index, chain_name, features)
                    continue
                m = close_mention_pattern.match(content, pos)
                if m:
                    # print('end mention')
                    pos += len(m.group(0))
                    open_mention_counter -= 1
                    yield "mention_end", None
                    continue
                m = word_pattern.match(content, pos)
                if m:
                    # print('token: %s' % m.group(0))
                    pos += len(m.group(0))
                    yield "token", m.group(0)
                    continue
                if open_mention_counter == 0:
                    m = sentence_end_pattern.match(content, pos)
                    if m:
                        # print('token: %s' % m.group(0))
                        pos += len(m.group(0))
                        yield "token", m.group(0)
                        yield "sentence_change", None
                        continue
                m = re.compile(r".").match(content, pos)
                if m:
                    # print('token: %s' % m.group(0))
                    pos += len(m.group(0))
                    yield "token", m.group(0)
                    continue
                assert False
