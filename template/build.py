#!/usr/bin/env python3
import os
import glob
from datetime import datetime, timezone
from jinja2 import Environment, FileSystemLoader

def main():
    # 1. Generate the dynamic UTC date
    build_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # 2. Load the templates
    env = Environment(loader=FileSystemLoader('template'))
    head_tmpl   = env.get_template('head.tmpl')
    header_tmpl = env.get_template('header.tmpl')
    footer_tmpl = env.get_template('footer.tmpl')

    # 3. Find all HTML files recursively
    html_files = glob.glob('**/*.html', recursive=True)

    for filepath in html_files:
        # Normalize path separators for depth calculation
        normalized_path = filepath.replace('\\', '/')
        filename = os.path.basename(normalized_path)
        
        # 4. Calculate Path Prefix based on folder depth
        depth = normalized_path.count('/')
        prefix = '../' * depth if depth > 0 else ''

        # 5. Determine which link should have class="active"
        template_vars = {
            'PATH_PREFIX': prefix,
            'BUILD_DATE': build_date,
            'IS_HOME': filename == 'index.html' and depth == 0,
            'IS_PROJECTS': 'projects.html' in normalized_path,
            'IS_TEACHING': 'teaching.html' in normalized_path,
            'IS_STUDENTS': 'team.html' in normalized_path or '/team/' in normalized_path,
            'IS_PUBLICATIONS': 'publications.html' in normalized_path,
            'IS_LINKS': 'links.html' in normalized_path,
            'IS_CONTACT': 'contact.html' in normalized_path,
        }

        # Render the templates with the variables
        head_out   = head_tmpl.render(**template_vars)
        header_out = header_tmpl.render(**template_vars)
        footer_out = footer_tmpl.render(**template_vars)

        # 6. Read the current HTML file
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        new_lines = []
        skip_mode = False

        # 7. Process line by line
        for line in lines:
            if skip_mode:
                # If we are inside a marker block, ignore everything except the END marker
                if "HEAD TEMPLATE END" in line or "HEADER TEMPLATE END" in line or "FOOTER TEMPLATE END" in line:
                    new_lines.append(line)
                    skip_mode = False
            else:
                # Look for BEGIN markers
                if "HEAD TEMPLATE BEGIN" in line:
                    new_lines.append(line)
                    new_lines.append(head_out + '\n')
                    skip_mode = True
                elif "HEADER TEMPLATE BEGIN" in line:
                    new_lines.append(line)
                    new_lines.append(header_out + '\n')
                    skip_mode = True
                elif "FOOTER TEMPLATE BEGIN" in line:
                    new_lines.append(line)
                    new_lines.append(footer_out + '\n')
                    skip_mode = True
                else:
                    new_lines.append(line)

        original_html = "".join(lines)
        new_html = "".join(new_lines)

        # 8. Write to disk only if content changed
        if original_html != new_html:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_html)
            print(f"Updated: {filepath}")

if __name__ == "__main__":
    main()
