
from .tree.tree import compute_hierarchy

from collections import defaultdict
import pandas as pd
import numpy as np
import re


class Phrase:
    """
    Phrase instance.
    """

    def __init__(self, phrase):

        # Basic parameters
        self.n = len(phrase)
        self.raw = [frozenset([c]) for c in phrase]

        # Phrase construction parameters
        self.phrase = ' '.join(c for c in phrase)
        self.symbol = 1

        # Digram generation
        self.generate_digrams()

        # Hash table generation
        self.generate_hash_tables()

    def generate_digrams(self):
        """
        Create digram instances.
        """

        self.digrams = [Digram(i, c1, c2)
                        for i, (c1, c2)
                        in enumerate(zip(self.raw[:-1],
                                         self.raw[1:]))]

        return

    def generate_hash_tables(self):
        """
        Builds hash tables for the positions and counts of 
        the occurrences.
        """

        positions = defaultdict(list)
        counts = defaultdict(int)

        for digram in self.digrams:

            positions[str(digram)].append(digram.pos)
            counts[str(digram)] += 1

        self.positions = positions
        self.counts = counts

        return

    def update_positions(self, helper):
        """
        Updates the positions of the digrams using the 
        helper vector.
        """

        for i_help, digram in enumerate(self.digrams):
            digram.pos -= helper[i_help]

        return

    def compute_results(self, data):
        """
        Expands the rules for better readability.
        """

        # Retrieve pairs from the results
        pairs = data['Rule'][1:]

        # Expand the rules
        expanded_rules = []
        for pair in pairs:

            # Iterate over the symbols in the pair
            symbols = []
            for symbol in pair.split(' '):

                # If that symbol contains a number, expand
                # that rule using the expanded version
                # of the rule at that number
                match = re.findall('[1-9][0-9]*', symbol)
                if match:
                    symbols.append(expanded_rules[int(match[0])-1])
                else:
                    symbols.append(symbol)

            expanded_rules.append(' '.join(symbol for symbol in symbols))

        self.results = data
        self.results['Expanded Rule'] = [''] + expanded_rules

        return

    def get_results(self):
        """
        Returns a pandas DataFrame with the grammar rules.
        """

        return pd.DataFrame({
            'Rule': self.results['Rule'],
            'Expanded Rule': self.results['Expanded Rule'],
            'Occurrence': self.results['Occurrence'],
            'Phrase': self.results['Phrase']
        }, index=self.results['index'])

    def get_hierarchy(self):
        """
        Uses a tree to compute the hierarchy in the compression
        rules. The output is a file called hierarchy.dot
        """

        compute_hierarchy(self.results)

        return


class Digram:
    """
    Digram instance.
    """

    def __init__(self, i, c1, c2):

        # Digram parameters
        self.pos = i
        self.c1 = c1
        self.c2 = c2

    def __str__(self) -> str:
        return f'{list(self.c1)[0]} {list(self.c2)[0]}'


def initialize_data_structures(phrase):
    """
    From the input phrase, builds a hash table that contains
    the occurrences of each digram (position and count).
    """

    return Phrase(phrase)


def most_reccuring_pair(phrase):
    """
    Finds the most reccurring pair.
    """

    pair = max(phrase.counts, key=phrase.counts.get)

    return pair, phrase.counts[pair]


def prune_positions(positions):
    """
    # Get a true vector of positions
    # i.e. 'aaaa' should return positions (0, 2) and not (0, 1, 2)

    # This part is probably not well optimized, there should be a better
    # solution
    """

    # Problematic positions are the ones that are successive
    # We identify successive values as '1's in diff
    diff = np.diff(positions)

    # Create a string with the positions in diff
    string = ''.join([str(d) if d == 1 else '0' for d in diff])

    # Use regex to find all successions of '1's
    reg = [m.span() for m in re.finditer('11*', string)]

    # If there are problematic positions
    if reg:

        # Non problematic positions
        good_positions = positions[np.where(diff != 1)[0]+1]

        # Return one indice out of two for successive indices
        # Transform the results into slices
        indices = [np.arange(i[0], i[1]+1, 2) for i in reg]

        # Finally get the correct positions bad positions
        bad_positions = np.hstack([positions[ind] for ind in indices])

        # Final positions
        positions = np.sort(
            np.unique(np.hstack([good_positions, bad_positions])))

    return positions


def replace_occurences(phrase, pair):
    """
    Introduces a new symbol and replaces all occurrences of the 
    most occurring pair.

    Equivalent to algorithm P from Larsson & Moffat (1999).
    """

    # Get a true vector of positions
    positions = prune_positions(np.array(phrase.positions[pair]))

    # Create a helper vector containing the correct value to subtract
    # to the position of the other digrams
    helper = np.zeros(len(phrase.phrase), dtype=int)
    helper[positions] = 1
    helper = np.cumsum(helper)

    # Update the neighbouring digrams
    for pos in positions:

        if pos == 0:
            right_neighbour = phrase.digrams[pos+1]
            right_neighbour.c1 = frozenset([str(phrase.symbol)])

        elif pos == len(phrase.digrams)-1:
            left_neighbour = phrase.digrams[pos-1]
            left_neighbour.c2 = frozenset([str(phrase.symbol)])

        else:
            left_neighbour = phrase.digrams[pos-1]
            right_neighbour = phrase.digrams[pos+1]
            left_neighbour.c2 = frozenset([str(phrase.symbol)])
            right_neighbour.c1 = frozenset([str(phrase.symbol)])

    # Update the position of the digrams
    phrase.update_positions(helper)

    # Remove most occurring pair from digrams list
    # Digrams are deleted in descending order so that the
    # values of indexes do not change
    for pos in sorted(positions, reverse=True):
        del phrase.digrams[pos]

    # Update the compressed string with the new symbol
    phrase.phrase = ' '.join(str(digram) for digram in phrase.digrams[::2])
    phrase.phrase += list(phrase.digrams[-1].c2)[0] if len(
        phrase.digrams) % 2 == 0 else ''

    # Update counts and positions of digrams
    phrase.generate_hash_tables()

    # Increment encoding symbol
    phrase.symbol += 1

    return


def repair(phrase):
    """
    Pair replacement mechanism.

    Equivalent to algorithm R from Larsson & Moffat (1999).
    """

    # Initialize phrase instance and inner data structures
    phrase = initialize_data_structures(phrase)

    # Initialize output data
    data = {
        'index': [''],
        'Rule': [''],
        'Occurrence': [1],
        'Phrase': [phrase.phrase]
    }

    while True:

        # Find most reccurring pairs of symbols
        pair, n_occurrence = most_reccuring_pair(phrase)

        # If no pair appears more than once, stop
        if n_occurrence == 1:
            break

        # Replace all occurrences of pairs with a symbol
        replace_occurences(phrase, pair)

        # Store information
        data['index'].append(f'R{phrase.symbol-1}')
        data['Rule'].append(f'{pair}')
        data['Occurrence'].append(n_occurrence)
        data['Phrase'].append(phrase.phrase)

    # Store results in the phrase instance
    phrase.compute_results(data)

    return phrase
