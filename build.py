#!/usr/bin/env python3
import os
import sys
import markdown
import frontmatter
import bibtexparser
import subprocess

from l2m4m import LaTeX2MathMLExtension
from datetime import datetime, timezone
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode
from jinja2 import Environment, FileSystemLoader

# Markdown extension imports
from markdown.extensions import Extension
from markdown.blockprocessors import BlockProcessor
from markdown.util import AtomicString
import xml.etree.ElementTree as etree

# Block processor for usage with extensions such as MathML
import re
from markdown.blockprocessors import BlockProcessor
import xml.etree.ElementTree as etree

class MacroBlockProcessor(BlockProcessor):
    """Generic processor to replace a [TAG] with pre-rendered HTML."""
    def __init__(self, parser, tag, html):
        super().__init__(parser)
        self.tag = tag
        self.html = html

    def test(self, parent, block):
        return block.strip() == self.tag

    def run(self, parent, blocks):
        blocks.pop(0) # Remove the [TAG] line
        if self.html:
            # We wrap the HTML in a div to ensure it's valid XML for the parser
            div = etree.SubElement(parent, 'div')
            # Use a placeholder that we will replace later or inject as raw
            # In python-markdown, the easiest way for raw HTML in blocks:
            placeholder = self.parser.md.htmlStash.store(self.html)
            div.text = placeholder


class MacroExtension(markdown.Extension):
    def __init__(self, **kwargs):
        self.config = {
            'pub_html': ['', 'HTML for publications'],
            'contact_html': ['', 'HTML for contact info']
        }
        super().__init__(**kwargs)

    def extendMarkdown(self, md):
        md.parser.blockprocessors.register(
            MacroBlockProcessor(md.parser, '[PUBL]', self.getConfig('pub_html')),
            'publ_macro', 175
        )
        md.parser.blockprocessors.register(
            MacroBlockProcessor(md.parser, '[CONTACT]', self.getConfig('contact_html')),
            'contact_macro', 176
        )


def setup_environment(template_dir):
    """Initialize and return the Jinja environment."""
    return Environment(loader=FileSystemLoader(template_dir),
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


def process_file(filepath, env, source_dir, output_dir, site_tz=None):
    # Calculate path relative to the source directory
    rel_path = os.path.relpath(filepath, source_dir)
    normalized_rel_path = rel_path.replace(os.sep, '/')
    filename = os.path.basename(normalized_rel_path)

    # Calculate path prefix for assets based on directory depth
    depth = normalized_rel_path.count('/')
    prefix = '../' * depth if depth > 0 else ''

    # 1. Base context starts with values in the YAML frontmatter
    post    = frontmatter.load(filepath)
    context = post.metadata.copy()

    # Render contact HTML from template
    # TODO: do this only for team websites?
    contact_template = env.get_template('contact.tmpl')
    contact_html = contact_template.render(
        role=post.metadata.get('role'),
        email=post.metadata.get('email'),
        office=post.metadata.get('office'),
        phone=post.metadata.get('phone'),
        orcid=post.metadata.get('orcid'),
        github=post.metadata.get('github'),
        scholar=post.metadata.get('scholar'),
        social=post.metadata.get('social'),
        PATH_PREFIX=prefix
    )

    # 2. Parse BibTeX files
    all_pubs = []
    bib_filename  = post.metadata.get('bibtex')
    last_modified = get_last_modified(filepath)
    pub_html = ""

    if bib_filename:
        try:
            # Use path relative to the markdown file
            md_dir = os.path.dirname(filepath)
            bib_path = os.path.normpath(os.path.join(md_dir, bib_filename))

            # If a bib file exists, get its date and keep the most recent one
            bib_last_modified = get_last_modified(bib_path)
            last_modified = max(bib_last_modified, last_modified)

            all_pubs = parse_bibtex(bib_path)
            context['publications'] = all_pubs

            # Pre-render the publication list
            pub_template = env.get_template('pub_list.tmpl')
            pub_html = pub_template.render(publications=all_pubs)

        except FileNotFoundError:
            print(f"Warning: BibTeX file '{bib_filename}' not found for {filepath}")

            # Inject a red error box for a missing file
            pub_html = f"""
            <div style="padding: 1rem; background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; border-radius: 4px;">
                <strong>Error:</strong> The specified BibTeX file <code>{bib_filename}</code> could not be found at the resolved path.
            </div>
            """

    elif '[PUBL]' in post.content:
        # Warn the user and inject a placeholder
        print(f"Warning: '[PUBL]' tag found in {filepath}, but no 'bib_file' specified in frontmatter.")

        # Inject a yellow warning box for missing metadata
        pub_html = """
        <div style="padding: 1rem; background-color: #ffeeba; color: #856404; border: 1px solid #ffeeba; border-radius: 4px;">
            <strong>Warning:</strong> The <code>[PUBL]</code> keyword was used, but no <code>bib_file</code> was defined in the page frontmatter.
        </div>
        """

    # Convert Markdown, injecting the publication list
    md = markdown.Markdown(extensions=[
        'toc','extra','codehilite',LaTeX2MathMLExtension(),
        MacroExtension(pub_html=pub_html, contact_html=contact_html)
    ])
    html_content = md.convert(post.content)
    toc_html     = md.toc

    # 3. Inject calculated routing variables
    context.update({
        'content': html_content,
        'toc_html': toc_html,
        'pub_html': pub_html,
        'PATH_PREFIX': prefix,
        'BUILD_DATE': last_modified.astimezone(site_tz).strftime("%B %d, %Y"),
        'IS_HOME': (filename == 'index.md' and depth == 0),
        'IS_PROJECTS': 'projects.md' in normalized_rel_path,
        'IS_TEACHING': 'teaching.md' in normalized_rel_path,
        'IS_TEAM': 'team.md' in normalized_rel_path or '/team/' in normalized_rel_path,
        'IS_PUBLICATIONS': 'publications.md' in normalized_rel_path,
    })

    # 4. Dynamically load the requested template
    layout_choice = post.metadata.get('layout', 'base')

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
    env = setup_environment('layout')
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
