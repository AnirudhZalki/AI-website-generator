import datetime
import os
import requests
import json
import zipfile
from io import BytesIO
import re
import google.generativeai as genai
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import tempfile

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Global storage for generated websites (use database in production)
generated_websites = {}


# -----------------------------
# OpenRouter Service Functions
# -----------------------------
def call_openrouter_api(messages, model="anthropic/claude-3.5-sonnet", max_tokens=8000):
    """Generic function to call OpenRouter API"""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "Django AI Website Generator"
    }

    data = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.7
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=120)
        response.raise_for_status()
        result = response.json()
        return {
            "success": True,
            "content": result["choices"][0]["message"]["content"],
            "tokens": result.get("usage", {}).get("total_tokens", 0),
            "model": result.get("model", model)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "content": None
        }


# -----------------------------
# Code Parser Functions
# -----------------------------
def parse_generated_code(content):
    """Parse AI-generated code into separate files"""
    files = {}

    # Pattern 1: Code blocks with filename comments
    pattern1 = r'```[\w]*\n?(?://|#)\s*filename:\s*(.+?)\n(.*?)```'
    matches1 = re.finditer(pattern1, content, re.DOTALL | re.IGNORECASE)

    for match in matches1:
        filename = match.group(1).strip()
        code = match.group(2).strip()
        files[filename] = code

    # Pattern 2: Filename markers without code blocks
    pattern2 = r'(?://|#)\s*filename:\s*(.+?)\n(.*?)(?=(?://|#)\s*filename:|$)'
    matches2 = re.finditer(pattern2, content, re.DOTALL | re.IGNORECASE)

    for match in matches2:
        filename = match.group(1).strip()
        code = match.group(2).strip()
        # Remove trailing code block markers
        code = re.sub(r'```\s*$', '', code)
        if filename not in files:
            files[filename] = code

    # If no files found, treat as single HTML file
    if not files:
        # Try to extract HTML from code blocks
        html_match = re.search(r'```html\n(.*?)```', content, re.DOTALL)
        if html_match:
            files['index.html'] = html_match.group(1).strip()
        else:
            # Look for DOCTYPE
            start = content.find("<!DOCTYPE html>")
            if start != -1:
                files['index.html'] = content[start:]
            else:
                files['index.html'] = content

    return files


def categorize_file(filename):
    """Categorize file by type"""
    filename_lower = filename.lower()

    if any(x in filename_lower for x in
           ['frontend/', 'client/', 'components/', 'pages/', '.html', '.css', '.jsx', '.tsx', '.vue']):
        return 'frontend'
    elif any(x in filename_lower for x in
             ['backend/', 'server/', 'api/', 'routes/', 'controllers/', 'server.js', 'app.py', 'main.py']):
        return 'backend'
    elif any(x in filename_lower for x in ['schema', 'migration', 'seed', '.sql', 'models.py', 'models.js']):
        return 'database'
    elif any(x in filename_lower for x in ['.env', 'config', 'package.json', 'requirements.txt', 'docker']):
        return 'config'
    elif filename_lower.endswith('.md'):
        return 'docs'
    else:
        return 'other'


