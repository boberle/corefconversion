"""Convert plain text to jsonlines.  The jsonlines format stores data for
several texts (a corpus).  Each line is a valid json document, as follows:

    {
      "clusters": [],
      "doc_key": "nw:docname",
      "sentences": [["This", "is", "the", "first", "sentence", "."],
                    ["This", "is", "the", "second", "."]],
      "speakers":  [["spk1", "spk1", "spk1", "spk1", "spk1", "spk1"],
                    ["spk2", "spk2", "spk2", "spk2", "spk2"]]
    }

It is used for some coreference resolution systems, such as:

- https://github.com/kentonl/e2e-coref
- https://github.com/kkjawz/coref-ee
- https://github.com/boberle/cofr

Tokenization is done with StanfordNLP
(https://github.com/stanfordnlp/stanfordnlp) (Qi, Dozat, Zhang, Manning 2018).

You need to install StanfordNLP via pip and then load the models, for example
for French models (use "en" for English models):

    python3 -c "import stanfordnlp; stanfordnlp.download('fr')"

Notes:
- the doc key is the concatenation of `--genre` and the file path,
- speaker data are left blank ("_")
"""

# (C) Bruno Oberle 2020 - Mozilla Public Licence 2.0


import argparse
import json

import stanfordnlp
from stanfordnlp.models.common.conll import CoNLLFile

# download French models:
#stanfordnlp.download('fr')


def tokenize(fpath):
    content = open(fpath).read()
    doc = stanfordnlp.Document(content)
    nlp = stanfordnlp.Pipeline(lang='fr', processors="tokenize,mwt")
    doc = nlp(doc)
    #print(doc.conll_file.conll_as_string())
    #print(doc.conll_file.sents)
    sents = [
        [ token[1] for token in sent if '-' not in token[0] ]
        for sent in doc.conll_file.sents
    ]
    return sents



def make_jsonlines(sents, fpath, genre):
    doc = dict(
        doc_key = f"{genre[:2]}:{fpath}",
        sentences = sents,
        speakers = [ [ "_" for tok in sent ] for sent in sents ],
        clusters = [],
    )
    return json.dumps(doc)



def make_conll(sents, fpath, genre):
    res = f"#begin document {genre[:2]}:{fpath}\n"
    for sent in sents:
        for i, token in enumerate(sent):
            res += f"{i+1}\t{token}\n"
        res += "\n"
    res += "#end document"
    return res



def parse_args():
    # definition
    parser = argparse.ArgumentParser(prog="text2jsonlines",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    # arguments (not options)
    parser.add_argument("infpath", default="", help="input file")
    # options
    parser.add_argument("--conll", dest="export_conll", default=False,
       action="store_true",
       help="export conll and not jsonlines (for debugging)")
    parser.add_argument("--genre", dest="genre", default="ge",
        help="genre (default is 'ge')")
    parser.add_argument("-o", dest="outfpath", required=False,
        default=None, help="output file (default to stdout)")
    # reading
    args = parser.parse_args()
    return args



def main():
    args = parse_args()
    sents = tokenize(args.infpath)
    if args.export_conll:
        code = make_conll(sents, fpath=args.infpath, genre=args.genre)
    else:
        code = make_jsonlines(sents, fpath=args.infpath, genre=args.genre)
    if args.outfpath:
        open(args.outfpath, 'w').write(code + "\n")
    else:
        print(code)



if __name__ == '__main__':
    main()
