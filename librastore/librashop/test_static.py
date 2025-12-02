#!/usr/bin/env python3
"""
Quick test to verify static files configuration
Run this while the server is running
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'librashop.settings')
django.setup()

from django.conf import settings
from pathlib import Path

print("=" * 60)
print("  Django Static Files Configuration Test")
print("=" * 60)
print()

print("📁 Settings:")
print(f"  BASE_DIR: {settings.BASE_DIR}")
print(f"  DEBUG: {settings.DEBUG}")
print()

print("🖼️  Static Files:")
print(f"  STATIC_URL: {settings.STATIC_URL}")
print(f"  STATIC_ROOT: {settings.STATIC_ROOT}")
print(f"  STATICFILES_DIRS: {settings.STATICFILES_DIRS}")
print()

print("📦 Media Files:")
print(f"  MEDIA_URL: {settings.MEDIA_URL}")
print(f"  MEDIA_ROOT: {settings.MEDIA_ROOT}")
print()

print("✓ File Existence Checks:")
static_dir = Path(settings.STATICFILES_DIRS[0])
media_dir = Path(settings.MEDIA_ROOT)

print(f"  Static dir exists: {static_dir.exists()} ({static_dir})")
print(f"  Media dir exists: {media_dir.exists()} ({media_dir})")
print()

# Check specific files
video_file = static_dir / 'videos' / 'promo.mp4'
print(f"  Video file exists: {video_file.exists()}")
if video_file.exists():
    print(f"    → {video_file}")
    print(f"    → Size: {video_file.stat().st_size:,} bytes")
    print(f"    → URL should be: {settings.STATIC_URL}videos/promo.mp4")
print()

# Check media files
products_dir = media_dir / 'products'
if products_dir.exists():
    image_files = list(products_dir.rglob('*.png')) + list(products_dir.rglob('*.jpg'))
    print(f"  Found {len(image_files)} product images")
    if image_files:
        print(f"  Example: {image_files[0].relative_to(media_dir)}")
        print(f"    → URL should be: {settings.MEDIA_URL}{image_files[0].relative_to(media_dir)}")
print()

print("🌐 Expected URLs:")
print(f"  Static video: http://localhost:8080{settings.STATIC_URL}videos/promo.mp4")
print(f"  Media example: http://localhost:8080{settings.MEDIA_URL}products/...")
print()

print("=" * 60)
print("If files exist but URLs return 404, check:")
print("  1. Server is running with DEBUG=True")
print("  2. urls.py includes static() configuration")
print("  3. Restart the server after changes")
print("=" * 60)