# -----------------------------
# Static Website Generation
# -----------------------------
def generate_local_html(title, prompt):
    """Fallback local HTML generation"""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .card {{
            backdrop-filter: blur(10px);
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}
        .animate-fade {{
            animation: fadeIn 1s ease-in;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
    </style>
</head>
<body class="font-sans text-white">
    <header class="sticky top-0 bg-white/10 backdrop-blur-lg border-b border-white/20 p-4">
        <nav class="container mx-auto flex justify-between items-center">
            <h1 class="text-2xl font-bold">{title}</h1>
            <div class="space-x-6">
                <a href="#about" class="hover:text-blue-200 transition">About</a>
                <a href="#features" class="hover:text-blue-200 transition">Features</a>
                <a href="#contact" class="hover:text-blue-200 transition">Contact</a>
            </div>
        </nav>
    </header>

    <main class="container mx-auto px-4 py-16">
        <section class="text-center mb-16 animate-fade">
            <h2 class="text-5xl font-bold mb-6">{title}</h2>
            <p class="text-xl text-blue-100 max-w-2xl mx-auto">{prompt}</p>
            <button onclick="showAlert()" class="mt-8 bg-white text-purple-600 px-8 py-3 rounded-full font-bold hover:scale-105 transition transform">
                Get Started
            </button>
        </section>

        <section id="features" class="grid md:grid-cols-3 gap-8 mb-16">
            <div class="card p-6 rounded-xl animate-fade">
                <div class="text-4xl mb-4">🚀</div>
                <h3 class="text-2xl font-bold mb-3">Fast</h3>
                <p class="text-blue-100">Lightning-fast performance and optimized loading times.</p>
            </div>
            <div class="card p-6 rounded-xl animate-fade" style="animation-delay: 0.2s">
                <div class="text-4xl mb-4">🎨</div>
                <h3 class="text-2xl font-bold mb-3">Beautiful</h3>
                <p class="text-blue-100">Stunning designs that captivate your audience.</p>
            </div>
            <div class="card p-6 rounded-xl animate-fade" style="animation-delay: 0.4s">
                <div class="text-4xl mb-4">💡</div>
                <h3 class="text-2xl font-bold mb-3">Innovative</h3>
                <p class="text-blue-100">Cutting-edge solutions for modern challenges.</p>
            </div>
        </section>

        <section id="about" class="card p-12 rounded-2xl text-center mb-16">
            <h2 class="text-3xl font-bold mb-6">About This Project</h2>
            <p class="text-lg text-blue-100 max-w-3xl mx-auto leading-relaxed">
                This website was generated as a starting template. The prompt was: "{prompt}".
                You can customize this template with your own content, colors, and functionality.
            </p>
        </section>

        <section id="contact" class="text-center">
            <h2 class="text-3xl font-bold mb-6">Get In Touch</h2>
            <form class="max-w-lg mx-auto card p-8 rounded-2xl" onsubmit="handleSubmit(event)">
                <input type="email" placeholder="Your Email" required
                       class="w-full p-3 rounded-lg bg-white/20 border border-white/30 text-white placeholder-white/60 mb-4">
                <textarea placeholder="Your Message" rows="4" required
                          class="w-full p-3 rounded-lg bg-white/20 border border-white/30 text-white placeholder-white/60 mb-4"></textarea>
                <button type="submit" class="w-full bg-white text-purple-600 py-3 rounded-lg font-bold hover:scale-105 transition transform">
                    Send Message
                </button>
            </form>
        </section>
    </main>

    <footer class="bg-black/30 backdrop-blur-lg border-t border-white/20 mt-20 py-8">
        <div class="container mx-auto text-center">
            <p class="text-blue-100">© {datetime.datetime.now().year} {title}. Generated with ZynoxGenI.</p>
        </div>
    </footer>

    <script>
        function showAlert() {{
            alert('Welcome to {title}! This is a demo website.');
        }}

        function handleSubmit(event) {{
            event.preventDefault();
            alert('Thanks for your message! This is a demo form.');
            event.target.reset();
        }}

        // Smooth scrolling for navigation links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
            anchor.addEventListener('click', function (e) {{
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {{
                    target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                }}
            }});
        }});

        // Intersection Observer for animations
        const observerOptions = {{
            threshold: 0.1,
            rootMargin: '0px 0px -100px 0px'
        }};

        const observer = new IntersectionObserver((entries) => {{
            entries.forEach(entry => {{
                if (entry.isIntersecting) {{
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }}
            }});
        }}, observerOptions);

        document.querySelectorAll('.card').forEach(el => observer.observe(el));
    </script>
</body>
</html>"""
    return html


def generate_static_website(title, prompt, preferences=None):
    """Generate a static website using OpenRouter"""
    system_prompt = """You are an expert web designer specializing in creating modern, responsive websites.

