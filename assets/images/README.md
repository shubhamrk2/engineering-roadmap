# Image Generation

> **Status: not in use.** AUTOMATIC1111 was trialled for generating the page images and
> then dropped. See "Why we stopped" below. The prompts are kept in `prompts.txt` in case
> the decision is revisited on a machine with more VRAM.

## Why we stopped

Three reasons, in order of how much they mattered:

1. **One GPU, one workload.** On a 4 GB card (RTX 2050), Stable Diffusion with `--medvram`
   holds most of the available VRAM. Ollama — which the roadmap actually depends on for
   Sheet 12's RAG work — then falls back to CPU and runs roughly ten times slower. You
   cannot usefully run both, and Ollama is the one that earns its place.
2. **Batch generation was not actually batch.** The "Prompts from file" script works, but
   each image still needed reviewing, regenerating and renaming by hand. Sixteen images was
   several hours of babysitting for decorative headers.
3. **The images were decorative.** Nothing on any sheet depends on them. The SVG drawings
   carry all the actual information.

## If you want to remove it

AUTOMATIC1111 is self-contained — no registry entries, no service, no uninstaller. The
folder is the installation.

```powershell
# 1. Find it
Get-ChildItem -Path C:\ -Filter "stable-diffusion-webui" -Directory -Recurse `
  -ErrorAction SilentlyContinue | Select-Object -First 3 FullName

$sd = "C:\path\to\stable-diffusion-webui"

# 2. Check what you are about to reclaim
"{0:N1} GB" -f ((Get-ChildItem $sd -Recurse -File -ErrorAction SilentlyContinue |
  Measure-Object -Property Length -Sum).Sum / 1GB)

# 3. Rescue anything you generated
Copy-Item "$sd\outputs" "$env:USERPROFILE\Pictures\sd-outputs" -Recurse

# 4. Delete
Remove-Item $sd -Recurse -Force

# 5. Caches it left outside the folder - often several more GB
Remove-Item "$env:USERPROFILE\.cache\huggingface" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$env:USERPROFILE\.cache\torch"       -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$env:LOCALAPPDATA\pip\Cache"         -Recurse -Force -ErrorAction SilentlyContinue

# 6. Python 3.10 was installed only for this. Confirm 3.12 is present first:
py --list
#    then: Settings -> Apps -> Installed apps -> Python 3.10.9 -> Uninstall

# 7. Confirm the GPU is free
nvidia-smi
#    Memory-Usage should return to the desktop baseline (~680 MiB) with no python.exe
```

Expect to reclaim 10–30 GB.

## If you revisit this later

On a card with 8 GB or more you can run both, and the batch workflow below works:

1. Open http://127.0.0.1:7860
2. **txt2img** tab
3. Scroll to **Script** at the bottom
4. Select **"Prompts from file or textbox"**
5. **Upload file** → `prompts.txt`
6. **Generate**

Output lands in `stable-diffusion-webui\outputs\txt2img-images\`. Rename per the map below
and copy into this folder.

## Image map (prompt number → filename → page)

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
