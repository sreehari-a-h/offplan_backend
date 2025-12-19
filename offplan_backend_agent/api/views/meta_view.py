import re
from django.core.cache import cache
from django.shortcuts import render
from django.http import HttpResponseRedirect
import requests
import json

CRAWLER_USER_AGENTS = re.compile(
    r"googlebot|bingbot|yandex|duckduckbot|baiduspider|facebook|twitterbot|linkedinbot|whatsapp|telegrambot|slackbot|redditbot|quora link preview|pinterest|tumblr|vkbot",
    re.I
)

def agent_meta_view(request, username):
    user_agent = request.META.get('HTTP_USER_AGENT', '')

    if CRAWLER_USER_AGENTS.search(user_agent):
        cache_key = f"agent_meta:{username}"
        meta_data = cache.get(cache_key)

        if not meta_data:
            api_url = f"https://offplan.market/api/agent/{username}/"
            try:
                response = requests.get(api_url, timeout=5)
                if response.status_code == 200 and response.json().get("status"):
                    agent = response.json()["data"]
                    
                    # Handle multilingual name properly
                    agent_name = agent.get('name', '')
                    if isinstance(agent_name, dict):
                        # Extract English name from multilingual dict
                        agent_name = agent_name.get('en', agent_name.get('english', ''))
                        if not agent_name and agent_name != '':
                            # Fallback to first available language
                            agent_name = list(agent_name.values())[0] if agent_name else 'Agent'
                    elif isinstance(agent_name, str):
                        # If it's already a string, use it as is
                        pass
                    else:
                        # Fallback if name is neither dict nor string
                        agent_name = 'Agent'
                    
                    profile_image = agent.get('profile_image_url')
                    if not profile_image:
                        profile_image = "https://offplan.market/static/default-agent.jpg"

                    # Handle multilingual bio if needed
                    agent_bio = agent.get('bio', '')
                    if isinstance(agent_bio, dict):
                        agent_bio = agent_bio.get('en', agent_bio.get('english', ''))
                        if not agent_bio and agent_bio != '':
                            agent_bio = list(agent_bio.values())[0] if agent_bio else ''
                    
                    if not agent_bio:
                        agent_bio = f"Explore premium off-plan projects with {agent_name}. Click to view listings & contact now."

                    meta_data = {
                        "title": f"{agent_name} | Offplan Expert – Offplan.Market",
                        "description": agent_bio,
                        "image": profile_image,
                        "url": request.build_absolute_uri(),
                    }
                    cache.set(cache_key, meta_data, timeout=300)
                else:
                    raise Exception("Agent not found")
            except Exception as e:
                print(f"Error fetching agent data: {e}")
                meta_data = {
                    "title": "Agent Not Found",
                    "description": "This agent profile does not exist.",
                    "image": "https://offplan.market/static/default-agent.jpg",
                    "url": request.build_absolute_uri(),
                }

        return render(request, "agent_meta_template.html", meta_data)

    react_url = f"https://offplan.market/{username}"
    return HttpResponseRedirect(react_url)

def blogs_listing_meta_view(request):
    """
    Render blogs listing page for ALL users
    """
    blogs = BlogPost.objects.all().order_by('-created_at')
    
    context = {
        "blogs": blogs,
    }
    
    return render(request, "blog_list.html", context)

from api.models import BlogPost

def blog_detail_meta_view(request, slug):
    """
    Render blog detail page with proper meta tags for ALL users (crawlers and regular users)
    """
    try:
        post = BlogPost.objects.get(slug=slug)
        
        # Handle multilingual title if needed
        post_title = post.title
        if isinstance(post_title, dict):
            post_title = post_title.get('en', post_title.get('english', ''))
            if not post_title:
                post_title = list(post_title.values())[0] if post_title else 'Blog Post'
        
        image = post.image.url if post.image else "https://offplan.market/static/default-blog.jpg"
        
        context = {
            "blog": post,
            "title": post.meta_title or post_title,
            "description": post.meta_description or (post.content[:160] if post.content else "Blog article"),
            "image": request.build_absolute_uri(image),
            "url": request.build_absolute_uri(),
        }
        
        return render(request, "blog_detail.html", context)
        
    except BlogPost.DoesNotExist:
        meta_data = {
            "title": "Blog Not Found",
            "description": "This blog post does not exist.",
            "image": "https://offplan.market/static/default-blog.jpg",
            "url": request.build_absolute_uri(),
        }
        return render(request, "meta_template.html", meta_data)

def contact_meta_view(request, username):
    user_agent = request.META.get("HTTP_USER_AGENT", "")
    if CRAWLER_USER_AGENTS.search(user_agent):
        meta_data = {
            "title": f"Contact {username.title()} - Senior Property Consultant | OFFPLAN.MARKET",
            "description": f"Get in touch with {username.title()} for expert property consultation in Dubai. Call +971 52 952 9687 or send a message for personalized real estate advice.",
            "image": "https://offplan.market/static/default-contact.jpg",
            "url": f"https://offplan.market/{username}/contact",
        }
        return render(request, "meta_template.html", meta_data)

    return HttpResponseRedirect(f"https://offplan.market/{username}/contact")

def about_meta_view(request, username):
    user_agent = request.META.get("HTTP_USER_AGENT", "")
    if CRAWLER_USER_AGENTS.search(user_agent):
        meta_data = {
            "title": f"About {username.title()} - Senior Property Consultant | OFFPLAN.MARKET",
            "description": f"Meet {username.title()}, your trusted Senior Property Consultant specializing in Dubai's off-plan real estate market. 6+ years experience, 150+ successful deals.",
            "image": "https://offplan.market/static/default-agent.jpg",
            "url": f"https://offplan.market/{username}/about",
        }
        return render(request, "meta_template.html", meta_data)

    return HttpResponseRedirect(f"https://offplan.market/{username}/about")