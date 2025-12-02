#!/usr/bin/env python3
"""
Static Files Verification Script
Checks if all static files are properly configured
"""

import os
from pathlib import Path

# Colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def check(condition, message):
    """Print check result"""
    if condition:
        print(f"{GREEN}✓{RESET} {message}")
        return True
    else:
        print(f"{RED}✗{RESET} {message}")
        return False

def warn(message):
    """Print warning"""
    print(f"{YELLOW}⚠{RESET} {message}")

def info(message):
    """Print info"""
    print(f"{BLUE}ℹ{RESET} {message}")

print("=" * 60)
print("  LibraStore Static Files Verification")
print("=" * 60)
print()

# Check current directory
current_dir = Path.cwd()
print(f"Current directory: {current_dir}")
print()

# Check if we're in the right directory
if not (current_dir / 'manage.py').exists():
    print(f"{RED}ERROR:{RESET} manage.py not found!")
    print("Please run this script from the librashop directory:")
    print("  cd /home/ranjith/Desktop/librastore/librashop")
    print("  python3 check_static.py")
    exit(1)

print("📁 Checking Directory Structure...")
print("-" * 60)

# Check static directory
static_dir = current_dir / 'static'
check(static_dir.exists(), f"static/ directory exists")

if static_dir.exists():
    # Check subdirectories
    images_dir = static_dir / 'images'
    videos_dir = static_dir / 'videos'
    banners_dir = images_dir / 'banners'
    
    check(images_dir.exists(), "static/images/ directory exists")
    check(videos_dir.exists(), "static/videos/ directory exists")
    check(banners_dir.exists(), "static/images/banners/ directory exists")
    
    # Check files
    favicon = images_dir / 'favicon.ico'
    video = videos_dir / 'promo.mp4'
    
    if check(favicon.exists(), "favicon.ico exists"):
        size = favicon.stat().st_size
        print(f"  → Size: {size:,} bytes ({size/1024:.1f} KB)")
    
    if check(video.exists(), "promo.mp4 exists"):
        size = video.stat().st_size
        print(f"  → Size: {size:,} bytes ({size/1024:.1f} KB)")
    
    # Check banner images (optional)
    banner_files = list(banners_dir.glob('*.jpg')) + list(banners_dir.glob('*.png'))
    if banner_files:
        info(f"Found {len(banner_files)} banner image(s)")
        for banner in banner_files:
            print(f"  → {banner.name}")
    else:
        info("No banner images found (using CSS gradients instead)")

print()
print("⚙️  Checking Configuration Files...")
print("-" * 60)

# Check settings.py
settings_file = current_dir / 'librashop' / 'settings.py'
if check(settings_file.exists(), "settings.py exists"):
    content = settings_file.read_text()
    
    check("STATIC_URL" in content, "STATIC_URL configured")
    check("STATICFILES_DIRS" in content, "STATICFILES_DIRS configured")
    check("MEDIA_URL" in content, "MEDIA_URL configured")
    check("MEDIA_ROOT" in content, "MEDIA_ROOT configured")
    
    # Check for correct STATIC_URL
    if "STATIC_URL = '/static/'" in content:
        check(True, "STATIC_URL has correct format ('/static/')")
    else:
        warn("STATIC_URL might not have leading slash")

# Check urls.py
urls_file = current_dir / 'librashop' / 'urls.py'
if check(urls_file.exists(), "urls.py exists"):
    content = urls_file.read_text()
    
    check("static(settings.STATIC_URL" in content, "Static files URL configured")
    check("static(settings.MEDIA_URL" in content, "Media files URL configured")

# Check .gitignore
gitignore_file = current_dir / '.gitignore'
if check(gitignore_file.exists(), ".gitignore exists"):
    content = gitignore_file.read_text()
    
    if '/static' in content and '# Note: /static is NOT ignored' not in content:
        warn(".gitignore might be blocking /static directory")
        print("  → This could prevent static files from being tracked")
    else:
        check(True, ".gitignore properly configured")

print()
print("📄 Checking Template Files...")
print("-" * 60)

# Check home.html
home_template = current_dir / 'store' / 'templates' / 'home.html'
if check(home_template.exists(), "home.html template exists"):
    content = home_template.read_text()
    
    check("{% load static %}" in content, "Template loads static tag")
    check("{% static 'videos/promo.mp4' %}" in content, "Video uses static tag")
    
    # Check if using gradients or images
    if 'linear-gradient' in content:
        info("Banners using CSS gradients (recommended)")
    elif "{% static 'images/banners/" in content:
        info("Banners using image files")

print()
print("🔧 Checking Dependencies...")
print("-" * 60)

# Check if Django is installed
try:
    import django
    check(True, f"Django installed (version {django.get_version()})")
except ImportError:
    check(False, "Django installed")
    warn("Run: pip install -r requirements.txt")

# Check requirements.txt
req_file = current_dir / 'requirements.txt'
if check(req_file.exists(), "requirements.txt exists"):
    content = req_file.read_text()
    check("Django" in content, "Django in requirements.txt")
    check("python-decouple" in content, "python-decouple in requirements.txt")

print()
print("=" * 60)
print("  Summary")
print("=" * 60)

# Final recommendations
print()
info("To start the server:")
print("  ./start_server.sh")
print()
info("Or manually:")
print("  source venv/bin/activate")
print("  python3 manage.py runserver")
print()
info("Then visit:")
print("  http://localhost:8000/")
print()
info("To test static files directly:")
print("  http://localhost:8000/static/images/favicon.ico")
print("  http://localhost:8000/static/videos/promo.mp4")
print()

print("=" * 60)
print(f"{GREEN}Verification complete!{RESET}")
print("=" * 60)
