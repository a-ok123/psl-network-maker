from diffusers import StableDiffusionPipeline, EulerDiscreteScheduler
import torch
from compel import Compel
import json

model_id = "stabilityai/stable-diffusion-2-base"

use_gpu = True
if use_gpu:
    dtype = torch.float16
else:
    dtype = torch.float32
scheduler = EulerDiscreteScheduler.from_pretrained(model_id, subfolder="scheduler")
pipe = StableDiffusionPipeline.from_pretrained(model_id, scheduler=scheduler, torch_dtype=dtype)
if use_gpu:
    pipe = pipe.to("cuda")

neg_prompt = "lowres, bad_anatomy, error_body, error_hair, error_arm, error_hands, bad_hands, error_fingers, bad_fingers, missing_fingers, error_legs, bad_legs, multiple_legs, missing_legs, error_lighting, error_shadow, error_reflection, text, error, extra_digit, fewer_digits, cropped, worst_quality, low_quality, normal_quality, jpeg_artifacts, signature, watermark, username, blurry"

prompt = "A majestic starship soars through the cosmos, its sleek lines and glowing engines cutting through the inky blackness of space. The vessel's hull glints with a rainbow of colors, reflecting the light of distant stars. A squadron of smaller craft flank the ship, their wings and engines aglow as they dart and weave in formation. In the distance, a swirling nebula glows like a celestial jellyfish, its tendrils reaching out towards the ship like ethereal tentacles."
prompt_parts = prompt.split(". ")
prompt_with_add = "(" + ', '.join(['"' + s + '"' for s in prompt_parts]) + ").add"

compel = Compel(tokenizer=pipe.tokenizer, text_encoder=pipe.text_encoder)
conditioning = compel(prompt_with_add)
# conditioning = compel(prompt)
negative_conditioning = compel(neg_prompt)
[conditioning, negative_conditioning] = compel.pad_conditioning_tensors_to_same_length([conditioning, negative_conditioning])
image = pipe(prompt_embeds=conditioning, negative_propmt_embeds=negative_conditioning, num_inference_steps=1000).images[0]
# image = pipe(prompt=prompt, num_inference_steps=1000).images[0]
image.save("testCompeln2-4.png")
