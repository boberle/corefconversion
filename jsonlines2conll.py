"""Script to convert a jsonlines file to a CoNLL file.

Use the `-h` and `--help` switches to get detailed help on the options.

Example command (output uses spaces):

    python3 jsonlines2conll.py -g testing/singe.jsonlines -o ouput.conll

    #begin document (ge/articleswiki_singe.xml); part 000
    Singe   (0)

             Les         (0
          singes         0)
            sont          -
             des         (0
      mammifères          -
              de          -
              l'         (1
           ordre          -
             des          -
              de          -
             les         (2
        primates      1)|2)
    ...
    #end document


Example command (merging coreference information with an existing conll
file, for example to add predicted coreference):

    python3 jsonlines2conll.py -g testing/singe.jsonlines -o ouput.conll \
        -c testing/singe.conll

    #begin document (ge/articleswiki_singe.xml); part 000
    1   Singe   Singe   NOUN   ...

       1            Les             le     DET   ...
       2         singes          singe    NOUN   ...
       3           sont           être     AUX   ...
       4            des             un     DET   ...
       5     mammifères      mammifère    NOUN   ...
       6             de             de     ADP   ...
       7             l'             le     DET   ...
       8          ordre          ordre    NOUN   ...
    9-10            des              _       _   ...
       9             de             de     ADP   ...
      10            les             le     DET   ...
      11       primates        primate    NOUN   ...
    ...
    #end document


Example command (merging + output uses tabulation):

    python3 jsonlines2conll.py -g testing/singe.jsonlines -o ouput.conll -c testing/singe.conll -T
"""

import argparse
import json

import conll_transform


def jsonlines2conll(*fpaths, cols=None, predicted_clusters=True,
        merge_with=None, outfpath=None, tabsep=False):

    if cols is None:
        cols = ['sentences']

    docs = dict()

    for line in (l for fpath in fpaths for l in open(fpath)):

        data = json.loads(line)
        doc_key = data["doc_key"]

        sents = [
            # token is just right: a tuple of col
            [list(token) for token in zip(*sent)]
            # sent is: [ sent1_tokens, sent2_speakers,... ]
            for sent in zip(*[iter(data[col]) for col in cols])
        ]

        chains = data['predicted_clusters'
            if predicted_clusters else 'clusters']

        mentions = [ m for chain in chains for m in chain ]
        conll_transform.textpos2sentpos(mentions, sents)

        conll_transform.write_chains(sents, chains, append=True)

        docs[doc_key] = sents

    if merge_with:
        conll_transform.replace_coref_col(docs, merge_with)
        docs = merge_with

    if outfpath:
        conll_transform.write_file(outfpath, docs, sep="\t" if tabsep else None)

    return docs


def parse_args():
    # definition
    parser = argparse.ArgumentParser(prog="jsonlines2conll",
        description="convert jsonlines to conll",
        #description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    # arguments (not options)
    parser.add_argument("infpaths", nargs="+", help="input files")
    # options
    parser.add_argument("-g", "--gold", dest="gold_clusters",
        default=False, action="store_true",
        help="use gold clusters instead of predicted clusters")
    parser.add_argument("-t", "--in-tab-sep", dest="intabsep",
        default=False, action="store_true",
        help="input conll files use tab as separator")
    parser.add_argument("-T", "--out-tab-sep", dest="outtabsep",
        default=False, action="store_true",
        help="output conll files use tab as separator")
    parser.add_argument("-o", dest="outfpath", required=True,
        help="output file")
    parser.add_argument("-c", "--conll", dest="conll_files", action="append",
        default=[],
        help="conll files to merge with, may be repeated")
    parser.add_argument("--cols", dest="cols", default='sentences',
        help="comma separated list of cols to include, in order "
        "(default: 'sentences')")
    # reading
    args = parser.parse_args()
    return args


def main():

    args = parse_args()

    if args.conll_files:
        merge_with = conll_transform.read_files(*args.conll_files,
            sep="\t" if args.intabsep else None)
    else:
        merge_with = None

    jsonlines2conll(
        *args.infpaths,
        outfpath=args.outfpath,
        predicted_clusters=not args.gold_clusters,
        merge_with=merge_with,
        cols=args.cols.split(','),
        tabsep=args.outtabsep,
    )
        

if __name__ == '__main__':
    main()

