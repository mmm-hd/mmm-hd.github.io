#!/usr/bin/env python3
import os
import sys
import markdown
import frontmatter
import bibtexparser
import subprocess

from l2m4m import LaTeX2MathMLExtension
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode
from jinja2 import Environment, FileSystemLoader


def setup_environment():
    """Initialize and return the Jinja environment."""
    return Environment(loader=FileSystemLoader('template'),
                       trim_blocks=True,    # Removes the first newline after a block
                       lstrip_blocks=True   # Strips tabs and spaces from the start of a line to a block
    )


def parse_bibtex(bib_filename):
    with open(bib_filename, 'r', encoding='utf-8') as bib_file:
        # 1. Initialize the custom parser
        parser = BibTexParser()

        # 2. Assign the unicode conversion rule
        parser.customization = convert_to_unicode

        # 3. Load the database using the custom parser
        bib_database = bibtexparser.load(bib_file, parser=parser)
        all_pubs = sorted(bib_database.entries, key=lambda x: x.get('year', '0'), reverse=True)

        # 4. Clean up structural newlines and double spaces
        for pub in all_pubs:
            for key, value in pub.items():
                if isinstance(value, str):
                    # We no longer need to manually strip '{' and '}' here!
                    clean_val = value.replace('\n', ' ').strip()
                    pub[key] = " ".join(clean_val.split())

        return all_pubs


def get_last_modified(filepath):
    """
    Fetch the last git commit date as seconds expired since epoch (UTC.)
    Falls back to the OS-level file modification time if untracked.

    Args:
        filepath (str): Path to the file.
        target_tz (tzinfo, optional): The target timezone. Defaults to system local time.
    """
    try:
        # %s returns the UNIX timestamp (seconds since epoch in UTC)
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%cd', '--date=format:%s', '--', filepath],
            capture_output=True, text=True, check=True
        )
        git_timestamp = result.stdout.strip()

        if git_timestamp:
            return datetime.fromtimestamp(int(git_timestamp), tz=timezone.utc)
        else:
            # Command succeeded, but no history exists for this file
            print(f"Warning: '{filepath}' is not tracked by Git. Using OS modified time.")

    except Exception as e:
        # Command failed completely (e.g., Git not installed, or not a repo)
        print(f"Warning: Git check failed for '{filepath}' ({e}). Using OS modified time.")

    # Fallback: Read the file's last-modified date directly from the filesystem
    file_timestamp = os.path.getmtime(filepath)
    return datetime.fromtimestamp(file_timestamp, tz=timezone.utc)


def process_file(filepath, env, source_dir, output_dir, target_tz=None):
    # Calculate path relative to the 'md' directory
    rel_path = os.path.relpath(filepath, source_dir)
    normalized_rel_path = rel_path.replace(os.sep, '/')
    filename = os.path.basename(normalized_rel_path)

    # Calculate path prefix for assets based on directory depth
    depth = normalized_rel_path.count('/')
    prefix = '../' * depth if depth > 0 else ''

    # Parse YAML frontmatter and markdown
    post            = frontmatter.load(filepath)
    md              = markdown.Markdown(extensions=['toc','extra','codehilite',LaTeX2MathMLExtension()])
    html_content    = md.convert(post.content)
    toc_html        = md.toc

    # Define canonical site timezone
    site_tz = ZoneInfo("Europe/Berlin")

    # 1. Base context starts with values in the YAML frontmatter
    context = post.metadata.copy()

    # 2. Parse BibTeX files
    all_pubs = []
    bib_filename = post.get('bib_file')
    last_modified = get_last_modified(filepath)

    if bib_filename:
        try:
            # If a bib file exists, get its date and keep the most recent one
            bib_last_modified = get_last_modified(bib_filename)
            last_modified = max(bib_last_modified, last_modified)

            all_pubs = parse_bibtex(bib_filename)
            context['publications'] = all_pubs
        except FileNotFoundError:
            print(f"Warning: BibTeX file '{bib_filename}' not found for {filepath}")

    # 3. Inject calculated routing variables
    context.update({
        'content': html_content,
        'toc_html': md.toc,
        'PATH_PREFIX': prefix,
        'BUILD_DATE': last_modified.astimezone(site_tz).strftime("%B %d, %Y"),
        'IS_HOME': (filename == 'index.md' and depth == 0),
        'IS_PROJECTS': 'projects.md' in normalized_rel_path,
        'IS_TEACHING': 'teaching.md' in normalized_rel_path,
        'IS_TEAM': 'team.md' in normalized_rel_path or '/team/' in normalized_rel_path,
        'IS_PUBLICATIONS': 'publications.md' in normalized_rel_path,
    })

    # 4. Dynamically load the requested template
    layout_choice = post.get('layout', 'base')

    try:
        template = env.get_template(f"{layout_choice}.tmpl")
    except Exception:
        print(f"Warning: Template '{layout_choice}.tmpl' not found. Falling back to 'base.tmpl'.")
        template = env.get_template("base.tmpl")

    # 5. Render the template
    final_html = template.render(**context)

    # Save the output
    output_rel_path = rel_path.replace('.md', '.html')
    output_path = os.path.join(output_dir, output_rel_path)

    # Ensure the target directory structure exists before writing
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Print the HTML
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_html)

    print(f"Built: {output_path}")


if __name__ == "__main__":
    env = setup_environment()
    files_to_build = sys.argv[1:]
    source_dir = 'md'
    output_dir = '.'

    if not files_to_build:
        # Fallback: build everything if no arguments are provided
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                if file.endswith('.md'):
                    files_to_build.append(os.path.join(root, file))

    for f in files_to_build:
        process_file(f, env, source_dir, output_dir)
