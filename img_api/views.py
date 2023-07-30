import base64
from decouple import config
from django.shortcuts import get_object_or_404, render, HttpResponse
import requests,json,os
from .models import GeneratedImage
from django.core.files.base import ContentFile

# def home(request):
#     return render(request, 'includes/index.html')

def galleryView(request):
    generated_images = GeneratedImage.objects.all().order_by('-created_at')
    return render(
        request, "img_api/img_gallery.html", {"old_image_objects": generated_images}
    )

def detailView(request,id=None):
    obj = get_object_or_404(GeneratedImage,id=id)
    return render(request,'img_api/image.html',{ "image_object":obj})


def generateView(request):
    context = {}
    if request.method == "POST":
        prompt = request.POST.get("text")
        number = int(request.POST.get("number"))
        style = request.POST.get('art_style')
        print(style)
        if len(prompt) > 250:
            return HttpResponse("ValidText is required(max len 250).", status=400)

        # Generate images using API
        api_response = generate_images(prompt,number,style)
        # with open(r'.\media\response_api.json','r') as f:
        #     api_response = json.load(f)
        if api_response:
            
            user = request.user if request.user.is_authenticated else None
                    # image=ImageFile(open(image_path, 'rb')),
            new_img_objects = []
            for i, image in enumerate(api_response):
                image_data = base64.b64decode(image["base64"])
                img_name = f"v40_txt2img_{i}.png"
                image_file = ContentFile(image_data, name=img_name)
                generated_image = GeneratedImage.objects.create(
                    user=user,
                    image=image_file,
                    text=prompt,
                )
                generated_image.save()
                new_img_objects.append(generated_image)
            
            context['new_image_objects'] = new_img_objects
            context['prompt']=prompt      
        else:
            return HttpResponse("Image generation failed.", status=500)

    if request.user.is_authenticated:
        generated_images_old = GeneratedImage.objects.filter(user=request.user)
        context["old_image_objects"] = generated_images_old

    return render(request, "img_api/img_get.html", context)


def generate_images(prompt,number,style):
    
    api_key = os.environ.get('API_TOI')
    api_host = 'https://api.stability.ai'
    engine_id = "stable-diffusion-v1-5"
    if api_key is None:
        raise Exception("Missing Stable API key.")
    response = requests.post(
        f"{api_host}/v1/generation/{engine_id}/text-to-image",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        json={
            "text_prompts": [{"text": prompt}],
            "cfg_scale": 7,
            "clip_guidance_preset": "FAST_BLUE",
            "style_preset": style,
            "height": 512,
            "width": 512,
            "samples": int(number),  # Number of images
            "steps": 30,
        },
    )
    if response.status_code != 200:
        error_message = "Non-200 response: " + str(response)
        return HttpResponse(error_message, status=response.status_code)
    
    data = response.json()
    return data.get("artifacts", [])

# def save_generated_images(api_response):
#     saved_image_data = {"image_data": []}
    
#     for i, image in enumerate(generated_images):
#         image_data = base64.b64decode(image["base64"])
#         saved_image_data["image_data"].append(image_data)
    
#     return saved_image_data
