r"""
Convert a CoNLL-2012 or CoNLL-U file in a SACR file, which you can
open with the SACR program (http://boberle.com/projects/sacr).  In this way,
you can check and edit coreference annotation.  To convert back, use the
`sacr2conll.py` script.

To convert from conll-2012 (space separated columns, word column is 3):

    python3 conll2sacr.py --output-dir DIR INPUT_FILE.conll

This will convert every document in `INPUT_FILE.conll` into a document in `DIR`
(the name of the file is based on the document name in the conll file).

To convert from conll-u (tabulation separated columns, word column is 1):

    python3 conll2sacr.py --output-dir DIR \
        --tab \
        --token-col 1 \ 
        INPUT_FILE.conll

Use the `--ignore-double-indices` if you want to ignore French amalgams
(`du -> de le`) decomposed by some corpora and software (such as StanfordNLP).
"""


import re
import argparse
import os

import conll_transform
from standoff2inline import Standoff2Inline

def convert(doc, doc_key, dpath, token_col):

    res = ""

    for sent in doc:
        inliner = Standoff2Inline(kind='sacr')
        mentions = conll_transform.compute_mentions([t[-1] for t in sent])
        for (start, stop), chain in mentions:
            inliner.add((start, (f"C{chain}", dict())), stop-1)
        res += inliner.apply(tokens=[t[token_col] for t in sent])
        res += "\n\n"

    if not isinstance(doc_key, str):
        doc_key = "_".join(str(x) for x in doc_key)
    fname = re.sub(r'[^-\w.]', r'_', doc_key)
    fpath = os.path.join(dpath, fname)
    open(fpath, 'w').write(res)


def parse_args():
    # definition
    parser = argparse.ArgumentParser(prog="conll2sacr",
        #description="convert conll to sacr",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    # arguments (not options)
    parser.add_argument("infpath", default="", help="input file")
    #parser.add_argument("outfpath", default="", help="output file")
    # options
    parser.add_argument("--output-dir", dest="outdpath", required=True,
        help="output directory")
    parser.add_argument("--token-col", dest="token_col", type=int,
        default=3, help="col index for tokens, def 3")
    parser.add_argument("--ignore-double-indices", dest="ignore_double_indices",
        type=int, default=None,
        help="ignore line containing a hyphen in the given column")
    parser.add_argument("--tab", dest="tab_sep", default=False,
       action="store_true", help="use tabulation as separator (conllu)")
    # reading
    args = parser.parse_args()
    return args



def main():

    args = parse_args()

    docs = conll_transform.read_file(
        args.infpath,
        sep="\t" if args.tab_sep else None,
        ignore_double_indices=args.ignore_double_indices,
    )
    for doc_key, doc in docs.items():
        print(f"Doing {doc_key}")
        convert(doc=doc, doc_key=doc_key, dpath=args.outdpath,
            token_col=args.token_col)


if __name__ == '__main__':
    main()
