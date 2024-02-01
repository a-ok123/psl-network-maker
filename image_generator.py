from diffusers import StableDiffusionPipeline, EulerDiscreteScheduler
import torch
from compel import Compel

from config import settings


class SDImageGenerator:
    def __init__(self):
        if settings.USE_GPU:
            dtype = torch.float16
        else:
            dtype = torch.float32
        scheduler = EulerDiscreteScheduler.from_pretrained(settings.IMAGE_MODEL_ID, subfolder="scheduler")
        self.pipe = StableDiffusionPipeline.from_pretrained(settings.IMAGE_MODEL_ID, scheduler=scheduler, torch_dtype=dtype)
        # self.compel = Compel(tokenizer=self.pipe.tokenizer, text_encoder=self.pipe.text_encoder)
        if settings.USE_GPU:
            self.pipe = self.pipe.to("cuda")

    def generate(self, prompt, file_name):
        # conditioning = self.compel.build_conditioning_tensor(prompt)
        # image = self.pipe(prompt_embeds=conditioning, num_inference_steps=20).images[0]
        image = self.pipe(prompt).images[0]
        image.save(file_name)
