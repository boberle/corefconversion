"""
Converting standoff annotations to inline annotations.

For example, in the sentence:

    The little cat drinks milk.

you know that the third word, between the 12th and 14th characters, is a noun.
You may want to surround it with some tags, like `<noun>` and `</noun>`:

    The little <noun>cat</noun> drinks milk.

This module offer classes and function to:
* add inline annotations, like xml annotations, counting in characters or
  tokens,
* highlight some chunks of text, for example with styled `<span>` tags,
* remove parts without annotations and replace them with something like
  `[...]`.

A quick preview:

```python
from standoff2inline import Standoff2Inline

string = "The little cat drinks milk."
inliner = Standoff2Inline()
inliner.add((0, "<sent>"), (26, "</sent>"))
inliner.add((0, "<gn>"), (13, "</gn>"))
inliner.add((11, "<noun>"), (13, "</noun>"))
inliner.add((22, "<noun>"), (25, "</noun>"))
inliner.add((0, "<det>"), (2, "</det>"))
inliner.apply(string)
```

which gives:

```
<sent><gn><det>The</det> little <noun>cat</noun></gn> drinks
<noun>milk</noun>.</sent>
```

Please read the user guide and play with the module in the Jupyter notebook.

************************************************************************

(c) Bruno Oberle 2019 - boberle.com

Distributed under the term of the Mozilla Public License 2.  See the LICENSE
file.

Version 1.0.0

"""



class Standoff2Inline:
    """Conversion from standoff annotation to inline annotations.

    Constructor:
    * `kind` (opt): one of `xml|sacr`: predefined annotation scheme.
    * `end_is_stop`: the "end" position is the position of the next token or
       character, not the last.
    """


    def __init__(self, kind=None, end_is_stop=False):
        self.kind = kind
        self._elements = []
        self._sorted = False
        self.end_is_stop = end_is_stop



    def add(self, start, end=None, stop=None):
        """Add an annotation.

        Annotations are given as a tuple `(position, string)`, where position
        may be in characters or tokens.

        The `start` annotation is required, `end|stop` annotation is optional.

        You give either an `end` or `stop` annotation.  `stop` works like
        Python's `range` function: the annotation is introduced *before* the
        next element.
        """

        if stop is not None:
            if isinstance(stop, int):
                stop = (stop, None)
            stop, value = stop
            end = (stop-1, value)
        if isinstance(end, int):
            end = (end, None)
        if end is None:
            end = (-1, None)
        self._elements.append((start, end))
        self._sorted = False



    def _iter_elements(self, elements):
        if self.kind is None:
            yield from self._get_strings(elements)
        elif self.kind == 'xml':
            yield from self._get_xml_strings(elements)
        elif self.kind == 'sacr':
            yield from self._get_sacr_strings(elements)
        else:
            assert False, self.kind



    def _get_xml_strings(self, elements):
        for (start, start_val), (end, end_val) in elements:
            if isinstance(start_val, str):
                tagname, dic = start_val, dict()
            else:
                tagname, dic = start_val
            attrs = " ".join('%s="%s"' % (k, v) for k, v in dic.items())
            if attrs:
                attrs = " " + attrs
            start_val = "<%s%s>" % (tagname, attrs)
            end_val = "</%s>" % tagname
            yield (start, start_val), (end, end_val)



    def _get_sacr_strings(self, elements):
        for (start, start_val), (end, end_val) in elements:
            tagname, dic = start_val
            attrs = " ".join('%s="%s"' % (k, v) for k, v in dic.items())
            if attrs:
                attrs = ":" + attrs
            start_val = "{%s%s " % (tagname, attrs)
            end_val = "}"
            yield (start, start_val), (end, end_val)



    def _get_strings(self, elements):
        for (start, start_val), (end, end_val) in elements:
            if end_val is None:
                end_val = ""
            yield (start, start_val), (end, end_val)



    def _tokens2string(self, tokens):
        """Convert a list of tokens into a string and compute new positions.

        Return a tuple `(string, elements)`, where `elements` is like
        `self.elements`, but with position in the string rather than in the
        token list.
        """

        string = ""
        t2s = []
        for i, token in enumerate(tokens):
            start = len(string)
            t2s.append((start, start+len(token)-1))
            string += token + " "
        elements = []
        for (start, start_val), (end, end_val) in self._elements:
            start = t2s[start][0]
            end = t2s[end][1]
            elements.append(((start, start_val), (end, end_val)))
        return string, elements



    def apply(self, string=None, tokens=None):
        """Insert the annotations and return a string with inline annotations.

        Specify either a `string` or a list of `tokens`.
        """

        return "".join(
            x[1] for x in self.iter_result(string=string, tokens=tokens))



    def iter_result(self, string=None, tokens=None, return_tokens=False):
        """Iterate over `prefix|string|suffix`.

        Each iteration yields a tuple `(kind, string)` where `kind` is one of
        `prefix|string|suffix` and `string` is either the annotation value or
        a chunk of text.
        """

        assert string or tokens and not (string and tokens)
        def yield_(k, v):
            if len(v):
                yield k, v
        if not self._sorted:
            self._elements.sort(key=lambda e: e[1][0], reverse=True)
            self._elements.sort(key=lambda e: e[0][0])
            self._sorted = True
        if tokens and not return_tokens:
            string, elements = self._tokens2string(tokens)
        else:
            elements = self._elements
        res = ""
        pos = 0
        filo = []
        move_one = 0 if self.end_is_stop else 1
        for (start, start_val), end_data in self._iter_elements(elements):
            while filo and filo[-1][0] < start:
                end, end_val = filo.pop()
                if tokens and return_tokens:
                    yield from yield_('string', tokens[pos:end+move_one])
                else:
                    yield from yield_('string', string[pos:end+move_one])
                pos = end + move_one
                yield 'suffix', end_val
            if tokens and return_tokens:
                yield from yield_('string', tokens[pos:start])
            else:
                yield from yield_('string', string[pos:start])
            yield 'prefix', start_val
            pos = start
            if end_data[0] != -1:
                filo.append(end_data)
        while filo:
            end, end_val = filo.pop()
            if tokens and return_tokens:
                yield from yield_('string', tokens[pos:end+move_one])
            else:
                yield from yield_('string', string[pos:end+move_one])
            pos = end + move_one
            yield from yield_('suffix', end_val)
        if tokens and return_tokens:
            yield from yield_('string', tokens[pos:])
        else:
            yield from yield_('string', string[pos:])
        return res



