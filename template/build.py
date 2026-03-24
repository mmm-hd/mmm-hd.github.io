#!/usr/bin/env python3
import os
import markdown
import frontmatter
from jinja2 import Environment, FileSystemLoader

def main():
    # Initialize Jinja environment
    env = Environment(loader=FileSystemLoader('template'))
    base_template = env.get_template('base.tmpl')
    profile_template = env.get_template('profile.tmpl')
    team_template = env.get_template('team.tmpl')
    publications_template = env.get_template('publications.tmpl')

    # Define source and output directories
    SOURCE_DIR = 'md'
    OUTPUT_DIR = '.'

    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.md'):
                filepath = os.path.join(root, file)
                
                # Calculate path relative to the 'md' directory
                rel_path = os.path.relpath(filepath, SOURCE_DIR)
                normalized_rel_path = rel_path.replace(os.sep, '/')
                filename = os.path.basename(normalized_rel_path)

                # Calculate path prefix for assets based on directory depth
                depth = normalized_path.count('/')
                prefix = '../' * depth if depth > 0 else ''
                
                # Determine active menu states
                is_home = (filename == 'index.md' and depth == 0)
                is_projects = 'projects.md' in normalized_path
                is_teaching = 'teaching.md' in normalized_path
                is_team = 'team.md' in normalized_path or '/team/' in normalized_path
                is_publications = 'publications.md' in normalized_path
                
                # Parse YAML frontmatter and markdown
                post = frontmatter.load(filepath)
                md = markdown.Markdown(extensions=['toc'])
                html_content = md.convert(post.content)
                toc_html = md.toc 
                
                layout_choice = post.get('layout', 'base')
                
                # Select and render the template
                if layout_choice == 'profile':
                    final_html = profile_template.render(
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
                    final_html = team_template.render(
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
                    final_html = base_template.render(
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
                output_path = filepath.replace('.md', '.html')
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(final_html)
                
                print(f"Built: {output_path}")

if __name__ == "__main__":
    main()
