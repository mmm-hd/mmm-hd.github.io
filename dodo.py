import os
from build import setup_environment, process_file

def task_html():
    """Compile Markdown files to HTML."""

    # Initialize the Jinja environment and load templates exactly once
    templates = setup_environment()
    source_dir = 'md'
    output_dir = '.'

    # Gather all templates for the dependency tracker
    tmpl_files = []
    for root, dirs, files in os.walk('template'):
        for file in files:
            if file.endswith('.tmpl'):
                tmpl_files.append(os.path.join(root, file))

    # Generate a task for every Markdown file in the md/ directory
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            if file.endswith('.md'):
                md_path   = os.path.join(root, file)
                rel_path  = os.path.relpath(md_path, 'md')
                html_path = os.path.join('.', rel_path.replace('.md', '.html'))

                yield {
                    'name': md_path,
                    'actions': [(process_file, [md_path, templates, source_dir, output_dir])],
                    'file_dep': [md_path] + tmpl_files,
                    'targets': [html_path],
                    'clean': True,
                }