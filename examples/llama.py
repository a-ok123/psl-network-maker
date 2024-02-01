from llama_cpp import Llama, LlamaGrammar

llm = Llama(
    model_path="D:\models\TheBloke\llama-2-13b-chat.Q8_0.gguf",
    chat_format="llama-2",
    n_gpu_layers=-1,
    n_ctx=1024
)

# read grammar from file
with open("../grammar-img.gbnf", "r") as file:
    grammar_text = file.read()
    grammar = LlamaGrammar.from_string(grammar_text)

system_message = {"role": "system", "content":  "You will be generating prompts for text to image generation. Be consistent in your use of "
                                                "grammar and avoid using cliches or unnecessary words. Be sure to avoid repeatedly using the "
                                                "same descriptive adjectives and adverbs. Use negative descriptions sparingly, and try to "
                                                "describe what you do want rather than what you don't want. Use figurative language sparingly "
                                                "and ensure that it is appropriate and effective in the context of the prompt. Combine a wide "
                                                "variety of rarely used and common words in your descriptions."
                                                }

output = llm.create_chat_completion(
    grammar=grammar,
    messages = [
        system_message,
        # {"role": "user", "content": "Make 1 random prompt. Use fantasy genre. Include a dragon and a castle."}
        {"role": "user", "content": "Make 1 random prompt. Use futuristic genre. Include city and ttransport."}
        ]
)

print(f"output: {output['choices'][0]['message']['content']}")