class Highlighter:


    def __init__(self, marks=None, prefix=None, suffix=None):
        self.marks = marks if marks is not None else list()
        self.prefix = prefix
        self.suffix = suffix


    def _get_affix(self, current, value):
        if current is None:
            return value
        if isinstance(current, list):
            current.append(value)
            return current
        return [current, value]


    def set_style(self, underline=False, bold=False, italic=False,
            color=None):
        res = ""
        if underline:
            res += "text-decoration: underline; "
        if bold:
            res += "font-weight: bold; "
        if italic:
            res += "font-style: italic; "
        if color is not None:
            res += "color: %s; " % color
        if res:
            self.prefix = '<span style="%s">%s' % (
                res, self.prefix if self.prefix else "")
            self.suffix = '%s</span>' % (self.suffix if self.suffix else "")


    def add_mark(self, start, end, prefix=None, suffix=None):
        self.marks.append((start, end))
        if prefix is not None:
            self.prefix = self._get_affix(self.prefix, prefix)
        if suffix is not None:
            self.suffix = self._get_affix(self.suffix, suffix)


    def add_marks(self, marks):
        for start, end in marks:
            self.add_mark(start, end)



def highlight_characters(text, *highlighters, end_is_stop=False):
    inliner = Standoff2Inline(end_is_stop=end_is_stop)
    for hl in highlighters:
        for i in range(len(hl.marks)):
            start, end = hl.marks[i]
            prefix = hl.prefix[i] if isinstance(hl.prefix, list) else hl.prefix
            suffix = hl.suffix[i] if isinstance(hl.suffix, list) else hl.suffix
            inliner.add(
                (start, prefix),
                (end, suffix),
            )
    return inliner.apply(text)



def highlight(text, *highlighters, margin=0, max_gap=0, ellipsis=" [...] ",
        char=False, end_is_stop=False):
    inliner = Standoff2Inline(end_is_stop=end_is_stop)
    for hl in highlighters:
        for i in range(len(hl.marks)):
            start, end = hl.marks[i]
            prefix = hl.prefix[i] if isinstance(hl.prefix, list) else hl.prefix
            suffix = hl.suffix[i] if isinstance(hl.suffix, list) else hl.suffix
            inliner.add(
                (start, prefix),
                (end, suffix),
            )
    #return inliner.apply(tokens=text)
    chunks = [
        [a, b] for a, b in inliner.iter_result(
            string=text if char else None,
            tokens=text if not char else None,
            return_tokens=True
        )
    ]
    if not char:
        ellipsis = ellipsis.strip()
    if margin and chunks[0][0] == 'string' and len(chunks[0][1]) > margin:
        chunks[0][1] = [ellipsis] + chunks[0][1][-1*margin:]
    if margin and chunks[-1][0] == 'string' and len(chunks[-1][1]) > margin:
        chunks[-1][1] = chunks[-1][1][:margin] + [ellipsis]
    level = 1 if chunks[0][0] == 'prefix' else 0
    if max_gap:
        for i in range(1, len(chunks)-1):
            kind, string = chunks[i]
            if kind == 'prefix':
                level += 1
                chunks[i][1] = chunks[i][1]
            if kind == 'suffix':
                level -= 1
                chunks[i][1] = chunks[i][1]
            if kind == 'string' and level == 0:
                if len(string) > max_gap:
                    chunks[i][1] = chunks[i][1][:margin] \
                        + [ellipsis] + chunks[i][1][-1*margin:]
    res = ""
    need_space = False
    for kind, chunk in chunks:
        if kind == "string":
            if need_space and not char:
                res += " "
            res += chunk if char else " ".join(chunk)
            need_space = True
        else:
            if kind == "prefix" and need_space and not char:
                res += " "
                need_space = False
            res += chunk
    return res.rstrip()



