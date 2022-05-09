
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
        self.raw = phrase  # Initial phrase
        self.phrase = phrase  # Phrase being compressed
        self.symbol = 1

        # Digram generation
        self.generate_digrams()

        # Hash table generation
        self.generate_hash_tables()

    def generate_digrams(self):
        """
        Create digram instances.
        """

        self.digrams = [Digram(i, c1, c2, self.raw)
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

    def get_results(self):

        return pd.DataFrame({'Occurrences': self.results['Occurrences'],
                             'Phrase': self.results['Phrase']},
                            index=self.results['Pair'])

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

    def __init__(self, i, c1, c2, raw):

        # Initial phrase
        self.raw = raw

        # Digram parameters
        self.pos = i
        self.c1 = c1
        self.c2 = c2

    def __str__(self) -> str:
        return self.c1 + self.c2


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
    string = ''.join([str(d) for d in diff])
    # Use regex to find all successions of '1's
    reg = [m.span() for m in re.finditer('11*', string)]

    # If there are problematic positions
    if reg:

        # Non problematic positions
        good_positions = positions[np.where(diff != 1)[0]+1]

        # Transform the results into slices
        indices = [np.arange(i[0], i[1]+1, 2, ) for i in reg]

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
            right_neighbour.c1 = str(phrase.symbol)

        elif pos == len(phrase.phrase)-2:  # -2 because of digram length
            left_neighbour = phrase.digrams[pos-1]
            left_neighbour.c2 = str(phrase.symbol)

        else:
            left_neighbour = phrase.digrams[pos-1]
            right_neighbour = phrase.digrams[pos+1]
            left_neighbour.c2 = str(phrase.symbol)
            right_neighbour.c1 = str(phrase.symbol)

    # Update the position of the digrams
    phrase.update_positions(helper)

    # Remove most occurring pair from digrams list
    # Digrams are deleted in descending order so that the
    # values of indexes do not change
    for pos in sorted(positions, reverse=True):
        del phrase.digrams[pos]

    # Update the compressed string with the new symbol
    phrase.phrase = phrase.phrase.split(pair)
    phrase.phrase = str(phrase.symbol).join(phrase.phrase)

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
        'Pair': [''],
        'Occurrences': [1],
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
        data['Pair'].append(f'{phrase.symbol-1} 🠖 {pair}')
        data['Occurrences'].append(n_occurrence)
        data['Phrase'].append(phrase.phrase)

    # Store results in the phrase instance
    phrase.results = data

    return phrase
