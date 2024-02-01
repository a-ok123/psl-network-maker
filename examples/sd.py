import time
from diffusers import StableDiffusionPipeline, EulerDiscreteScheduler, DiffusionPipeline
import torch
from compel import Compel
import json

model_id = "stabilityai/stable-diffusion-2-base"

prompt = """
{
"ImageType": "image", "Genre": "Futuristic", "Emotion": "Excitement", "Scene": "City", "Actors": "Humans", "LocationType": "Transportation", "Tags": ["flying cars", "neon lights", "skyscrapers", "high-tech gadgets"],"AspectRatio": "16:9", "Media":  {"Style": "Digital Painting", "ColorPalette": "Vibrant"}
}
"""


def json_to_compel_prompt(json_prompt):
    json_data = json.loads(json_prompt)
    flat_list = []
    def flatten_element(key, value):
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                flatten_element(f"{sub_key}", sub_value)
        elif isinstance(value, list):
            flat_list.append(', '.join(value))
        else:
            flat_list.append(value)
    for k, v in json_data.items():
        flatten_element(k, v)
    # return '("{0}").and()'.format("\", \"".join(flat_list))
    return ",".join(flat_list)

def flatten_json_prompt(json_prompt):
    json_data = json.loads(json_prompt)
    flat_list = []
    def flatten_element(key, value):
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                flatten_element(f"{sub_key}", sub_value)
        elif isinstance(value, list):
            flat_list.append(f"{key}: {', '.join(value)}")
        else:
            flat_list.append(f"{key}: {value}")
    for k, v in json_data.items():
        flatten_element(k, v)
    return ", ".join(flat_list)

# Use the Euler scheduler here instead
scheduler = EulerDiscreteScheduler.from_pretrained(model_id, subfolder="scheduler")
pipe = StableDiffusionPipeline.from_pretrained(model_id, scheduler=scheduler, torch_dtype=torch.float16)
# pipe = DiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16, custom_pipeline="lpw_stable_diffusion", scheduler=scheduler)
pipe = pipe.to("cuda")

neg_prompt = "lowres, bad_anatomy, error_body, error_hair, error_arm, error_hands, bad_hands, error_fingers, bad_fingers, missing_fingers, error_legs, bad_legs, multiple_legs, missing_legs, error_lighting, error_shadow, error_reflection, text, error, extra_digit, fewer_digits, cropped, worst_quality, low_quality, normal_quality, jpeg_artifacts, signature, watermark, username, blurry"
prompt = flatten_json_prompt(prompt)
# prompt = json_to_compel_prompt(prompt)
print(prompt)

# with Compel
compel = Compel(tokenizer=pipe.tokenizer, text_encoder=pipe.text_encoder)
conditioning = compel(prompt)
negative_conditioning = compel(neg_prompt)
[conditioning, negative_conditioning] = compel.pad_conditioning_tensors_to_same_length([conditioning, negative_conditioning])
image = pipe(prompt_embeds=conditioning, negative_propmt_embeds=negative_conditioning, num_inference_steps=1000).images[0]
image.save("testCompeln2-1.png")

# with lpw_stable_diffusion
# image = pipe.text2img(prompt, negative_prompt=neg_prompt, width=512,height=512,max_embeddings_multiples=3, num_inference_steps=1000).images[0]
# image.save("testLPW.png")

# image = pipe(prompt, num_inference_steps=1000).images[0]
# image.save("test2.png")