CRITICAL REQUIREMENTS:
- Create a COMPLETE single-file HTML document with ALL code inline
- Put ALL CSS inside <style> tags in the <head>
- Put ALL JavaScript inside <script> tags at the end of <body>
- Use Tailwind CSS via CDN: <script src="https://cdn.tailwindcss.com"></script>
- Include semantic HTML5 (header, nav, main, sections, footer)
- Add a sticky navigation with smooth scrolling
- Make it fully responsive (mobile-first design)
- Use modern design principles (proper spacing, typography, colors)
- Include interactive elements with vanilla JavaScript
- NO placeholders - use meaningful content based on the prompt
- Add accessibility features (ARIA labels, semantic HTML)
- NO external CSS or JS files - everything must be inline

IMPORTANT: Output ONLY ONE complete HTML file with everything included. Do NOT create separate CSS or JS files.
Start with <!DOCTYPE html> and end with </html>."""

    user_prompt = f"""Create a professional single-file website:

Title: {title}
Description: {prompt}

{f"Additional preferences: {preferences}" if preferences else ""}

CRITICAL: Generate ONE complete HTML file with:
1. <!DOCTYPE html> declaration
2. Complete <head> with:
   - Meta tags
   - Title
   - Tailwind CDN: <script src="https://cdn.tailwindcss.com"></script>
   - ALL custom CSS in <style> tags
3. Complete <body> with:
   - All HTML content
   - ALL JavaScript in <script> tags at the end
4. </html> closing tag

Do NOT create separate files. Everything must be in ONE HTML file.
Make it visually stunning and fully functional."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    result = call_openrouter_api(messages, model="gpt-4o", max_tokens=16000)

    if result['success']:
        content = result['content']
        # Extract HTML - try multiple patterns

        # Pattern 1: Look for <!DOCTYPE html>
        start = content.find("<!DOCTYPE html>")
        if start == -1:
            # Pattern 2: Look for <html
            start = content.find("<html")
        if start == -1:
            # Pattern 3: Look for ```html code block
            html_match = re.search(r'```html\s*(<!DOCTYPE html>.*?)```', content, re.DOTALL | re.IGNORECASE)
            if html_match:
                html_content = html_match.group(1)
            else:
                # Pattern 4: Just take everything in code block
                html_match = re.search(r'```html?\s*(.*?)```', content, re.DOTALL | re.IGNORECASE)
                if html_match:
                    html_content = html_match.group(1)
                else:
                    html_content = content
        else:
            html_content = content[start:]

        # Ensure Tailwind CDN is included
        if 'cdn.tailwindcss.com' not in html_content and '<head>' in html_content:
            # Inject Tailwind CDN
            html_content = html_content.replace(
                '<head>',
                '<head>\n  <script src="https://cdn.tailwindcss.com"></script>'
            )

        return {
            "success": True,
            "html": html_content.strip(),
            "tokens": result['tokens'],
            "model": result['model']
        }

    return {
        "success": False,
        "error": result.get('error', 'Failed to generate HTML')
    }


