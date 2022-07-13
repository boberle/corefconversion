"""
Convert a SACR file (http://boberle.com/projects/sacr) to a conll file.  The
conll format produced is tabulation separated with three columns: index, word
and coreference.

To convert:

    python3 sacr2conll.py -o OUTPUT.conll INPUT.sacr

You can specify the document name (or key) with the `--docname` option.
Otherwise, it will be `#textid`, if any, otherwise the file name.

With the --speaker switch, you can add a 4th column, which will be placed
before the coreference columns.  In the SACR file, the speaker can be mentionned
as a comment prefixed with `#speaker:` before each line, like this:

    #title: Lucian, Dialogues of the Dead, 4: Hermes and Charon

    #speaker: Hermes
    Ferryman, what do you say to settling up accounts? It will prevent any
    unpleasantness later on.

    #speaker: Charon
    Very good. It does save trouble to get these things straight.

You can remove the speaker for a paragraph by setting:

    #speaker:
    ... the text of the narrator ...
"""


import os
import argparse
import re

import sacr_parser

__version__ = "1.0.0"


def read_file(fpath, index, docname=None, part_is_index=True, include_speaker=False):

    parser = sacr_parser.SacrParser(
        fpath=fpath,
        tokenization_mode=sacr_parser.WORD_TOKENIZATION,
    )

    tokens = []
    starts = dict()  # start -> {ids}
    ends = dict()  # end -> {ids}
    sentences = set()  # index of last tokens

    filo = []

    textid = None
    speaker = ""

    for item, params in parser.parse():

        if item == "text_id":
            textid = params

        elif item in ("par_start", "par_end", "sentence_change"):
            if tokens:
                sentences.add(len(tokens))

        elif item == "mention_start":
            chain = params[0]
            l = len(tokens)
            if l not in starts:
                starts[l] = []
            starts[l].append(chain)
            filo.append(chain)

        elif item == "comment":
            if params.startswith("speaker:"):
                speaker = params[8:].strip().replace(" ", "_")

        elif item == "mention_end":
            chain = filo.pop()
            l = len(tokens) - 1
            if l not in ends:
                ends[l] = []
            ends[l].append(chain)

        elif item == "token":
            tokens.append((params, speaker))

    lines = []

    counter = 0
    for i, (token, speaker) in enumerate(tokens):
        if i in sentences:
            lines.append("")
            counter = 0
        corefcol = "_".join(
            # ["(%d)" % x for x in (starts[i]
            #  if (i in starts and i in ends) else [])]
            # + ["(%d" % x for x in (starts[i]
            ["(%d" % x for x in (starts[i] if i in starts else [])]
            + ["%d)" % x for x in (ends[i] if i in ends else [])]
        )
        corefcol = re.sub(r"\((\d+)_\1\)", r"(\1)", corefcol)
        if not corefcol:
            corefcol = "-"
        if include_speaker:
            cols = [str(counter), token, speaker, corefcol]
        else:
            cols = [str(counter), token, corefcol]
        lines.append("\t".join(cols))
        counter += 1

    if not docname:
        docname = textid if textid else os.path.basename(fpath)
    res = "#begin document (%s); part %03d\n" % (docname, index if part_is_index else 0)
    res += "\n".join(lines)
    res += "\n#end document\n"
    return res


def parse_args():
    # definition
    parser = argparse.ArgumentParser(
        prog="sacr2conll",
        # description="convert sacr files to conll file",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # arguments (not options)
    parser.add_argument("infpaths", nargs="+", help="input files")
    # options
    parser.add_argument(
        "-o", dest="outfpath", default="", help="output file, default is stdout"
    )
    parser.add_argument(
        "-n",
        "--docname",
        dest="docname",
        default="",
        help="document name; otherwise #textid; otherwise file name",
    )
    parser.add_argument(
        "-i",
        "--index",
        dest="part_is_index",
        default=False,
        action="store_true",
        help="document part is file index (otherwise the part is 0; "
        "this is implied by --docname",
    )
    parser.add_argument(
        "-s",
        "--speaker",
        default=False,
        action="store_true",
        help="include a column 'speaker' before the coref column",
    )
    # special options
    parser.add_argument(
        "--version", action="version", version="%(prog)s " + __version__
    )
    # reading
    args = parser.parse_args()
    # check
    if args.docname:
        args.part_is_index = True
    return args


def main():
    args = parse_args()
    res = []
    for i, fpath in enumerate(args.infpaths):
        res.append(
            read_file(
                fpath, index=i, docname=args.docname, part_is_index=args.part_is_index, include_speaker=args.speaker
            )
        )
    res = "\n\n".join(res)
    if args.outfpath:
        open(args.outfpath, "w").write(res)
    else:
        print(res)


if __name__ == "__main__":
    main()
