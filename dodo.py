import os
import frontmatter
from build import setup_environment, process_file
from doit import get_var
from zoneinfo import ZoneInfo

# get_var(key, default_value)
SOURCE_DIR = get_var('source', 'md')
OUTPUT_DIR = get_var('output', '.')
LAYOUT_DIR = get_var('layout', 'layout')

# Define canonical site timezone
SITE_TZ = ZoneInfo("Europe/Berlin")

# Templates that affect the entire website
COMMON_TEMPLATES = ['navbar.tmpl', 'footer.tmpl', 'contact.tmpl']

def task_html():
    """Compile Markdown files to HTML."""

    env = setup_environment(LAYOUT_DIR)

    for root, dirs, files in os.walk(SOURCE_DIR):
        for file in files:
            if file.endswith('.md'):
                md_path   = os.path.join(root, file)
                rel_path  = os.path.relpath(md_path, SOURCE_DIR)
                html_path = os.path.join(OUTPUT_DIR, rel_path.replace('.md', '.html'))

                # Retrieve used layout (template) from markdown file
                try:
                    post = frontmatter.load(md_path)
                    md_dir = os.path.dirname(md_path)
                    layout_choice = post.get('layout', 'base')
                    bib_filename  = post.get('bibtex')
                    teaching_data = post.get('teaching_data', [])
                    teaching_path = []

                    # Resolve the file relative to the current markdown file
                    if bib_filename:
                        bib_path = os.path.normpath(os.path.join(md_dir, bib_filename))
                    else:
                        bib_path = None

                    for item in teaching_data:
                        csv_filename = item.get('file')

                        if csv_filename:
                            csv_path = os.path.normpath(os.path.join(md_dir, csv_filename))
                            teaching_path.append(csv_path)
                        else:
                            csv_path = None

                except Exception as e:
                    print(f"Warning: Failed to parse frontmatter for {md_path}")
                    print(f"Error: {e}")

                    layout_choice = 'base'
                    bib_path = None
                    teaching_data = []

                # 1. Track the Markdown file as input
                deps = [md_path]

                # 2. Track the common templates (header, footer)
                for common in COMMON_TEMPLATES:
                    layout_tmpl_path = os.path.join(LAYOUT_DIR, common)
                    deps.append(layout_tmpl_path)

                # 3. Track the used layout template
                layout_tmpl_path = os.path.join(LAYOUT_DIR, f"{layout_choice}.tmpl")
                if layout_tmpl_path not in deps and os.path.exists(layout_tmpl_path):
                    deps.append(layout_tmpl_path)

                # 4. Track the BibTeX file if one is specified
                if bib_path and os.path.exists(bib_path):
                    deps.append(bib_path)

                # 5. Track the CSV file if one is specified
                for csv_path in teaching_path:
                    if csv_path and os.path.exists(csv_path):
                        deps.append(csv_path)

                yield {
                    'name': md_path,
                    'actions': [(process_file, [md_path, env, SOURCE_DIR, OUTPUT_DIR, SITE_TZ])],
                    'file_dep': deps,
                    'targets': [html_path],
                    'clean': True,
                }