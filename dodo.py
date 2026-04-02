import os
import frontmatter
from build import setup_environment, process_file
from doit import get_var

# Templates that affect the entire website
COMMON_TEMPLATES = ['template/navbar.tmpl', 'template/footer.tmpl']

# get_var(key, default_value)
SOURCE_DIR = get_var('source', 'md')
OUTPUT_DIR = get_var('output', '.')

def task_html():
    """Compile Markdown files to HTML."""

    env = setup_environment()

    for root, dirs, files in os.walk(SOURCE_DIR):
        for file in files:
            if file.endswith('.md'):
                md_path   = os.path.join(root, file)
                rel_path  = os.path.relpath(md_path, SOURCE_DIR)
                html_path = os.path.join(OUTPUT_DIR, rel_path.replace('.md', '.html'))

                # Retrieve used layout (template) from markdown file
                try:
                    post = frontmatter.load(md_path)
                    layout_choice = post.get('layout', 'base')
                    bib_filename  = post.get('bib_file')

                    # Resolve the file relative to the current markdown file
                    md_dir = os.path.dirname(md_path)
                    bib_path = os.path.normpath(os.path.join(md_dir, bib_filename))

                except Exception:
                    layout_choice = 'base'
                    bib_path  = None

                # 1. Track the Markdown file as input
                deps = [md_path] + COMMON_TEMPLATES

                # 2. Track the used layout template
                layout_tmpl_path = os.path.join('template', f"{layout_choice}.tmpl")
                if layout_tmpl_path not in deps and os.path.exists(layout_tmpl_path):
                    deps.append(layout_tmpl_path)

                # 3. Track the BibTeX file if one is specified
                if bib_path and os.path.exists(bib_path):
                    deps.append(bib_path)

                yield {
                    'name': md_path,
                    'actions': [(process_file, [md_path, env, SOURCE_DIR, OUTPUT_DIR])],
                    'file_dep': deps,
                    'targets': [html_path],
                    'clean': True,
                }