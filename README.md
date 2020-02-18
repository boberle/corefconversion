# Conversion Scripts for Coreference

This repository contains conversion scripts for coreference.

## `text2jsonlines.py`

Script to convert a plain text to a jsonlines format (used for example for [cofr](https://github.com/boberle/cofr)).  It tokenizes the text with [StanfordNLP](https://github.com/stanfordnlp/stanfordnlp).

```
python3 text2jsonlines.py <plain.txt> -o <output.jsonlines>
```


## License

All the scripts are distributed under the terms of the Mozilla Public Licence 2.0.

