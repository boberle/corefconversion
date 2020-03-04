"""Convert plain text to jsonlines.  The jsonlines format stores data for
several texts (a corpus).  Each line is a valid json document, as follows:

    {
      "clusters": [],
      "doc_key": "nw:docname",
      "sentences": [["This", "is", "the", "first", "sentence", "."],
                    ["This", "is", "the", "second", "."]],
      "speakers":  [["spk1", "spk1", "spk1", "spk1", "spk1", "spk1"],
                    ["spk2", "spk2", "spk2", "spk2", "spk2"]]
      "pos":       [["DET", "V", "DET", "ADJ", "NOUN", "PUNCT"],
                    ["DET", "V", "DET", "ADJ", "PUNCT"]],
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
import re

import stanfordnlp
from stanfordnlp.models.common.conll import CoNLLFile

# download French models:
#stanfordnlp.download('fr')


def tokenize(fpath, lang):

    content = open(fpath).read()
    paragraphs = re.split(r'\n+', content)
    res_sents = []
    res_pars = []
    res_pos = []
    start_par = 0
    for par in paragraphs:
        par = par.strip()
        if not par:
            continue
        doc = stanfordnlp.Document(par)
        nlp = stanfordnlp.Pipeline(lang=lang, processors="tokenize,mwt,pos")
        doc = nlp(doc)
        #print(doc.conll_file.conll_as_string())
        #print(doc.conll_file.sents)
        sents = [
            [ token[1] for token in sent if '-' not in token[0] ]
            for sent in doc.conll_file.sents
        ]
        pos = [
            [ token[3] for token in sent if '-' not in token[0] ]
            for sent in doc.conll_file.sents
        ]
        res_sents.extend(sents)
        res_pos.extend(pos)
        length = sum((len(s) for s in sents))
        res_pars.append([start_par, start_par+length-1])
        start_par = start_par+length
    return res_sents, res_pos, res_pars


def make_jsonlines(sents, pos, pars, fpath, genre):
    doc = dict(
        doc_key = f"{genre[:2]}:{fpath}",
        sentences = sents,
        speakers = [ [ "_" for tok in sent ] for sent in sents ],
        clusters = [],
        pos = pos,
        paragraphs = pars,
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
    parser.add_argument("--lang", dest="lang", default="en",
        help="lang: en, fr, etc. (default is 'en')")
    parser.add_argument("-o", dest="outfpath", required=False,
        default=None, help="output file (default to stdout)")
    # reading
    args = parser.parse_args()
    return args



def main():
    args = parse_args()
    sents, pos, pars = tokenize(args.infpath, lang=args.lang)
    if args.export_conll:
        code = make_conll(sents, fpath=args.infpath, genre=args.genre)
    else:
        code = make_jsonlines(sents, pos, pars,
            fpath=args.infpath, genre=args.genre)
    if args.outfpath:
        open(args.outfpath, 'w').write(code + "\n")
    else:
        print(code)



if __name__ == '__main__':
    main()
