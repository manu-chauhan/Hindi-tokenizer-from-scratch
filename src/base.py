import unicodedata


def get_stats(ids, counts=None):
    """
    Given a list of ints/ids, count the pairwise occurence
    Returns count dict
    """
    counts = {} if counts is None else counts
    for pair in zip(ids, ids[1:]):
        counts[pair] = counts.get(pair, 0) + 1

    return counts


def merge(ids, pair_to_merge, idx_to_use):
    """
    find and merge the given `pair` and replace it with given `idx_to_use` in given list of ints/ids
    Return updated list
    """
    new_ids = []

    i = 0

    while i < len(ids):
        # check pair match AND if 0th position is NOT last element
        if i < len(ids) - 1 and (pair_to_merge[0] == ids[i] and pair_to_merge[1] == ids[i + 1]):
            new_ids.append(idx_to_use)  # pair found, append to new list of ids
            i += 2  # skip by two elements as the pair is found
        else:
            # pair not found in the list, normal 1 element update
            new_ids.append(ids[i])  # append the current item from old list as it is not a pair
            i += 1
    return new_ids


# helper functions taken directly from Karpathy's BPE repo
def replace_control_characters(s: str) -> str:
    chars = []
    for ch in s:
        if unicodedata.category(ch)[0] != "C":
            chars.append(ch)  # this character is ok
        else:
            chars.append(f"\\u{ord(ch):04x}")  # escape
    return "".join(chars)


def render_token(t: bytes) -> str:
    # pretty print a token, escaping control characters
    s = t.decode('utf-8', errors='replace')
    s = replace_control_characters(s)
    return s


# base Tokenizer class

class Tokenizer:
    """Base Tokenizer class, MUST inherit for use"""

    def __init__(self) -> None:
        # defaults -> no patterns used, no merges, use usual first 256 bytes as mapping/vocab items
        self.merges = {}  # this will hold the actual merged data eg: (101, 32) -> 256 , here say 101 chr e and 32 ' '(space) had max pair count -> replace this with next ID in order
        self.pattern = ""  # any regular expression pattern if to be used on raw text
        self.special_tokens = {}  # a mapping t hold any special tokens, empty here, to be used for subclasses, str -> int, e.g. {'<|endoftext|>': 90257}
        self.vocab = self._build_vocab()  # int -> bytes

    def train(self, text, vocab_size, verbose=False):
        # Tokenizer can train a vocabulary of size vocab_size from text
        raise NotImplementedError

    def encode(self, text):
        # Tokenizer can encode a string into a list of integers
        raise NotImplementedError

    def decode(self, ids):
        # Tokenizer can decode a list of integers into a string
        raise NotImplementedError

    def _build_vocab(self):
        # here vocab starts from normal 256 bytes of ints and then merges after it
        vocab = {idx: bytes([idx]) for idx in range(256)}

        for (pos0, pos1), idx in self.merges.items():
            vocab[idx] = vocab[pos0] + vocab[pos1]

        # NOW add special tokens defined in __init__()
        # NOTE encode special tokens using .encode with UTF-8 encoding
        for tok, idx in self.special_tokens.items():
            vocab[idx] = tok.encode("utf-8")

    # directly from BPE repo
    def save(self, file_prefix):
        """
        Saves two files: file_prefix.vocab and file_prefix.model
        This is inspired (but not equivalent to!) sentencepiece's model saving:
        - model file is the critical one, intended for load()
        - vocab file is just a pretty printed version for human inspection only
        """
        print("Saving tokenizer...")
        # write the model: to be used in load() later
        model_file = file_prefix + ".model"
        with open(model_file, 'w') as f:
            # write the version, pattern and merges, that's all that's needed
            f.write("base v1\n")
            f.write(f"{self.pattern}\n")
            # write the special tokens, first the number of them, then each one
            f.write(f"{len(self.special_tokens)}\n")
            for special, idx in self.special_tokens.items():
                f.write(f"{special} {idx}\n")
            # the merges dict
            for idx1, idx2 in self.merges:
                f.write(f"{idx1} {idx2}\n")
        # write the vocab: for the human to look at
        vocab_file = file_prefix + ".vocab"
        inverted_merges = {idx: pair for pair, idx in self.merges.items()}
        with open(vocab_file, "w", encoding="utf-8") as f:
            for idx, token in self.vocab.items():
                # note: many tokens may be partial utf-8 sequences
                # and cannot be decoded into valid strings. Here we're using
                # errors='replace' to replace them with the replacement char �.
                # this also means that we couldn't possibly use .vocab in load()
                # because decoding in this way is a lossy operation!
                s = render_token(token)
                # find the children of this token, if any
                if idx in inverted_merges:
                    # if this token has children, render it nicely as a merge
                    idx0, idx1 = inverted_merges[idx]
                    s0 = render_token(self.vocab[idx0])
                    s1 = render_token(self.vocab[idx1])
                    f.write(f"[{s0}][{s1}] -> [{s}] {idx}\n")
                else:
                    # otherwise this is leaf token, just print it
                    # (this should just be the first 256 tokens, the bytes)
                    f.write(f"[{s}] {idx}\n")

    def load(self, model_file):
        """Inverse of save() but only for the model file"""
        assert model_file.endswith(".model")
        # read the model file
        merges = {}
        special_tokens = {}
        idx = 256
        with open(model_file, 'r', encoding="utf-8") as f:
            # read the version
            version = f.readline().strip()
            print(version)

            # read the pattern
            self.pattern = f.readline().strip()

            # read the special tokens
            num_special = int(f.readline().strip())
            for _ in range(num_special):
                special, special_idx = f.readline().strip().split()
                special_tokens[special] = int(special_idx)
            # read the merges
            for line in f:
                idx1, idx2 = map(int, line.split())
                merges[(idx1, idx2)] = idx
                idx += 1
        self.merges = merges
        self.special_tokens = special_tokens
        self.vocab = self._build_vocab()
