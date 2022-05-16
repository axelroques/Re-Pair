# _Re-Pair_ algorithm

Python implementation of the _Re-Pair_ compression scheme from Larsson and Moffat (1999). This algorithm is loosely related to the grammar-based compression method _Sequitur_ of Nevill-Manning and Witten (1997). However, because Sequitur processes the message in a left-to-right manner and maintains its two invariants (uniqueness and utility) at all times, it does not necessarily choose as grammar rules the phrases that might eventually lead to the most compact representation.

_Re-Pair_ is acombination of a simple but powerful offline phrase derivation method and a compact dictionary encoding. The goal of dictionary-based modeling is to derive a set of phrases in such a way that replacing the occurrences of these phrases in the message with references to the table of phrases decreases the length of the message.

The phrase derivation algorithm consists of replacing the most frequent pair of symbols in the source message by a new symbol, reevaluating the frequencies of all of the symbol pairs with respect to the now-extended alphabet and then repeating the process until there is no pair of adjacent symbols that occurs twice.
Therefore, every phrase is used either to directly code at least two distinct parts of the source message or as a building block of a longer phrase that is itself used twice or more.

Note that we have not specified in which order pairs should be scheduled for replacement when there are several pairs of equal maximum frequency. While this does influence the outcome of the algorithm, in general it appears to be of minor importance.

---

## Requirements

**Mandatory**:

- numpy
- pandas

**Optional**:

- pydot

---

## Examples

Process a string.

```python
s = 'singing.do.wah.diddy.diddy.dum.diddy.do'
phrases = RePair(s)
```

Display the resulting phrases.

```python
phrases.get_results()
```

Generate a .dot file and .png. file with the containing the hierarchy of the resulting phrases. Requires the pydot module (https://pypi.org/project/pydot/).

```python
phrases.get_hierarchy()
```
