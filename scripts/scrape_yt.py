import yt_dlp
import os
import re
import argparse
from datetime import datetime

def sanitize_filename(name):
    """Removes invalid characters for a safe filename."""
    sanitized = re.sub(r'[^\w\-\. ]', '_', name)
    return sanitized.strip()

def escape_yaml_string(text):
    """Escapes quotes and removes newlines to keep the string safe inside double quotes."""
    if not text:
        return ""
    # Replace newlines with spaces so it stays on a single line in the frontmatter
    text = text.replace('\n', ' ').replace('\r', '')
    # Escape existing double quotes
    return text.replace('"', '\\"')

def scrape_channel(username, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    ydl_opts = {
        'extract_flat': False, # False ensures we get the full description and exact dates
        'ignoreerrors': True,
        'quiet': False,
        # 'playlist_items': '1-5', # Uncomment this to test on just the first 5 items per tab
    }
    
    # YouTube separates published content into distinct tabs
    content_tabs = ['videos', 'shorts', 'streams']
    
    # Keep track of processed video IDs to avoid creating duplicates
    processed_ids = set()

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for tab in content_tabs:
            channel_url = f"https://www.youtube.com/@{username}/{tab}"
            print(f"\nFetching metadata for {channel_url}...")
            
            info = ydl.extract_info(channel_url, download=False)

            if not info or 'entries' not in info:
                print(f"Could not find any entries in the {tab} tab.")
                continue

            entries = info['entries']
            
            for entry in entries:
                if not entry:
                    continue

                video_id = entry.get('id')
                
                # Skip if we already processed this video
                if video_id in processed_ids:
                    continue
                processed_ids.add(video_id)

                title = entry.get('title', 'Untitled')
                desc = entry.get('description', '')
                upload_date = entry.get('upload_date', '19700101') # format YYYYMMDD
                uploader = entry.get('uploader', username)

                # Parse yt-dlp date format to YYYY-MM-DD
                try:
                    dt = datetime.strptime(upload_date, '%Y%m%d')
                    formatted_date = dt.strftime('%Y-%m-%d')
                except ValueError:
                    formatted_date = '1970-01-01'

                safe_title = escape_yaml_string(title)
                safe_desc = escape_yaml_string(desc)
                safe_uploader = escape_yaml_string(uploader)
                
                # Create a clean filename: YYYY-MM-DD-Video_Title.md
                filename = f"{formatted_date}-{sanitize_filename(title)}.md"
                filepath = os.path.join(output_dir, filename)

                # Dynamically assign the tag based on the tab being scraped
                content_tag = tab if tab != 'videos' else 'vlog'

                # Construct the file payload
                content = f"""---
layout: base
title: "{safe_title}"
desc: "{safe_desc}"
figlet: youtube
date:   {formatted_date}
tags: [youtube, {content_tag}]
author: "{safe_uploader}"
---

{{% include youtube_embed.html id="{video_id}" %}}"""

                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"Created: {filename} ({tab})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape YouTube channel metadata (Videos, Shorts, Streams) into Markdown files.")
    parser.add_argument("username", help="YouTube username/handle (without the @ symbol)")
    parser.add_argument("--dir", default="youtube_metadata", help="Output directory for the markdown files")
    
    args = parser.parse_args()
    scrape_channel(args.username, args.dir)