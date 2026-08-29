# Image Generation Guide

## Image Map (prompt number → filename → page)

| # | Save as | Page |
|---|---------|------|
| 1 | index-hero.png | index.html — hero section |
| 2 | setup-laptops.png | setup.html — top |
| 3 | programming-languages.png | programming.html — top |
| 4 | frontend-ui.png | frontend.html — top |
| 5 | backend-api.png | backend.html — top |
| 6 | apis-network.png | apis.html — top |
| 7 | databases-storage.png | databases.html — top |
| 8 | aws-cloud.png | aws.html — top |
| 9 | azure-cloud.png | azure.html — top |
| 10 | devops-pipeline.png | devops.html — top |
| 11 | terraform-iac.png | terraform.html — top |
| 12 | kafka-messaging.png | messaging.html — top |
| 13 | ai-neural.png | ai.html — top |
| 14 | interview-whiteboard.png | interview.html — top |
| 15 | dsa-algorithms.png | dsa.html — top |
| 16 | projects-coding.png | projects.html — top |

## How to batch generate in AUTOMATIC1111

1. Open http://127.0.0.1:7860
2. Go to the **txt2img** tab
3. Scroll to the bottom — find the **Script** dropdown
4. Select **"Prompts from file or textbox"**
5. Click **"Upload file"** and select this file: `prompts.txt`
6. Hit **Generate**
7. All 16 images will generate one by one automatically

## After generation

Images are saved in AUTOMATIC1111's output folder:
`stable-diffusion-webui\outputs\txt2img-images\`

Rename them according to the image map above, copy to this folder (`assets/images/`), then:

```
git add .
git commit -m "add: generated images for all roadmap pages"
git push
```
