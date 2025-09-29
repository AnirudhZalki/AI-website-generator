from django.shortcuts import render
import datetime
import os, requests

# -----------------------------
# Local (no API, simple fallback)
# -----------------------------
def generate_local_html(title, prompt):
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="font-sans bg-gray-50 text-gray-900">
        <header class="bg-blue-600 text-white p-4 sticky top-0">
            <h1 class="text-2xl font-bold">{title}</h1>
        </header>

        <main class="p-8">
            <h2 class="text-xl font-semibold mb-4">Prompt:</h2>
            <p>{prompt}</p>

            <h2 class="text-xl font-semibold mt-8 mb-4">Generated Section:</h2>
            <p>This is an auto-generated section based on your prompt.</p>
        </main>

        <footer class="bg-gray-200 text-center p-4">
            <p>© {datetime.datetime.now().year} {title}. Built from a prompt.</p>
        </footer>
    </body>
    </html>
    """
    return html


# -----------------------------
# OpenRouter (AI generation)
# -----------------------------
def generate_html_from_openrouter(title, prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json",
    }

    system_prompt = """
    You are a senior web designer. 
    Create a COMPLETE single-file HTML document styled with Tailwind CSS (via CDN).
    Requirements:
    - Must start with <!DOCTYPE html>.
    - Include <html>, <head>, and <body>.
    - Use semantic HTML5 sections (hero, about, contact, etc. as relevant).
    - Add a sticky navigation bar with anchor links.
    - No external CSS or JS (Tailwind CDN only).
    - Avoid placeholders like lorem ipsum; use meaningful sample text.
    """

    data = {
        "model": "gpt-4o-mini",   # You can change this to "anthropic/claude-3-haiku" or others
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Title: {title}\nPrompt: {prompt}"}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        result = response.json()

        content = result["choices"][0]["message"]["content"]
        start = content.find("<!DOCTYPE html>")
        if start == -1:
            return "<p>Failed to generate HTML</p>"
        return content[start:]
    except Exception as e:
        return f"<p>Error generating HTML: {e}</p>"


# -----------------------------
# Django view
# -----------------------------
def home(request):
    generated_html = None
    if request.method == "POST":
        title = request.POST.get("title", "My Website")
        prompt = request.POST.get("prompt", "")
        mode = request.POST.get("mode", "local")  # "local" or "ai"

        if mode == "ai":
            generated_html = generate_html_from_openrouter(title, prompt)
        else:
            generated_html = generate_local_html(title, prompt)

    return render(request, "generator/home.html", {"generated_html": generated_html})
