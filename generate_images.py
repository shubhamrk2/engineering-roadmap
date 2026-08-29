import os, urllib.request, time
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

OUTPUT_DIR = r"C:\Users\shubham.bi.singh\OneDrive - Accenture\Documents\engineering-roadmap\assets\images"

images = [
    ("index-hero.png",            "futuristic server room with glowing blue and cyan network connections between servers, data flowing as light streams, dark background, cinematic lighting, photorealistic, 8k, professional photography"),
    ("setup-laptops.png",         "two laptops side by side on a clean desk, one showing VS Code with code, corporate office, dark room, soft blue monitor glow, photorealistic, cinematic, professional"),
    ("programming-languages.png", "Python JavaScript Java TypeScript programming as glowing neon code symbols floating in dark space, multiple screens with code, dark background, cyan and gold light, cinematic, photorealistic"),
    ("frontend-ui.png",           "modern dark theme web application on large ultrawide monitor, React components on second screen, developer workspace, neon blue glow, photorealistic, cinematic"),
    ("backend-api.png",           "glowing server infrastructure with API data packets flowing between nodes, dark background, cyan colored light beams, network connections, cinematic, photorealistic"),
    ("apis-network.png",          "network of glowing interconnected API service nodes, data flowing between microservices, dark background, cyan and gold colored light, cinematic visualization, photorealistic"),
    ("databases-storage.png",     "three glowing database server towers side by side in dark server room, data streams flowing into them, blue and amber lighting, photorealistic, cinematic"),
    ("aws-cloud.png",             "Amazon AWS cloud infrastructure concept, glowing orange cloud services connected by light beams, dark space background, cinematic, photorealistic, futuristic data center"),
    ("azure-cloud.png",           "Microsoft Azure cloud services visualization, blue glowing cloud data centers connected by light streams, dark background, cinematic, photorealistic, futuristic"),
    ("devops-pipeline.png",       "CI CD deployment pipeline visualization, Docker containers as glowing blue cubes, Kubernetes cluster nodes, dark background, green and cyan lights, cinematic, photorealistic"),
    ("terraform-iac.png",         "infrastructure as code concept, cloud resources materializing from glowing code lines, dark background, purple and cyan colors, cinematic, photorealistic, futuristic"),
    ("kafka-messaging.png",       "Kafka message queue visualization, glowing gold data streams flowing through broker nodes to multiple consumers, dark background, brass and amber colored light, cinematic, photorealistic"),
    ("ai-neural.png",             "artificial intelligence neural network brain visualization, RAG pipeline with glowing vector embeddings, dark background, purple cyan and gold nodes connected by light beams, cinematic, photorealistic"),
    ("interview-whiteboard.png",  "software engineer at whiteboard drawing system architecture diagram, tech company dark office, dramatic lighting, focused professional, photorealistic, cinematic"),
    ("dsa-algorithms.png",        "data structures visualization, glowing binary tree nodes, linked list, graph edges, algorithm execution paths, dark background, cyan colored nodes, cinematic, photorealistic"),
    ("projects-coding.png",       "developer working with multiple screens showing different code projects, dark room, blue monitor glow, focused, cinematic, photorealistic, professional workspace"),
]

print(f"Generating {len(images)} images...\n")

for i, (filename, prompt) in enumerate(images, 1):
    out_path = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(out_path):
        print(f"[{i}/{len(images)}] SKIP (exists): {filename}")
        continue
    try:
        print(f"[{i}/{len(images)}] Generating: {filename} ...", end=" ", flush=True)
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1792x1024",
            quality="standard",
            n=1,
        )
        url = response.data[0].url
        urllib.request.urlretrieve(url, out_path)
        print("done")
        time.sleep(1)
    except Exception as e:
        print(f"ERROR: {e}")

print("\nAll done! Check assets/images/")
