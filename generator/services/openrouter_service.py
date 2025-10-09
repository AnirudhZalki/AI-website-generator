# website_generator/services/openrouter_service.py
import os
import requests
from typing import Dict, List, Optional
from django.conf import settings


class OpenRouterService:
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.default_model = "anthropic/claude-3.5-sonnet"  # or "openai/gpt-4"

    def _make_request(self, messages: List[Dict], model: str = None,
                      temperature: float = 0.7, max_tokens: int = 8000) -> Dict:
        """Make request to OpenRouter API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": settings.SITE_URL,
            "X-Title": "Django AI Website Generator"
        }

        payload = {
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

            return {
                "success": True,
                "content": data["choices"][0]["message"]["content"],
                "tokens_used": data.get("usage", {}).get("total_tokens", 0),
                "model": data.get("model", model)
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "content": None
            }

    def generate_static_website(self, description: str,
                                preferences: Optional[Dict] = None) -> Dict:
        """Generate a static website"""
        system_prompt = """You are an expert web developer specializing in creating modern, 
responsive, and accessible static websites. Generate clean HTML5, CSS3, and vanilla JavaScript code.

Requirements:
- Use semantic HTML5
- Modern CSS (Flexbox, Grid, CSS Variables)
- Responsive design (mobile-first)
- Accessibility best practices
- Clean, commented code
- Single HTML file with inline CSS and JavaScript"""

        user_prompt = f"""Create a static website with the following description:
{description}

{f"Additional preferences: {preferences}" if preferences else ""}

Provide a complete, production-ready HTML file with inline CSS and JavaScript.
Include comments explaining key sections."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        return self._make_request(messages, max_tokens=12000)

    def generate_fullstack_website(self, description: str,
                                   features: Dict, stack: str) -> Dict:
        """Generate a full-stack website"""

        # Stack-specific system prompts
        stack_prompts = {
            'react_node': """You are an expert full-stack developer specializing in React and Node.js.
Generate production-ready code with:
- React frontend (functional components, hooks)
- Express.js backend with RESTful API
- Proper project structure
- Error handling and validation
- Security best practices""",

            'nextjs': """You are an expert Next.js developer.
Generate a complete Next.js application with:
- App Router or Pages Router (specify which)
- API routes for backend
- Server and client components
- TypeScript (if applicable)
- Proper data fetching patterns""",

            'django_react': """You are an expert full-stack developer specializing in Django and React.
Generate production-ready code with:
- Django REST Framework backend
- React frontend
- Proper authentication
- CORS configuration
- Serializers and viewsets"""
        }

        system_prompt = stack_prompts.get(stack, stack_prompts['react_node'])

        # Build feature requirements
        feature_list = []
        if features.get('has_authentication'):
            feature_list.append("User authentication (JWT or session-based)")
        if features.get('has_database'):
            feature_list.append("Database integration with proper models/schema")
        if features.get('has_api'):
            feature_list.append("RESTful API with CRUD operations")
        if features.get('has_realtime'):
            feature_list.append("Real-time updates (WebSockets)")
        if features.get('has_payments'):
            feature_list.append("Payment integration (Stripe)")

        features_text = "\n- ".join(feature_list)

        user_prompt = f"""Create a full-stack website with the following requirements:

Description: {description}

Required Features:
- {features_text}

Tech Stack: {stack}

Provide separate files with clear filename headers:
1. Frontend code (components, pages)
2. Backend code (server, routes, controllers)
3. Database schema/models
4. Configuration files (.env.example, package.json, requirements.txt)
5. README.md with setup instructions

Format each file like this:
// filename: frontend/App.jsx
[code here]

// filename: backend/server.js
[code here]

Ensure all code is production-ready with proper error handling, validation, and security."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        return self._make_request(messages, max_tokens=16000)

    def improve_code(self, current_code: str, improvement_request: str,
                     file_type: str = "general") -> Dict:
        """Improve existing code based on user feedback"""
        system_prompt = f"""You are an expert code reviewer and developer.
Improve the provided {file_type} code based on user feedback.
Maintain the overall structure while implementing the requested changes.
Provide the complete improved code."""

        user_prompt = f"""Current code:
```
{current_code}
```

Improvement request: {improvement_request}

Provide the complete improved code with explanations of what changed."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        return self._make_request(messages)

    def convert_static_to_fullstack(self, static_code: str,
                                    required_features: Dict, stack: str) -> Dict:
        """Convert a static website to full-stack"""
        system_prompt = """You are an expert full-stack developer.
Convert the provided static website into a full-stack application.
Maintain the design and frontend functionality while adding backend capabilities."""

        features_desc = []
        if required_features.get('has_database'):
            features_desc.append("Add database models for storing data")
        if required_features.get('has_authentication'):
            features_desc.append("Implement user authentication")
        if required_features.get('has_api'):
            features_desc.append("Create RESTful API endpoints")

        user_prompt = f"""Convert this static website to a full-stack application:

Static Code:
```
{static_code}
```

Target Stack: {stack}

Requirements:
{chr(10).join(f"- {f}" for f in features_desc)}

Provide:
1. Updated frontend code (integrated with backend)
2. Complete backend code
3. Database schema
4. API documentation
5. Setup instructions"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        return self._make_request(messages, max_tokens=16000)

    def generate_component(self, component_description: str,
                           framework: str = "react") -> Dict:
        """Generate a specific component"""
        system_prompt = f"""You are an expert {framework} developer.
Generate a production-ready, reusable component based on the description.
Include proper TypeScript types if applicable, and comprehensive comments."""

        user_prompt = f"""Create a {framework} component:
{component_description}

Include:
- Component code
- PropTypes/TypeScript types
- Usage example
- Styling (Tailwind or CSS)"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        return self._make_request(messages)