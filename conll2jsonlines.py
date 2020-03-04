r"""
Convert conll format (2012 or U or X) into jsonlines format.

The jsonlines format stores data for
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

To convert from the original CoNLL2012 format into jsonlines format:

python3 conll2jsonlines.py \
  --token-col 3 \
  --speaker-col 9 \
  INPUT_FILE \
  OUTPUT_FILE

To convert from the StanfordNLP format into jsonlines format:

python3 conll2jsonlines.py \
  --skip-singletons \
  --skip-empty-documents \
  --tab \
  --ignore-double-indices 0 \
  --token-col 1 \
  --speaker-col "_" \
  --no-coref \
  INPUT_FILE \
  OUTPUT_FILE

To convert from the Democrat corpus in CoNLL format (with a column for
paragraphs at position 11):

python3 conll2jsonlines.py \
  --tab \
  --ignore-double-indices 0 \
  --token-col 1 \
  --speaker-col "_" \
  --par-col 11 \
  testing/singe.conll \
  testing/singe.jsonlines

Note that you may have to change document keys in the CoNLL files before
running this script if you want to transform them.
"""

import json
import os
import argparse

import conll_transform


def conll2jsonlines(
        infpath, outfpath,
        sep=None, token_col=3, speaker_col=9, add_coref=True, par_col=0,
        ignore_double_indices=None,
        skip_empty_documents=False, skip_singletons=False):

    docs = conll_transform.read_files(
        infpath,
        sep=sep,
        ignore_double_indices=ignore_double_indices,
    )

    with open(outfpath, 'w') as fh:

        for doc_key, doc in docs.items():

            print("Doing %s" % doc_key)

            if add_coref:
                clusters = conll_transform.compute_chains(doc)
                clusters = [
                    [ list(mention) for mention in cluster]
                    for cluster in clusters
                ]
                for cluster in clusters:
                    conll_transform.sentpos2textpos(cluster, doc)
                if skip_singletons:
                    clusters = list(filter(lambda c: len(c) > 1, clusters))
                if skip_empty_documents and not clusters:
                    print("Skipping %s because no cluster" % doc_key)
                    continue
            else:
                clusters = []

            tokens = [t for sent in doc for t in sent]

            sentences = [
                [token[token_col] for token in sent] for sent in doc
            ]

            if par_col:
                start = 0
                length = 0
                current = -1
                paragraphs = []
                for sent in doc:
                    length += len(sent)
                    if int(sent[0][par_col]) != current:
                        current = int(sent[0][par_col])
                        paragraphs.append([start, start+length-1])
                        start += length
                        length = 0
            else:
                #paragraphs = [[0, len(tokens)]]
                paragraphs = None

            if speaker_col.isdigit():
                speakers = [
                    [token[int(speaker_col)] for token in sent] for sent in doc
                ]
            else:
                speakers = [
                    [speaker_col for token in sent] for sent in sentences
                ]


            dic = dict(
                doc_key=doc_key,
                clusters=clusters,
                sentences=sentences,
                speakers=speakers,
            )
            if paragraphs is not None:
                dic['paragraphs'] = paragraphs
            fh.write(json.dumps(dic) + "\n")



def parse_args():
    # definition
    parser = argparse.ArgumentParser(prog="conll2jsonlines",
        #description="convert conll file to jsonlines",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    # arguments (not options)
    parser.add_argument("input_fpath", default="", help="input file")
    parser.add_argument("output_fpath", default="", help="output file")
    # options
    parser.add_argument("--skip-singletons", dest="skip_singletons",
        default=False, action="store_true", help="skip singletons")
    parser.add_argument("--skip-empty-documents", dest="skip_empty_documents",
        default=False, action="store_true", help="skip empty documents")
    parser.add_argument("--no-coref", dest="add_coref",
        default=True, action="store_false",
        help="ignore coreference information")
    parser.add_argument("--tab", dest="sep_is_tab",
        default=False, action="store_true",
        help="separator is tab and no a bunch of spaces as in the original "
        "conll 2012 format")
    parser.add_argument("--token-col", dest="token_col", type=int,
        default=3, help="col index for tokens, def 3")
    parser.add_argument("--speaker-col", dest="speaker_col", default="9",
        help="col index for speakers, def 9. Use a char (ex. _) if you want "
        "the speaker col to be filled with that char, eg if there is no "
        "speaker column)")
    parser.add_argument("--ignore-double-indices", dest="ignore_double_indices",
        type=int, default=None,
        help="ignore line containing a hyphen in the given column")
    parser.add_argument("--par-col", dest="par_col", type=int,
        default=0, help="paragraph column, def 0 (= no paragraph information)")
    # reading
    args = parser.parse_args()
    return args



def main():
    args = parse_args()
    conll2jsonlines(
        infpath=args.input_fpath,
        outfpath=args.output_fpath,
        skip_empty_documents=args.skip_empty_documents,
        skip_singletons=args.skip_singletons,
        add_coref=args.add_coref,
        token_col=args.token_col,
        speaker_col=args.speaker_col,
        sep="\t" if args.sep_is_tab else None,
        ignore_double_indices=args.ignore_double_indices,
        par_col=args.par_col,
    )



if __name__ == '__main__':
    main()

