from llama_cpp import Llama

from config import settings

SYSTEM_PROMPT = (
    "You will be generating prompts for a Generative Adversarial Network (GAN) that can take text "
    "and output images. Your goal is to create a prompt that the GAN can use to generate an image. "
    "The 'imagine prompt' should strictly contain under 1,500 words. Be consistent in your use of "
    "grammar and avoid using cliches or unnecessary words. Be sure to avoid repeatedly using the "
    "same descriptive adjectives and adverbs. Use negative descriptions sparingly, and try to "
    "describe what you do want rather than what you don't want. Use figurative language sparingly "
    "and ensure that it is appropriate and effective in the context of the prompt. Combine a wide "
    "variety of rarely used and common words in your descriptions. Use following example as template "
    "to output prompts: IMAGE_TYPE: Macro close-up | GENRE: Fantasy | EMOTION: Quirky | SCENE: A tiny "
    "fairy sitting on a mushroom in a magical forest, surrounded by glowing fireflies | ACTORS: Fairy "
    "| LOCATION TYPE: Magical forest | CAMERA MODEL: Fujifilm X-T4 | CAMERA LENSE: 100mm f/2.8 Macro "
    "| SPECIAL EFFECTS: Infrared photography | TAGS: macro, fantasy, whimsical, fairy, glowing "
    "fireflies, magical atmosphere, mushroom, enchanted forest — ar 16:9"
    "No chit-chat! No fluff! No filler! Just the file name, strait. NO 'Sure!'; NO 'Here's ...'; JUST A PROMPT!!!"
)
# SYSTEM_PROMPT = (
#    "You generate diverse and creative prompts for image generation, "
#    "focusing on themes such as "
#    "futuristic technology, "
#    "cyberpunk landscapes, "
#    "abstract art, "
#    "nature scenes, "
#    "and architectural designs. "
#    # "Incorporate elements like vivid colors, "
#    "intricate patterns, and unique perspectives. "
#    "Ensure variety and innovation in each prompt to inspire a wide range of "
#    "imaginative and visually compelling images."
# )

USER_REQUEST = "Make 1 random prompt. Use fantasy genre. Include a dragon and a castle." # No more than 100 words."
# USER_REQUEST = ("Generate a unique and detailed prompt for image generation, "
#                 "focusing on themes related to advanced technology, cyber security, or futuristic concepts. "
#                 "Include elements that evoke a sense of innovation, complexity, and intrigue. "
#                 "The prompt should inspire an image that visually represents cutting-edge ideas or scenarios.")
FILE_NAME_REQUEST = (
    "Generate a single, concise file name reflecting the main themes of the image prompt above. "
    "The file name should be simple, descriptive, and follow standard file naming conventions "
    "without special characters. File name must be 50 character MAX. "
    "Please provide a direct answer only without any additional context or explanation. No elaboration needed. "
    "No chit-chat! No fluff! No filler! Just the file name, strait.  NO 'Sure!'; NO 'Here's ...'; JUST A FILENAME!!!"
)


class LlamaPromptGenerator:
    def __init__(self):
        if settings.USE_GPU:
            self.llm = Llama(model_path=settings.PROMPT_MODEL_PATH,
                             chat_format=settings.PROMPT_CHAT_FORMAT, n_gpu_layers=-1, n_ctx=2048)
        else:
            self.llm = Llama(model_path=settings.PROMPT_MODEL_PATH,
                             chat_format=settings.PROMPT_CHAT_FORMAT)
        self.system_message = {"role": "system", "content": SYSTEM_PROMPT}

    def generate_prompt(self) -> str:
        # response = self.llm(prompt=USER_REQUEST)
        # return response['choices'][0]['message']['content']
        output = self.llm.create_chat_completion(messages=[
            self.system_message,
            {"role": "user", "content": USER_REQUEST}])
        return self.parse_output(output)

    def generate_file_name(self, prompt) -> str:
        output = self.llm.create_chat_completion(messages=[
            self.system_message,
            {"role": "assistant", "content": prompt},
            {"role": "user", "content": FILE_NAME_REQUEST}], stop=[".jpeg", ".jpg", ".png"])
        name = self.parse_output(output).strip().strip("'").strip('"')
        return name + ".png"

    @staticmethod
    def parse_output(output):
        if (output and
                'choices' in output and output['choices'] and len(output['choices']) > 0 and
                'message' in output['choices'][0] and output['choices'][0]['message'] and
                'content' in output['choices'][0]['message'] and output['choices'][0]['message']['content']):
            return output['choices'][0]['message']['content']
        else:
            return None
