import os
import frontmatter
from build import setup_environment, process_file

# Templates that affect the entire website
COMMON_TEMPLATES = ['template/navbar.tmpl', 'template/footer.tmpl']

def task_html():
    """Compile Markdown files to HTML."""

    env = setup_environment()
    source_dir = 'md'
    output_dir = '.'

    for root, dirs, files in os.walk(source_dir):
        for file in files:
            if file.endswith('.md'):
                md_path   = os.path.join(root, file)
                rel_path  = os.path.relpath(md_path, 'md')
                html_path = os.path.join('.', rel_path.replace('.md', '.html'))

                # Retrieve used layout (template) from markdown file
                try:
                    post = frontmatter.load(md_path)
                    layout_choice = post.get('layout', 'base')
                    bib_filename  = post.get('bib_file')

                except Exception:
                    layout_choice = 'base'
                    bib_filename  = None

                # 1. Track the Markdown file as input
                deps = [md_path] + COMMON_TEMPLATES

                # 2. Track the used layout template
                layout_tmpl_path = os.path.join('template', f"{layout_choice}.tmpl")
                if layout_tmpl_path not in deps and os.path.exists(layout_tmpl_path):
                    deps.append(layout_tmpl_path)

                # 3. Track the BibTeX file if one is specified
                if bib_filename and os.path.exists(bib_filename):
                    deps.append(bib_filename)

                yield {
                    'name': md_path,
                    'actions': [(process_file, [md_path, env, source_dir, output_dir])],
                    'file_dep': deps,
                    'targets': [html_path],
                    'clean': True,
                }