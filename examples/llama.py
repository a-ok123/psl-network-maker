from llama_cpp import Llama, LlamaGrammar

llm = Llama(
    model_path="/home/alexey/work/Models/TheBloke/llama-2-13b-chat.Q8_0.gguf",
    chat_format="llama-2",
    n_gpu_layers=-1,
    n_ctx=1024
)

# read grammar from file
with open("../grammar-img.gbnf", "r") as file:
    grammar_text = file.read()
    grammar = LlamaGrammar.from_string(grammar_text)

# system_message = {"role": "system", "content":  "You will be generating prompts for text to image generation. Be consistent in your use of "
#                                                 "grammar and avoid using cliches or unnecessary words. Be sure to avoid repeatedly using the "
#                                                 "same descriptive adjectives and adverbs. Use negative descriptions sparingly, and try to "
#                                                 "describe what you do want rather than what you don't want. Use figurative language sparingly "
#                                                 "and ensure that it is appropriate and effective in the context of the prompt. Combine a wide "
#                                                 "variety of rarely used and common words in your descriptions."
                                                    # "Describe the genre, scene, actors, mood, action, location, context;"
                                                    # "choose type of the image (painting, photograph, digital image, etc.)"
                                                    # "For painting: describe the style, technique, and materials. "
                                                    # "For photograph: describe the focal length, aperture, and lighting."
                                                    # "For digital image: describe the software, tools, and resolution (SD, HD, 4K, etc.)"
#                                                 }
system_message = {"role": "system", "content":
                  "You will be Generate descriptions of a random images. Use less than 200 words. "
                  "Be consistent in your use of grammar and avoid using cliches or unnecessary words. "
                  "Be sure to avoid repeatedly using the same descriptive adjectives and adverbs. "
                  }

output = llm.create_chat_completion(
    grammar=grammar,
    messages=[
        system_message,
        {"role": "user", "content": "Generate 5 descriptions. Use space opera genre"}
        ]
)

print(f"output: {output['choices'][0]['message']['content']}")
