# source: https://huggingface.co/learn/nlp-course/en/chapter6/8?fw=pt

from tokenizers import normalizers, models, decoders, pre_tokenizers, trainers, Tokenizer, processors
from datasets import load_dataset

dataset = load_dataset("wikitext", name="wikitext-2-raw-v1", split="train")


def get_training_corpus(batch_size=1000):
    for i in range(0, len(dataset), batch_size):
        yield dataset[i: i + batch_size]["text"]


tokenizer = Tokenizer(model=models.WordPiece(unk_token="[UNK]"))

tokenizer.normalizer = normalizers.Sequence([normalizers.NFD(), normalizers.Lowercase(), normalizers.StripAccents()])

print(tokenizer.normalizer.normalize_str("Héllò hôw are ü?"))

tokenizer.pre_tokenizer = pre_tokenizers.Whitespace()  # pre_tokenizers.BertPreTokenizer()

print(tokenizer.pre_tokenizer.pre_tokenize_str("Let's test my pre-tokenizer."))
pre_tokenizer = pre_tokenizers.WhitespaceSplit()
print(pre_tokenizer.pre_tokenize_str("Let's test my pre-tokenizer."))

# manually selecting individual splitters
pre_tokenizer = pre_tokenizers.Sequence(
    [pre_tokenizers.WhitespaceSplit(), pre_tokenizers.Punctuation()]
)
print(pre_tokenizer.pre_tokenize_str("Let's test my pre-tokenizer."))

special_tokens = ["[UNK]", "[PAD]", "[CLS]", "[SEP]", "[MASK]"]
trainer = trainers.WordPieceTrainer(vocab_size=25000, special_tokens=special_tokens)

# train from an iterator
tokenizer.train_from_iterator(get_training_corpus(), trainer=trainer)
cls_token_id = tokenizer.token_to_id("[CLS]")
sep_token_id = tokenizer.token_to_id("[SEP]")

print(cls_token_id, sep_token_id)

"""
To write the template for the TemplateProcessor, we have to specify how to treat a single sentence and a pair of sentences. 
For both, we write the special tokens we want to use; the first (or single) sentence is represented by $A, 
while the second sentence (if encoding a pair) is represented by $B. For each of these (special tokens and sentences), 
we also specify the corresponding token type ID after a colon.

The classic BERT template is thus defined as follows:

"""

tokenizer.post_processor = processors.TemplateProcessing(
    single=f"[CLS]:0 $A:0 [SEP]:0",
    pair=f"[CLS]:0 $A:0 [SEP]:0 $B:1 [SEP]:1",
    special_tokens=[("[CLS]", cls_token_id), ("[SEP]", sep_token_id)],
)

encoding = tokenizer.encode("Let's test this tokenizer.")
print(encoding.tokens)

encoding = tokenizer.encode("Let's test this tokenizer...", "on a pair of sentences.")
print(encoding.tokens)
print(encoding.type_ids)

tokenizer.decoder = decoders.WordPiece(prefix="##")

from transformers import PreTrainedTokenizerFast

wrapped_tokenizer = PreTrainedTokenizerFast(
    tokenizer_object=tokenizer,
    # tokenizer_file="tokenizer.json", # You can load from the tokenizer file, alternatively
    unk_token="[UNK]",
    pad_token="[PAD]",
    cls_token="[CLS]",
    sep_token="[SEP]",
    mask_token="[MASK]",
)