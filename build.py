#!/usr/bin/env python3
import os
import sys
import markdown
import frontmatter
import bibtexparser

from datetime import datetime
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode
from jinja2 import Environment, FileSystemLoader
from bs4 import BeautifulSoup


def setup_environment():
    """Initialize and return the Jinja environment."""
    return Environment(loader=FileSystemLoader('template'))


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


def process_file(filepath, env, source_dir, output_dir):
    # Calculate path relative to the 'md' directory
    rel_path        = os.path.relpath(filepath, source_dir)
    normalized_path = rel_path.replace(os.sep, '/')
    filename        = os.path.basename(normalized_path)

    # Calculate path prefix for assets based on directory depth
    depth = normalized_path.count('/')
    prefix = '../' * depth if depth > 0 else ''

    # Parse YAML frontmatter and markdown
    post            = frontmatter.load(filepath)
    md              = markdown.Markdown(extensions=['toc'])
    html_content    = md.convert(post.content)
    toc_html        = md.toc

    # 1. Base context starts with values in the YAML frontmatter
    context = post.metadata.copy()

    # 2. Inject calculated routing variables
    context.update({
        'content': html_content,
        'toc_html': md.toc,
        'PATH_PREFIX': prefix,
        'IS_HOME': (filename == 'index.md' and depth == 0),
        'IS_PROJECTS': 'projects.md' in normalized_path,
        'IS_TEACHING': 'teaching.md' in normalized_path,
        'IS_TEAM': 'team.md' in normalized_path or '/team/' in normalized_path,
        'IS_PUBLICATIONS': 'publications.md' in normalized_path,
        'BUILD_DATE': datetime.now().strftime("%B %d, %Y"), # e.g., "March 26, 2026"
    })

    # 3. Parse BibTeX files
    all_pubs = []
    bib_filename = post.get('bib_file')

    if bib_filename:
        try:
            all_pubs = parse_bibtex(bib_filename)
            context['publications'] = all_pubs
        except FileNotFoundError:
            print(f"Warning: BibTeX file '{bib_filename}' not found for {filepath}")

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

    # Parse the HTML and format it with proper indentation
    soup = BeautifulSoup(final_html, 'html.parser')
    pretty_html = soup.prettify()

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(pretty_html)

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