# -----------------------------
# Full-Stack Website Generation
# -----------------------------
def generate_fullstack_website(title, prompt, stack, features):
    """Generate a full-stack website"""

    # Stack-specific prompts
    stack_configs = {
        'react_node': {
            'name': 'React + Node.js + Express',
            'prompt': """Create a full-stack web application with:
- Frontend: React with functional components and hooks
- Backend: Express.js with RESTful API
- Use modern ES6+ JavaScript
- Include proper error handling and validation"""
        },
        'nextjs': {
            'name': 'Next.js Full-Stack',
            'prompt': """Create a Next.js 14+ application with:
- App Router (not Pages Router)
- Server and Client Components
- API Routes for backend
- TypeScript (optional but preferred)
- Modern React patterns"""
        },
        'vue_express': {
            'name': 'Vue.js + Express',
            'prompt': """Create a full-stack web application with:
- Frontend: Vue.js 3 with Composition API
- Backend: Express.js with RESTful API
- Use modern JavaScript/TypeScript"""
        },
        'django_react': {
            'name': 'Django + React',
            'prompt': """Create a full-stack web application with:
- Backend: Django with Django REST Framework
- Frontend: React with hooks
- Proper CORS configuration
- Token-based authentication"""
        }
    }

    config = stack_configs.get(stack, stack_configs['react_node'])

    # Build feature requirements
    feature_list = []
    if features.get('has_authentication'):
        feature_list.append("- User authentication (JWT or session-based with login/register)")
    if features.get('has_database'):
        feature_list.append("- Database integration with models/schema")
    if features.get('has_api'):
        feature_list.append("- RESTful API with CRUD operations")
    if features.get('has_realtime'):
        feature_list.append("- Real-time updates using WebSockets")
    if features.get('has_payments'):
        feature_list.append("- Payment integration (Stripe setup)")

    system_prompt = f"""You are an expert full-stack developer specializing in {config['name']}.

{config['prompt']}

IMPORTANT: Provide separate files with clear filename markers like:
// filename: frontend/App.jsx
[code here]

// filename: backend/server.js
[code here]

Include:
1. Complete frontend code (components, pages, routing)
2. Complete backend code (server, routes, controllers, middleware)
3. Database schema/models
4. Configuration files (package.json, .env.example, etc.)
5. README.md with setup instructions

Ensure production-ready code with:
- Proper error handling
- Input validation
- Security best practices
- Clean code structure
- Comments explaining key sections"""

    user_prompt = f"""Create a full-stack {config['name']} application:

Project: {title}
Description: {prompt}

Required Features:
{chr(10).join(feature_list)}

Provide complete, working code for all files needed to run this application."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    result = call_openrouter_api(messages, model="gpt-4o", max_tokens=16000)

    if result['success']:
        files = parse_generated_code(result['content'])

        # Organize files by category
        organized_files = {
            'frontend': {},
            'backend': {},
            'database': {},
            'config': {},
            'docs': {}
        }

        for filename, content in files.items():
            category = categorize_file(filename)
            organized_files[category][filename] = content

        return {
            "success": True,
            "files": organized_files,
            "tokens": result['tokens'],
            "model": result['model']
        }

    return {
        "success": False,
        "error": result.get('error', 'Failed to generate full-stack website')
    }


# -----------------------------
# Convert Static to Full-Stack
# -----------------------------
def convert_to_fullstack(static_html, stack, features):
    """Convert static website to full-stack"""

    feature_desc = []
    if features.get('has_authentication'):
        feature_desc.append("User authentication with login/register")
    if features.get('has_database'):
        feature_desc.append("Database to store user data and content")
    if features.get('has_api'):
        feature_desc.append("RESTful API endpoints")

    system_prompt = """You are an expert full-stack developer.
Convert the provided static website into a full-stack application while maintaining the design and UI.

Requirements:
- Keep the existing design and styling
- Add backend functionality
- Create proper file structure
- Include all necessary configuration files
- Provide setup instructions"""

    user_prompt = f"""Convert this static website to a full-stack {stack} application:

Static HTML:
```html
{static_html[:3000]}  # Truncate if too long
```

Add these features:
{chr(10).join(f"- {f}" for f in feature_desc)}

Provide:
1. Updated frontend code (connected to backend)
2. Complete backend code
3. Database schema
4. Configuration files
5. README with setup instructions

Use filename markers for each file."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    result = call_openrouter_api(messages, model="gpt-4o", max_tokens=16000)

    if result['success']:
        files = parse_generated_code(result['content'])
        organized_files = {}
        for filename, content in files.items():
            category = categorize_file(filename)
            if category not in organized_files:
                organized_files[category] = {}
            organized_files[category][filename] = content

        return {
            "success": True,
            "files": organized_files,
            "tokens": result['tokens']
        }

    return {"success": False, "error": result.get('error')}


# -----------------------------
# Django Views
# -----------------------------
latest_html = None
latest_project = None


