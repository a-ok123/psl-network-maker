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
        self.pipe = StableDiffusionPipeline.from_pretrained(settings.IMAGE_MODEL_ID,
                                                            scheduler=scheduler, torch_dtype=dtype)
        if settings.USE_GPU:
            self.pipe = self.pipe.to("cuda")
        self.compel = Compel(tokenizer=self.pipe.tokenizer, text_encoder=self.pipe.text_encoder)
        self.negative_conditioning = self.compel(settings.IMAGE_NEGATIVE_PROMPT)

    def generate(self, prompt, file_name):
        prompt_parts = prompt.split(". ")
        if len(prompt_parts) > 1:
            prompt = "(" + ', '.join(['"' + s + '"' for s in prompt_parts]) + ").add"
        conditioning = self.compel(prompt)
        [conditioning, negative_conditioning] = self.compel.pad_conditioning_tensors_to_same_length(
            [conditioning, self.negative_conditioning])
        image = self.pipe(
            prompt_embeds=conditioning,
            negative_propmt_embeds=negative_conditioning,
            num_inference_steps=settings.SD_ITERATIONS).images[0]
        image.save(file_name)
