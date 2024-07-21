import pathlib
import random

import gradio as gr
from src import HindiTokenizer, BasicTokenizer

Basic = BasicTokenizer()
Basic._build_vocab()

Hindi = HindiTokenizer()
Hindi.load(
    model_file_path=pathlib.Path(
        "saved_vocabs/batch_1_Hindi_Tokenizer-test-all_batches-100_000_batchsize-initial_vocab_size_5000.model"))


def tokenize_and_color(text, tokenizer_choice="HindiTokenizer"):
    if tokenizer_choice == "BasicTokenizer":
        tokenizer = Basic
    else:
        tokenizer = Hindi

    tokens = tokenizer.encode(text)

    # colors = [
    #     "#FF5733", "#33FF57", "#3357FF", "#F333FF",
    #     "#33FFF3", "#F3FF33", "#FF3380", "#3380FF",
    #     "#83FF33", "#FF8333"
    # ]
    colors = [
        "#FF5733", "#33FF57", "#3357FF", "#F333FF",
        "#33FFF3", "#F3FF33", "#FF3380", "#3380FF",
        "#83FF33", "#FF8333", "#7FDBFF", "#0074D9",
        "#39CCCC", "#3D9970", "#2ECC40", "#01FF70",
        "#FFDC00", "#FF851B", "#FF4136", "#85144b",
        "#F012BE", "#B10DC9", "#AAAAAA", "#DDDDDD"
    ]

    colored_text = '<div style="word-wrap: break-word; white-space: pre-wrap;">'
    token_color_mapping = {}
    last_color = ""
    for index, token in enumerate(tokens):
        token_id = token
        if token_id in token_color_mapping:
            color = token_color_mapping[token_id]
        else:
            color = random.choice([c for c in colors if c != last_color])
            last_color = color
            token_color_mapping[token_id] = color
        colored_text += f'<span id="{token_id}" style="color: {color}; margin-right: 20px;">{token}</span>'
    colored_text += '</div>'

    return colored_text


examples = [
    ["आप कैसे हैं??"],
    ["यह एक परीक्षण है।"],
    ["लोरेम इप्सम एक छद्म-लैटिन पाठ है जिसका उपयोग मुद्रण और टाइपसेटिंग उद्योगों में किया जाता है।"],
    ["This is just English text for testing purposes."]
]

iface = gr.Interface(fn=tokenize_and_color,
                     title="Hindi Text Tokenizer",
                     description="Enter text to see the tokenized output with each token colored differently.",
                     inputs=[
                         gr.Textbox(lines=2, label="Input Text"),
                         gr.Radio(choices=["BasicTokenizer", "HindiTokenizer"], label="Tokenizer Choice",
                                  value="HindiTokenizer")
                     ],
                     outputs=[
                         gr.HTML(label="Tokenized and Colored Text")
                     ],
                     examples=examples,
                     # theme=gr.themes.Soft()
                     theme=gr.themes.Base()
                     )
if __name__ == "__main__":
    iface.launch()
