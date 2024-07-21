"""
Minimal (byte-level) Byte Pair Encoding tokenizer.

Algorithmically follows along the GPT tokenizer:
https://github.com/openai/gpt-2/blob/master/src/encoder.py

But:
- Does not handle the regular expression splitting pattern.
- Does not handle any special tokens.
"""
import copy

from .base import Tokenizer, get_stats, merge


# class BasicTokenizer(Tokenizer):
#
#     def __init__(self):
#         super().__init__()
#
#     def train(self, text, vocab_size, verbose=False):
#         assert vocab_size >= 256
#         num_merges = vocab_size - 256
#
#         # input text preprocessing
#         text_bytes = text.encode("utf-8")  # raw bytes
#         ids = list(text_bytes)  # list of integers in range 0..255
#
#         # iteratively merge the most common pairs to create new tokens
#         merges = {}  # (int, int) -> int
#         vocab = {idx: bytes([idx]) for idx in range(256)}  # int -> bytes
#         for i in range(num_merges):
#             # count up the number of times every consecutive pair appears
#             stats = get_stats(ids)
#             # find the pair with the highest count
#             pair = max(stats, key=stats.get)
#             # mint a new token: assign it the next available id
#             idx = 256 + i
#             # replace all occurrences of pair in ids with idx
#             ids = merge(ids, pair, idx)
#             # save the merge
#             merges[pair] = idx
#             vocab[idx] = vocab[pair[0]] + vocab[pair[1]]
#             # prints
#             if verbose:
#                 print(f"merge {i + 1}/{num_merges}: {pair} -> {idx} ({vocab[idx]}) had {stats[pair]} occurrences")
#
#         # save class variables
#         self.merges = merges  # used in encode()
#         self.vocab = vocab  # used in decode()
#
#     def decode(self, ids):
#         # given ids (list of integers), return Python string
#         text_bytes = b"".join(self.vocab[idx] for idx in ids)
#         text = text_bytes.decode("utf-8", errors="replace")
#         return text
#
#     def encode(self, text):
#         # given a string text, return the token ids
#         text_bytes = text.encode("utf-8")  # raw bytes
#         ids = list(text_bytes)  # list of integers in range 0..255
#         while len(ids) >= 2:
#             # find the pair with the lowest merge index
#             stats = get_stats(ids)
#             pair = min(stats, key=lambda p: self.merges.get(p, float("inf")))
#             # subtle: if there are no more merges available, the key will
#             # result in an inf for every single pair, and the min will be
#             # just the first pair in the list, arbitrarily
#             # we can detect this terminating case by a membership check
#             if pair not in self.merges:
#                 break  # nothing else can be merged anymore
#             # otherwise let's merge the best pair (lowest merge index)
#             idx = self.merges[pair]
#             ids = merge(ids, pair, idx)
#         return ids


class BasicTokenizer(Tokenizer):

    def __init__(self):
        super().__init__()
        self.merge_counter = 0

    def train(self, text, vocab_size, verbose=False):
        # left assert in place just to introduce consistency and a hard check of the increase in vocab size and number of merges
        assert vocab_size >= 256
        num_merges = vocab_size - 256

        current_batch_merge_counter = 0  # in case not all exact `num_merges` happen

        # input text preprocessing
        text_bytes = text.encode("utf-8")  # encode to get all waw bytes
        ids = list(text_bytes)  # represent the bytes in ints

        # use same merge dict if exists
        self.merges = {} if self.merges is None else self.merges  # to hold all merges (int, int) -> int

        # Use same vocab for this Tokenizer object if it exists
        # Tokenizer vocab:  int -> bytes
        self.vocab = {idx: bytes([idx]) for idx in range(256)} if self.vocab is None else self.vocab

        # iteratively merge the MOST COMMON pair from the text
        for i in range(num_merges):
            # get count of pairs
            stats = get_stats(ids)

            # find the pair with the highest count
            # pair = max(stats, key=stats.get)

            # tmp_stats = copy.deepcopy(stats)

            # get most occurring pair from ids
            pair = max(stats, key=stats.get)

            while pair in self.merges:
                # pair was previously merged ... use this first to update IDS
                # No need to add to merges and vocab, use previously stored token
                already_merged_idx = self.merges[pair]

                # just replace already merged pairs in ids and get new ids and no need to again add to merges and vocab
                ids = merge(ids, pair, already_merged_idx)

                stats = get_stats(ids)

                if stats and len(ids) >= 2:
                    pair = max(stats, key=stats.get)
                else:
                    # no new merges found in this incoming data batch
                    print(f"\n\nstopping merges as no new byte pair found in the current batch")
                    break

            # this most occurring pair not merged yet in any data batch
            #  generate a new token considering how many have been generated so far for the same tokenizer
            idx = len(self.vocab) + 1

            # update current new generated tokens to add to self.merge_counter later
            current_batch_merge_counter += 1

            # replace all occurrences of `pair` above in `ids` with NEW `idx` token, add this one to merges & vocab
            # Note: this pair has never been seen for merging
            ids = merge(ids, pair, idx)
            self.merges[pair] = idx
            self.vocab[idx] = self.vocab[pair[0]] + self.vocab[pair[1]]
            if verbose:
                print(f"merge {i + 1}/{num_merges}: {pair} -> {idx} ({self.vocab[idx]}) had {stats[pair]} count")

        self.merge_counter += current_batch_merge_counter

    def decode(self, ids):
        # given ids (list of integers), return Python string
        text_bytes = b"".join(self.vocab[idx] for idx in ids)
        text = text_bytes.decode("utf-8", errors="replace")
        return text

    def encode(self, text):
        # input a string text, returns the token ids
        text_bytes = text.encode("utf-8")
        ids = list(text_bytes)
        while len(ids) >= 2:
            # here find the pair with the lowest merge index
            stats = get_stats(ids)
            pair = min(stats, key=lambda p: self.merges.get(p, float("inf")))
            # if no merges i.e. the pair is not in merges dict,
            # the key will result in an `inf` for every single pair,
            # and the min will be just the first pair in the list,
            # we can detect this terminating case by a membership check
            if pair not in self.merges:
                break  # nothing else can be merged anymore
            # otherwise merge the best pair NOTE: (lowest merge index)
            idx = self.merges[pair]
            ids = merge(ids, pair, idx)
        return ids
