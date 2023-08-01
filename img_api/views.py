import base64
from django.shortcuts import get_object_or_404, render, HttpResponse
import requests,json,os
from .models import GeneratedImage
from django.core.paginator import Paginator
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage


def galleryView(request):
    try:
        generated_images = GeneratedImage.objects.all().order_by('-created_at')
        regenerated_images = []
        for image_obj in generated_images:
            if not default_storage.exists(image_obj.image.name):
                # If the image file is missing, regenerate it from the saved img bytes
                image_data = image_obj.img_bytes
                if image_data:
                    img_name = f"v6_txt2img_N{image_obj.id}.png"
                    image_file = ContentFile(image_data, name=img_name)
                    image_obj.image = image_file
                    image_obj.save()
                    regenerated_images.append(image_obj)
                    print("regenerated..")
                else:
                    print("no image data bytes in object")
            else:
                regenerated_images.append(image_obj)

        paginator = Paginator(regenerated_images, 15)
        page_number = request.GET.get('page')
        page_object = paginator.get_page(page_number)

        return render(
            request, "img_api/img_gallery.html", {"page_obj": page_object}
        )
    except Exception as e:
        return HttpResponse(f"Error occurred: {str(e)}", status=500)


def detailView(request,id=None):
    try:
        obj = get_object_or_404(GeneratedImage,id=id)
        return render(request,'img_api/image.html',{"image_object":obj})
    except Exception as e:
        return HttpResponse(f"Error occurred: {str(e)}", status=500)

def generateView(request):
    context = {}
    try:
        if request.method == "POST":
            prompt = request.POST.get("text")
            number = int(request.POST.get("number"))
            style = request.POST.get('art_style')
            # print(style)#default is 3d
            if len(prompt) > 250:
                return HttpResponse("ValidText is required(max len 250).", status=400)

            # Generate images using API
            api_response = generate_images(prompt,number,style)
            # with open(r'.\media\response_api1080.json','+w') as f:
                # json.dump(api_response,f)
            # with open(r'.\media\response_api.json','r') as f:
            #     api_response = json.load(f)
            if api_response:
                
                user = request.user if request.user.is_authenticated else None
                        # image=ImageFile(open(image_path, 'rb')),
                generated_images_list = []
                for i, image in enumerate(api_response):
                    image_data = base64.b64decode(image["base64"])
                    img_name = f"v40_txt2img_{i}.png"
                    image_file = ContentFile(image_data, name=img_name)
                    generate_image = GeneratedImage(
                        user=user,
                        image=image_file,
                        text=prompt,
                        img_bytes = image_data,
                    )
                    generated_images_list.append(generate_image)

                GeneratedImage.objects.bulk_create(generated_images_list)
                context['new_image_objects'] = generated_images_list
                context['prompt']=prompt      
            else:
                return HttpResponse("Image generation failed.", status=500)

        if request.user.is_authenticated:
            generated_images_old = GeneratedImage.objects.filter(user=request.user)
            context["old_image_objects"] = generated_images_old

        print("n")
        return render(request, "img_api/img_get.html", context)
    
    except Exception as e:
        return HttpResponse(f"Error occurred: {str(e)}", status=500)


def generate_images(prompt,number,style):
    api_key = os.environ.get('API_TOI')
    api_host = 'https://api.stability.ai'
    engine_id = "stable-diffusion-v1-5"
    if api_key is None:
        raise Exception("Missing Stable API key.")
    try:

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
    
    except Exception as e:
        return None


