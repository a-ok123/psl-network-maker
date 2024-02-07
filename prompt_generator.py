import json

from llama_cpp import Llama, LlamaGrammar

from config import settings


class LlamaPromptGenerator:
    def __init__(self):
        if settings.USE_GPU:
            self.llm = Llama(model_path=settings.PROMPT_MODEL_PATH,
                             chat_format=settings.PROMPT_CHAT_FORMAT, n_gpu_layers=-1, n_ctx=2048)
        else:
            self.llm = Llama(model_path=settings.PROMPT_MODEL_PATH,
                             chat_format=settings.PROMPT_CHAT_FORMAT)
        self.system_message = {"role": "system", "content": settings.LLAMA_SYSTEM_PROMPT}

        self.grammar = None
        with open(settings.GRAMMAR_PATH, "r") as file:
            grammar_text = file.read()
            self.grammar = LlamaGrammar.from_string(grammar_text)

    def generate_prompt(self, tip: str = "") -> dict:
        user_prompt = settings.LLAMA_USER_REQUEST.format(tip)
        output = self.llm.create_chat_completion(
            grammar=self.grammar,
            messages=[
                self.system_message,
                {"role": "user", "content": user_prompt}
            ]
        )
        return self.parse_output(output)

    @staticmethod
    def parse_output(output) -> dict|None:
        if (output and
                'choices' in output and output['choices'] and len(output['choices']) > 0 and
                'message' in output['choices'][0] and output['choices'][0]['message'] and
                'content' in output['choices'][0]['message'] and output['choices'][0]['message']['content']):
            return json.loads(output['choices'][0]['message']['content'])
        else:
            return None


#### NFT
# {
#   "description": "",
#   "name": "",
#   "creator_name": "",
#   "issued_copies": 1,
#   "keywords": "",
#   "series_name": ""
#   "royalty": 0.0,
#   "green": true|false,
# }
# collection_act_txid
# open_api_group_id
# make_publicly_accessible

#### Cascade
# make_publicly_accessible


#### Sense
# collection_act_txid
# open_api_group_id