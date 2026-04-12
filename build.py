#!/usr/bin/env python3
import os
import sys
import markdown
import frontmatter
import bibtexparser
import subprocess
import csv
import re

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


class ParamBlockProcessor(BlockProcessor):
    """Processor to replace [TAG:ID] with HTML mapped to that ID."""
    def __init__(self, parser, pattern, html_dict):
        super().__init__(parser)
        self.pattern = re.compile(pattern)
        self.html_dict = html_dict

    def test(self, parent, block):
        # Returns True if the block matches exactly [TAG:ID]
        return bool(self.pattern.match(block.strip()))

    def run(self, parent, blocks):
        block = blocks.pop(0).strip()
        match = self.pattern.match(block)
        if match:
            block_id = match.group(1)
            # Fetch the pre-rendered HTML, or a warning if the ID wasn't found
            html_content = self.html_dict.get(
                block_id,
                f"<div style='color:red;'>[Warning: No data found for ID {block_id}]</div>"
            )

            div = etree.SubElement(parent, 'div')
            placeholder = self.parser.md.htmlStash.store(html_content)
            div.text = placeholder


class MacroExtension(markdown.Extension):
    def __init__(self, **kwargs):
        self.config = {
            'pub_html': ['', 'HTML for publications'],
            'contact_html': ['', 'HTML for contact info'],
            'teaching_blocks': [{}, 'Dictionary of teaching HTML blocks']
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
        # Parameterized regex processor for [TEACHING:id]
        md.parser.blockprocessors.register(
            ParamBlockProcessor(md.parser,r'^\[TEACHING:([a-zA-Z0-9_-]+)\]$',
                self.getConfig('teaching_blocks')
            ),
            'teaching_macro', 177
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


def get_routing_info(filepath, source_dir):
    """Calculates all path-related variables for a given file."""
    rel_path = os.path.relpath(filepath, source_dir)
    norm_path = rel_path.replace(os.sep, '/')
    depth = norm_path.count('/')

    return {
        'rel_path': rel_path,
        'norm_path': norm_path,
        'filename': os.path.basename(norm_path),
        'path_prefix': '../' * depth if depth > 0 else '',
        'depth': depth
    }


def render_contact_block(metadata, env, prefix, content):
    """Renders the contact HTML only if the macro is used."""
    if '[CONTACT]' not in content:
        return ""

    contact_template = env.get_template('contact.tmpl')
    return contact_template.render(
        role=metadata.get('role'),
        email=metadata.get('email'),
        office=metadata.get('office'),
        phone=metadata.get('phone'),
        orcid=metadata.get('orcid'),
        github=metadata.get('github'),
        scholar=metadata.get('scholar'),
        social=metadata.get('social'),
        PATH_PREFIX=prefix
    )


def render_publications(metadata, filepath, env, base_last_modified, content):
    """Handles BibTeX parsing and handles missing files/tags."""
    bib_filename = metadata.get('bibtex')

    if not bib_filename:
        if '[PUBL]' in content:
            print(f"Warning: '[PUBL]' tag found in {filepath}, but no 'bibtex' specified.")
            return """
            <div style="padding: 1rem; background-color: #ffeeba; color: #856404; border: 1px solid #ffeeba; border-radius: 4px;">
                <strong>Warning:</strong> The <code>[PUBL]</code> keyword was used, but no <code>bibtex</code> file was defined.
            </div>
            """, [], base_last_modified
        return "", [], base_last_modified

    try:
        md_dir   = os.path.dirname(filepath)
        bib_path = os.path.normpath(os.path.join(md_dir, bib_filename))

        # Update last modified date based on the BibTeX file
        bib_last_modified = get_last_modified(bib_path)
        updated_last_modified = max(bib_last_modified, base_last_modified)

        all_pubs = parse_bibtex(bib_path)
        pub_template = env.get_template('pub_list.tmpl')

        return pub_template.render(publications=all_pubs), all_pubs, updated_last_modified

    except FileNotFoundError:
        print(f"Warning: BibTeX file '{bib_filename}' not found for {filepath}")
        return f"""
        <div style="padding: 1rem; background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; border-radius: 4px;">
            <strong>Error:</strong> The specified BibTeX file <code>{bib_filename}</code> could not be found.
        </div>
        """, [], base_last_modified


def render_teaching_blocks(metadata, filepath, env):
    """Reads teaching CSVs and returns a dict of HTML blocks keyed by LV_NUMMER."""
    datasets = metadata.get('teaching_data', [])
    md_dir = os.path.dirname(filepath)
    courses = {}

    for data in datasets:
        csv_filename = data.get('file')
        if not csv_filename: continue

        csv_path = os.path.normpath(os.path.join(md_dir, csv_filename))
        if not os.path.exists(csv_path):
            print(f"Warning: Teaching CSV '{csv_filename}' not found.")
            continue

        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                lv_id = row.get('LV_NUMMER')
                if not lv_id: continue

                if lv_id not in courses:
                    courses[lv_id] = {'title': row['TITEL'], 'schedule': []}

                courses[lv_id]['schedule'].append({
                    'date': row['DATUM'],
                    'time': f"{row['VON']} - {row['BIS']}",
                    'room': row['ORT']
                })

    # Render templates
    html_blocks = {}
    try:
        template = env.get_template('teaching_list.tmpl')
        for lv_id, course_data in courses.items():
            html_blocks[lv_id] = template.render(
                course_title=course_data['title'],
                schedule=course_data['schedule']
            )
    except Exception as e:
        print(f"Warning: Could not render teaching templates: {e}")

    return html_blocks


def process_file(filepath, env, source_dir, output_dir, site_tz=None):
    # 1. Routing & setup
    routing       = get_routing_info(filepath, source_dir)
    post          = frontmatter.load(filepath)
    context       = post.metadata.copy()
    last_modified = get_last_modified(filepath)

    # 2. Process contact information from YAML block - [CONTACT] keyword
    contact_html = render_contact_block(post.metadata, env, routing['path_prefix'], post.content)

    # 2. Process publications from BibTeX file - [PUBL] keyword
    pub_html, all_pubs, last_modified = render_publications(
        post.metadata, filepath, env, last_modified, post.content
    )
    if all_pubs:
        context['publications'] = all_pubs

    # Process teaching blocks
    teaching_blocks = render_teaching_blocks(post.metadata, filepath, env)

    # 3. Convert Markdown
    extensions = ['toc', 'extra', 'codehilite', LaTeX2MathMLExtension()]
    use_macros = post.metadata.get('render_macros', True)
    use_toc    = post.metadata.get('toc', True)

    if use_macros:
        extensions.append(MacroExtension(
            pub_html=pub_html,
            contact_html=contact_html,
            teaching_blocks=teaching_blocks
        ))
    else:
        # Skip the extension; [PUBL] and [CONTACT] remain as raw text
        print(f"Info: macros disabled for {routing['filename']}")

    md = markdown.Markdown(extensions=extensions)
    html_content = md.convert(post.content)

    # 4. Assemble final template context
    norm_path = routing['norm_path']
    context.update({
        'content': html_content,
        'toc': use_toc,
        'toc_html': md.toc,
        'pub_html': pub_html,
        'PATH_PREFIX': routing['path_prefix'],
        'BUILD_DATE': last_modified.astimezone(site_tz).strftime("%B %d, %Y"),
        'IS_HOME': (routing['filename'] == 'index.md' and routing['depth'] == 0),
        'IS_PROJECTS': 'projects.md' in norm_path,
        'IS_TEACHING': 'teaching.md' in norm_path,
        'IS_TEAM': 'team.md' in norm_path or 'team/' in norm_path,
        'IS_PUBLICATIONS': 'publications.md' in norm_path,
    })

    # 5. Render template
    layout_choice = post.metadata.get('layout', 'base')
    try:
        template = env.get_template(f"{layout_choice}.tmpl")
    except Exception:
        print(f"Warning: Template '{layout_choice}.tmpl' not found. Falling back to 'base.tmpl'.")
        template = env.get_template("base.tmpl")

    final_html = template.render(**context)

    # 6. Save output as html
    output_path = os.path.join(output_dir, routing['rel_path'].replace('.md', '.html'))
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

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