def home(request):
    """Main page - generate websites"""
    global latest_html, latest_project

    context = {
        'generated_html': None,
        'project_data': None,
        'error': None
    }

    if request.method == "POST":
        title = request.POST.get("title", "My Website")
        prompt = request.POST.get("prompt", "")
        mode = request.POST.get("mode", "local")
        project_type = request.POST.get("project_type", "static")

        try:
            if project_type == "static":
                # Generate static website
                if mode == "ai":
                    result = generate_static_website(title, prompt)
                    if result['success']:
                        generated_html = result['html']
                        latest_html = generated_html
                        context['generated_html'] = generated_html
                        context['tokens_used'] = result['tokens']
                    else:
                        context['error'] = result.get('error')
                else:
                    generated_html = generate_local_html(title, prompt)
                    latest_html = generated_html
                    context['generated_html'] = generated_html

            elif project_type == "fullstack":
                # Generate full-stack website
                stack = request.POST.get("stack", "react_node")
                features = {
                    'has_authentication': request.POST.get("has_authentication") == "on",
                    'has_database': request.POST.get("has_database") == "on",
                    'has_api': request.POST.get("has_api") == "on",
                    'has_realtime': request.POST.get("has_realtime") == "on",
                    'has_payments': request.POST.get("has_payments") == "on",
                }

                result = generate_fullstack_website(title, prompt, stack, features)

                if result['success']:
                    # Store in global dict (use database in production)
                    project_id = f"project_{len(generated_websites) + 1}"
                    latest_project = {
                        'id': project_id,
                        'title': title,
                        'description': prompt,
                        'type': 'fullstack',
                        'stack': stack,
                        'features': features,
                        'files': result['files'],
                        'tokens': result['tokens']
                    }
                    generated_websites[project_id] = latest_project

                    context['project_data'] = latest_project
                    context['success'] = True
                else:
                    context['error'] = result.get('error')

        except Exception as e:
            context['error'] = str(e)

    return render(request, "generator/home.html", context)


def preview(request):
    """Preview generated static website"""
    global latest_html
    if not latest_html:
        return HttpResponse("<p>No website generated yet.</p>")
    return HttpResponse(latest_html)


@csrf_exempt
def convert_static_to_fullstack_view(request):
    """Convert current static website to full-stack"""
    global latest_html

    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=400)

    if not latest_html:
        return JsonResponse({"error": "No static website to convert"}, status=400)

    try:
        data = json.loads(request.body)
        stack = data.get('stack', 'react_node')
        features = {
            'has_authentication': data.get('has_authentication', False),
            'has_database': data.get('has_database', False),
            'has_api': data.get('has_api', True),
        }

        result = convert_to_fullstack(latest_html, stack, features)

        if result['success']:
            project_id = f"project_{len(generated_websites) + 1}"
            project = {
                'id': project_id,
                'title': 'Converted Project',
                'type': 'fullstack',
                'stack': stack,
                'files': result['files'],
                'tokens': result['tokens']
            }
            generated_websites[project_id] = project

            return JsonResponse({
                "success": True,
                "project_id": project_id,
                "files": result['files']
            })
        else:
            return JsonResponse({"success": False, "error": result['error']}, status=500)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def download_project(request, project_id=None):
    """Download project as ZIP file"""
    global latest_html, latest_project

    # Create ZIP file
    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        if project_id and project_id in generated_websites:
            # Download full-stack project
            project = generated_websites[project_id]

            for category, files in project['files'].items():
                for filename, content in files.items():
                    zip_file.writestr(filename, content)

            # Add README
            readme = f"""# {project.get('title', 'Project')}

## Description
{project.get('description', 'Full-stack application')}

## Stack
{project.get('stack', 'N/A')}

## Features
{'- Authentication' if project.get('features', {}).get('has_authentication') else ''}
{'- Database' if project.get('features', {}).get('has_database') else ''}
{'- API' if project.get('features', {}).get('has_api') else ''}

## Setup
See individual file comments for setup instructions.

Generated with Django AI Website Generator
"""
            zip_file.writestr('README.md', readme)

        elif latest_html:
            # Download static website
            zip_file.writestr('index.html', latest_html)
            zip_file.writestr('README.md', '# Static Website\n\nOpen index.html in your browser.')

        else:
            return HttpResponse("No project to download", status=404)

    zip_buffer.seek(0)

    response = HttpResponse(zip_buffer.read(), content_type='application/zip')
    filename = project_id if project_id else 'static-website'
    response['Content-Disposition'] = f'attachment; filename="{filename}.zip"'
    return response


def view_project_files(request, project_id):
    """View generated files for a full-stack project"""
    if project_id not in generated_websites:
        return HttpResponse("Project not found", status=404)

    project = generated_websites[project_id]
    return render(request, "generator/project_files.html", {"project": project})


