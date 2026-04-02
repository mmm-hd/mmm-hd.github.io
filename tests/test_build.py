import os
import tempfile
import pytest
import datetime
import sys
from jinja2 import Environment, DictLoader
import textwrap

# Add the project root (the parent directory of 'tests') to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the function you want to test from your main script
# Assuming your script is named build.py
from build import process_file

@pytest.fixture
def build_env():
    """Sets up temporary directories and an in-memory Jinja2 environment."""
    with tempfile.TemporaryDirectory() as source_dir, \
         tempfile.TemporaryDirectory() as output_dir:
        
        # Create dummy templates in memory, injecting context variables for testing
        templates = {
            'base.tmpl': 'HOME:{{ IS_HOME }}|TEAM:{{ IS_TEAM }}|PREFIX:{{ PATH_PREFIX }}|CONTENT:{{ content }}',
            'contact.tmpl': '<div class="contact-mock">{{ email }}</div>',
            'pub_list.tmpl': '<ul class="pub-mock">{% for pub in publications %}<li>{{ pub.title }}</li>{% endfor %}</ul>'
        }

        env = Environment(loader=DictLoader(templates))
        
        # We also need a dummy timezone object since your function accepts site_tz
        dummy_tz = datetime.timezone.utc
        
        yield source_dir, output_dir, env, dummy_tz

def test_missing_bibtex_file_injects_error(build_env):
    source_dir, output_dir, env, site_tz = build_env
    
    # 1. Setup input Markdown
    md_content = textwrap.dedent("""\
    ---
    title: Test Page
    bibtex: fake.bib
    ---
    # Publications
    [PUBL]
    """)
    filepath = os.path.join(source_dir, 'test.md')
    with open(filepath, 'w') as f:
        f.write(md_content)

    # 2. Execute the function
    process_file(filepath, env, source_dir, output_dir, site_tz)

    # 3. Assert the output
    output_path = os.path.join(output_dir, 'test.html')
    assert os.path.exists(output_path)
    
    with open(output_path, 'r') as f:
        html = f.read()
        
    # Check for the specific error box injected by process_file
    assert "The specified BibTeX file <code>fake.bib</code> could not be found" in html

def test_routing_home_page(build_env):
    source_dir, output_dir, env, site_tz = build_env

    # Setup index.md at the root
    filepath = os.path.join(source_dir, 'index.md')
    with open(filepath, 'w') as f:
        f.write("---\ntitle: Home\n---\nWelcome")

    process_file(filepath, env, source_dir, output_dir, site_tz)

    output_path = os.path.join(output_dir, 'index.html')
    with open(output_path, 'r') as f:
        html = f.read()

    # Assert it is recognized as the home page and has no path prefix
    assert "HOME:True" in html
    assert "PREFIX:|" in html

def test_routing_nested_team_page(build_env):
    source_dir, output_dir, env, site_tz = build_env

    # Create a nested directory structure: team/researchers/
    team_dir = os.path.join(source_dir, 'team', 'researchers')
    os.makedirs(team_dir)

    filepath = os.path.join(team_dir, 'smith.md')
    with open(filepath, 'w') as f:
        f.write("---\ntitle: Smith\n---\nProfile content")

    process_file(filepath, env, source_dir, output_dir, site_tz)

    # Read the output from the corresponding nested build directory
    output_path = os.path.join(output_dir, 'team', 'researchers', 'smith.html')
    with open(output_path, 'r') as f:
        html = f.read()

    # Assert it triggers the TEAM flag and calculates a depth of 2 (../../)
    assert "TEAM:True" in html
    assert "PREFIX:../../|" in html

def test_contact_macro_renders_when_present(build_env):
    source_dir, output_dir, env, site_tz = build_env

    # Markdown contains the macro and frontmatter contains the data
    md_content = textwrap.dedent("""\
    ---
    email: test@example.com
    ---
    Here is my contact info:
    
    [CONTACT]
    """)
    filepath = os.path.join(source_dir, 'contact_present.md')
    with open(filepath, 'w') as f:
        f.write(md_content)

    process_file(filepath, env, source_dir, output_dir, site_tz)

    output_path = os.path.join(output_dir, 'contact_present.html')
    with open(output_path, 'r') as f:
        html = f.read()

    # Assert the dummy contact template was rendered with the frontmatter data
    assert '<div class="contact-mock">test@example.com</div>' in html

def test_contact_macro_ignored_when_absent(build_env):
    source_dir, output_dir, env, site_tz = build_env

    # Frontmatter contains data, but the macro is NOT in the Markdown
    md_content = textwrap.dedent("""\
    ---
    email: test@example.com
    ---
    Just some regular text here.
    """)
    filepath = os.path.join(source_dir, 'contact_absent.md')
    with open(filepath, 'w') as f:
        f.write(md_content)

    process_file(filepath, env, source_dir, output_dir, site_tz)

    output_path = os.path.join(output_dir, 'contact_absent.html')
    with open(output_path, 'r') as f:
        html = f.read()

    # Assert the contact template was NOT rendered
    assert '<div class="contact-mock">' not in html

def test_missing_macro_warning(build_env):
    source_dir, output_dir, env, site_tz = build_env
    md_content = textwrap.dedent("""\
    ---
    title: Test Page
    ---
    # Publications
    [PUBL]
    """)
    filepath = os.path.join(source_dir, 'test.md')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(md_content)

    process_file(filepath, env, source_dir, output_dir, site_tz)

    with open(os.path.join(output_dir, 'test.html'), 'r') as f:
        html = f.read()
    assert "no <code>bibtex</code> file was defined" in html

def test_publications_render_success(build_env):
    source_dir, output_dir, env, site_tz = build_env

    # 1. Create a dummy bib file - NO leading spaces!
    bib_content = textwrap.dedent("""\
    @article{test2026,
    title = {Test Paper},
    author = {Doe, John},
    year = {2026}
    }""")

    bib_path = os.path.join(source_dir, 'publications.bib')
    with open(bib_path, 'w', encoding='utf-8') as f:
        f.write(bib_content)

    # 2. Create MD file using ONLY the 'bibtex' key
    md_content = textwrap.dedent("""\
    ---
    title: Pubs
    bibtex: publications.bib
    ---
    [PUBL]
    """)
    filepath = os.path.join(source_dir, 'publications.md')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(md_content)

    # 3. Build
    process_file(filepath, env, source_dir, output_dir, site_tz)

    # 4. Assert
    output_path = os.path.join(output_dir, 'publications.html')
    with open(output_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # We check for the content. Since the mock template renders the list
    # as strings, we look for the key parts of that string.
    assert "Test Paper" in html