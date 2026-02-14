#!/usr/bin/env python3
"""Extract WordPress comments from XML export into Hugo data files.

Reads approved comments from the WordPress XML export and writes one JSON
file per post to site/data/comments/<slug>.json for use in Hugo templates.
"""

import xml.etree.ElementTree as ET
import json
import hashlib
import os
import re
from datetime import datetime

XML_PATH = '/Users/michael/Downloads/WordPress.2026-02-14.xml'
OUTPUT_DIR = 'site/data/comments'

NS = {
    'content': 'http://purl.org/rss/1.0/modules/content/',
    'excerpt': 'http://wordpress.org/export/1.2/excerpt/',
    'wp': 'http://wordpress.org/export/1.2/',
    'dc': 'http://purl.org/dc/elements/1.1/',
}


def gravatar_hash(email):
    """Return MD5 hash of lowercased, stripped email for Gravatar URLs."""
    if not email:
        return ''
    return hashlib.md5(email.strip().lower().encode('utf-8')).hexdigest()


def parse_cdata(text):
    if text is None:
        return ''
    return text.strip()


def main():
    print("Parsing WordPress XML for comments...")
    tree = ET.parse(XML_PATH)
    root = tree.getroot()
    channel = root.find('channel')

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    total_comments = 0
    total_posts = 0
    skipped_pingbacks = 0
    skipped_unapproved = 0

    for item in channel.findall('item'):
        post_type = item.find('wp:post_type', NS)
        post_type = parse_cdata(post_type.text) if post_type is not None else ''
        if post_type not in ('post', 'page'):
            continue

        post_status = item.find('wp:status', NS)
        post_status = parse_cdata(post_status.text) if post_status is not None else ''
        if post_status != 'publish':
            continue

        post_name = item.find('wp:post_name', NS)
        slug = parse_cdata(post_name.text) if post_name is not None else ''
        if not slug:
            continue

        comments = []
        for comment in item.findall('wp:comment', NS):
            # Skip pingbacks and trackbacks
            comment_type = comment.find('wp:comment_type', NS)
            comment_type = parse_cdata(comment_type.text) if comment_type is not None else ''
            if comment_type in ('pingback', 'trackback'):
                skipped_pingbacks += 1
                continue

            # Only approved comments (status "1")
            approved = comment.find('wp:comment_approved', NS)
            approved = parse_cdata(approved.text) if approved is not None else ''
            if approved != '1':
                skipped_unapproved += 1
                continue

            comment_id = comment.find('wp:comment_id', NS)
            comment_id = parse_cdata(comment_id.text) if comment_id is not None else '0'

            author = comment.find('wp:comment_author', NS)
            author = parse_cdata(author.text) if author is not None else ''

            author_email = comment.find('wp:comment_author_email', NS)
            author_email = parse_cdata(author_email.text) if author_email is not None else ''

            author_url = comment.find('wp:comment_author_url', NS)
            author_url = parse_cdata(author_url.text) if author_url is not None else ''

            date = comment.find('wp:comment_date', NS)
            date = parse_cdata(date.text) if date is not None else ''

            content = comment.find('wp:comment_content', NS)
            content = parse_cdata(content.text) if content is not None else ''

            parent = comment.find('wp:comment_parent', NS)
            parent = parse_cdata(parent.text) if parent is not None else '0'

            comments.append({
                'id': comment_id,
                'author': author,
                'author_url': author_url,
                'date': date,
                'content': content,
                'parent': parent,
                'gravatar_hash': gravatar_hash(author_email),
            })

        if not comments:
            continue

        # Sort by date
        comments.sort(key=lambda c: c['date'])

        data = {
            'comment_count': len(comments),
            'comments': comments,
        }

        # Hugo data keys use underscores not hyphens
        filename = slug + '.json'
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        total_comments += len(comments)
        total_posts += 1

    print(f"\nDone!")
    print(f"Posts with comments: {total_posts}")
    print(f"Total comments extracted: {total_comments}")
    print(f"Skipped pingbacks/trackbacks: {skipped_pingbacks}")
    print(f"Skipped unapproved: {skipped_unapproved}")
    print(f"Output directory: {OUTPUT_DIR}/")


if __name__ == '__main__':
    main()
