#!/usr/bin/env python3
import os
import sys
import markdown
import frontmatter
import bibtexparser

from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode
from jinja2 import Environment, FileSystemLoader
from bs4 import BeautifulSoup


def setup_environment():
    """Initialize and return the Jinja environment."""
    env = Environment(loader=FileSystemLoader('template'))

    return {
        'base': env.get_template('base.tmpl'),
        'profile': env.get_template('profile.tmpl'),
        'team': env.get_template('team.tmpl'),
        'publications': env.get_template('publications.tmpl')
    }


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


def process_file(filepath, templates, source_dir, output_dir):
    # Calculate path relative to the 'md' directory
    rel_path        = os.path.relpath(filepath, source_dir)
    normalized_path = rel_path.replace(os.sep, '/')
    filename        = os.path.basename(normalized_path)

    # Calculate path prefix for assets based on directory depth
    depth = normalized_path.count('/')
    prefix = '../' * depth if depth > 0 else ''

    # Determine active menu states
    is_home = (filename == 'index.md' and depth == 0)
    is_projects     = 'projects.md' in normalized_path
    is_teaching     = 'teaching.md' in normalized_path
    is_team         = 'team.md' in normalized_path or '/team/' in normalized_path
    is_publications = 'publications.md' in normalized_path

    # Parse YAML frontmatter and markdown
    post            = frontmatter.load(filepath)
    md              = markdown.Markdown(extensions=['toc'])
    html_content    = md.convert(post.content)
    toc_html        = md.toc

    # Parse BibTeX files
    all_pubs = []
    bib_filename = post.get('bib_file')

    if bib_filename:
        try:
            all_pubs = parse_bibtex(bib_filename)
        except FileNotFoundError:
            print(f"Warning: BibTeX file '{bib_filename}' not found for {filepath}")

    layout_choice = post.get('layout', 'base')

    # Select and render the template
    if layout_choice == 'publications':
       final_html = templates['publications'].render(
           title=post.get('title', 'Publications'),
           content=html_content,
           publications=all_pubs,
           PATH_PREFIX=prefix,
           IS_HOME=is_home,
           IS_PROJECTS=is_projects,
           IS_TEACHING=is_teaching,
           IS_TEAM=is_team,
           IS_PUBLICATIONS=is_publications
       )
    elif layout_choice == 'profile':
        final_html = templates['profile'].render(
            title=post.get('title', 'Team Member'),
            role=post.get('role', ''),
            photo=post.get('photo', ''),
            toc_html=toc_html,
            content=html_content,
            PATH_PREFIX=prefix,
            IS_HOME=is_home,
            IS_PROJECTS=is_projects,
            IS_TEACHING=is_teaching,
            IS_TEAM=is_team,
            IS_PUBLICATIONS=is_publications
        )
    elif layout_choice == 'team':
        final_html = templates['team'].render(
            title=post.get('title', 'Team'),
            content=html_content,
            members=post.get('members', []),
            affiliates=post.get('affiliates', []),
            PATH_PREFIX=prefix,
            IS_HOME=is_home,
            IS_PROJECTS=is_projects,
            IS_TEACHING=is_teaching,
            IS_TEAM=is_team,
            IS_PUBLICATIONS=is_publications
        )
    elif layout_choice == 'base':
        final_html = templates['base'].render(
            title=post.get('title', 'Page'),
            content=html_content,
            PATH_PREFIX=prefix,
            IS_HOME=is_home,
            IS_PROJECTS=is_projects,
            IS_TEACHING=is_teaching,
            IS_TEAM=is_team,
            IS_PUBLICATIONS=is_publications
        )
    else:
        print(f"build.py: unsupported layout: {layout_choice}")
        sys.exit(1)

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
    templates = setup_environment()
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
        process_file(f, templates, source_dir, output_dir)
