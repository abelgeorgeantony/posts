import instaloader
import os
import re
import argparse
from datetime import datetime
import time

def sanitize_filename(name):
    """Removes invalid characters for a safe filename."""
    sanitized = re.sub(r'[^\w\-\. ]', '_', name)
    # Truncate to avoid overly long filenames from long captions
    return sanitized.strip()[:50] 

def escape_yaml_string(text):
    """Escapes quotes and removes newlines to keep the string safe inside double quotes."""
    if not text:
        return ""
    text = text.replace('\n', ' ').replace('\r', '')
    return text.replace('"', '\\"')

def scrape_instagram_profile(username, output_dir, login_user=None):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Initialize Instaloader
    L = instaloader.Instaloader(
        download_pictures=False,
        download_video_thumbnails=False,
        download_videos=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False
    )

    # Logging in is highly recommended/required for Instagram
    if login_user:
        try:
            # Requires you to have run `instaloader --login YOUR_USERNAME` in terminal first
            # to save the session token, otherwise you can pass password here (not recommended)
            L.load_session_from_file(login_user)
            print(f"Loaded session for {login_user}")
        except FileNotFoundError:
            print(f"Session file for {login_user} not found. Proceeding anonymously (likely to fail).")

    print(f"Fetching profile metadata for @{username}...")
    
    try:
        profile = instaloader.Profile.from_username(L.context, username)
    except Exception as e:
        print(f"Failed to fetch profile: {e}")
        return

    # Loop through the user's posts
    for post in profile.get_posts():
        shortcode = post.shortcode
        caption = post.caption if post.caption else "Instagram Post"
        
        # Instagram dates are already datetime objects in UTC
        upload_date = post.date_utc
        formatted_date = upload_date.strftime('%Y-%m-%d')
        
        # Determine content type for tagging
        if post.is_video:
            content_tag = "reel" if post.title else "video" # title often exists for IGTV/Reels
        else:
            content_tag = "photo"

        safe_title = escape_yaml_string(caption[:60] + "..." if len(caption) > 60 else caption)
        safe_desc = escape_yaml_string(caption)
        safe_uploader = escape_yaml_string(username)

        # Create a clean filename
        filename_base = sanitize_filename(safe_title) if safe_title else shortcode
        filename = f"{formatted_date}-{filename_base}.md"
        filepath = os.path.join(output_dir, filename)

        # Construct the file payload
        content = f"""---
layout: base
title: "{safe_title}"
desc: "{safe_desc}"
figlet: instagram
date:   {formatted_date}
tags: [instagram, {content_tag}]
author: "{safe_uploader}"
shortcode: "{shortcode}"
---

{{% include instagram_embed.html shortcode="{shortcode}" %}}"""

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Created: {filename} ({content_tag})")
        
        # VERY IMPORTANT: Sleep to avoid rate limiting/bans
        time.sleep(2) 

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape Instagram metadata into Markdown files.")
    parser.add_argument("username", help="Instagram username to scrape")
    parser.add_argument("--dir", default="ig_metadata", help="Output directory for the markdown files")
    parser.add_argument("--login", default=None, help="Your Instagram username (requires pre-saved session)")
    
    args = parser.parse_args()
    scrape_instagram_profile(args.username, args.dir, args.login)