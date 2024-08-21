import os
import pathlib
import subprocess
import time

import utilities
from src import HindiTokenizer
from src.HindiTokenizer import SIMPLE_HINDI_PATTERN


@utilities.log_to_file("main.log")
def main():
    BATCH_SIZE = 20_000
    NUMBER_OF_BATCHES = None # None --> read all batches of entire data from all files present in `dataset` dir
    train = False

    '''
       initial vocab size to start with, basic Hindi chars/tokens/units of alphabet'''
    initial_vocab_size = 5000
    """increase vocab size by this much for every batch, will reuse same tokenizer object and vocab"""
    vocab_increase_size = 100  # considering that added check if most are just replacements and very low new tokens then loop breaks before this number is reached
    resume = True  # resume building vocab from already saved file
    resumed = False  # a flag to check if resume process already began

    if NUMBER_OF_BATCHES is None:

        FILE_SAVE_PREFIX = (f"Hindi_Tokenizer-test-all_batches-{BATCH_SIZE:_}_batchsize"
                            f"-initial_vocab_size_{initial_vocab_size}")
    else:
        FILE_SAVE_PREFIX = (f"Hindi_Tokenizer-test-{NUMBER_OF_BATCHES}_batches-{BATCH_SIZE:_}_batchsize"
                            f"-initial_vocab_size_{initial_vocab_size}")
    """
    HINDI_BASIC_UNITS_COUNT = 101
    Came to be 101 count when splitting this on space, 1 for every character:
    
                    अ आ इ ई उ ऊ ए ऐ ओ औ अं अः ऋ ॠ
                    ा ि ी ु ू ृॄ ॅॆ े ैॉ ॊ ो ौ                     
                    क ख ग घ ङ क़ ख़ ग़ घ़ ङ़
                    च छ ज झ ञ ज़ झ़ ञ़
                    ट ठ ड ढ ण ड़ ढ़ ण़
                    त थ द ध न त़ थ़ द़ ध़ ऩ
                    प फ ब भ म प़ फ़ ब़ म़
                    य र ल ळ व य़ ऱ ल़ ऴ व़
                    श ष ॺ स ह श़ ष़ स़ ह़
                    ० १ २ ३ ४ ५ ६ ७ ८ ९ 
                    ॥
                    
    """
    HINDI_BASIC_UNITS_COUNT = 101  # hindi_varnmala_and_basic_units.strip().split() -> removed | , ? ; . as special ones are already in first 256 bytes

    tokenizer = HindiTokenizer(pattern=SIMPLE_HINDI_PATTERN)

    all_files = utilities.get_all_text_dataset("dataset")

    # NOTE: first pull all LFS files; src: https://stackoverflow.com/a/72830455/3903762
    process = subprocess.Popen(["git", "lfs", "fetch", "--all"], stdout=subprocess.PIPE)
    output = process.communicate()[0]
    print(output)
    # actually download original file contents, previous command only fetches metadata
    process = subprocess.Popen(["git", "lfs", "checkout"], stdout=subprocess.PIPE)
    output = process.communicate()[0]
    print(output)

    """returns a generator and not a list"""

    # TODO joblib's Parallel should be used to use all CPU cores and update shared data structure to build vocab : to reduce time

    result = utilities.read_from_all_files(all_files, batch_size=BATCH_SIZE, batch_num=NUMBER_OF_BATCHES)

    os.makedirs("saved_vocabs", exist_ok=True)

    start = time.perf_counter()

    '''run Tokenizer "train" on each batch ... using same Tokenizer object AND vocab !'''
    for batch_idx, data_batch in enumerate(result):
        print(f"\n\nBatch number=====================================================: {batch_idx}\n")

        batch_text = "".join(data_batch)  # need to join to get single str as batch is list of lines of text

        if batch_idx == 0 and train is True:
            if not resume:
                tokenizer.train(text=batch_text,
                                vocab_size=initial_vocab_size + (256 + HINDI_BASIC_UNITS_COUNT),
                                # 256 + 101 ; characters [ह़] -> 345,  [९] -> 355,  [॥] -> 356
                                verbose=True,
                                current_batch_num=batch_idx + 1,
                                save_tokenizer_at_train_end=True,
                                prefix_for_save=FILE_SAVE_PREFIX
                                )
            else:
                print("Skipping first batch as it resumes from existing vocab and merges.")
                continue
        else:
            if resume and not resumed:
                tokenizer.load(
                    model_file_path=pathlib.Path(
                        "saved_vocabs/batch_1_Hindi_Tokenizer-test-all_batches-100_000_batchsize-initial_vocab_size_5000.model"))
                resumed = True
            if train is True:
                tokenizer.train(text=batch_text,
                                vocab_size=vocab_increase_size + (256 + HINDI_BASIC_UNITS_COUNT),  # 256 + 101
                                current_batch_num=batch_idx + 1,
                                save_tokenizer_at_train_end=True,
                                prefix_for_save=FILE_SAVE_PREFIX,
                                just_replacing_already_seen_tokens_counter_threshold=500,
                                minting_new_token_for_merge_threshold=5,
                                save_at_every_nth_iteration=100,
                                verbose=True)
            else:
                break

    end = time.perf_counter()

    if train:
        print(f"\n==============\n\nTime taken for running BPE on entire dataset : {(end - start)} seconds")
    elif not train and resume:
        print("loaded vocab and merges...")

    # save the tokenizer object
    # tokenizer.save(file_prefix="hindi-30k_batchsize-all_batches-200_initial_vocab-50_next_batches")

    print("\n====Running batches on entire data to be read for encoding now...")

    result = utilities.read_from_all_files(all_files, batch_size=BATCH_SIZE, batch_num=NUMBER_OF_BATCHES)
    total_raw_text_len = total_encoded_len = 0

    for batch_idx, batch_data in enumerate(result):
        batch_text = "".join(batch_data)  # need to join to get single str as batch is list of lines of text
        raw_batch_data_len = len(batch_text)
        total_raw_text_len += raw_batch_data_len

        encoded = tokenizer.encode(text=batch_text)
        encoded_batch_data_len = len(encoded)
        total_encoded_len += encoded_batch_data_len

        print(f"\nbatch : {batch_idx} len:{raw_batch_data_len}...encoded len: {encoded_batch_data_len}...\n")

    print(f"\n\n================================\n"
          f"Total len of text in Hindi ran for {str(NUMBER_OF_BATCHES) + ' batches'
          if isinstance(NUMBER_OF_BATCHES, int) else 'all batches for entire dataset'} is : {total_raw_text_len}")

    print(f"Encoded total len: {total_encoded_len}")

    print(f"Ratio of raw data for : {str(NUMBER_OF_BATCHES) + ' for each batch size :' + str(BATCH_SIZE)")
    if isinstance(NUMBER_OF_BATCHES, int) else 'entire dataset'} compressed: {total_raw_text_len / total_encoded_len}")


if __name__ == "__main__":
    main()
