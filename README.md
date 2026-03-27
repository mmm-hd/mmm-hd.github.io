## mmm-hd.github.io

### Inner workings
The website has the following components:

* Assets (images, javascript, stylesheets) -> `assets`
* Templates in `Jinja2` (navlinks, footer, publications, ...) -> `template/`
* Pages in YAML (frontmatter) and Markdown body -> `md/`
  * `layout`: which template to choose
  * `title`: title of the page
  * template-specific fields such as `photo`
* Static site generator -> `build.py`
  * Assemble Markdown pages to corresponding template
  * Convert BibTeX files (`bibtexparser`)
  * `dodo.py` detects which `md` files need to be rebuilt


### Employee pages

Every employee has their own "webspace" as a subdirectory in `team/`.
The base page should be edited in `index.md`. The header consists of a
profile photo, team role, title and text (Markdown) body.

To include publications, add a BibTeX file and write the name in
`bib_file`. The publications can then be inserted with the `[PUBL]`
keyword.

> **Note**: Currently BibTeX is only implemented for the main publications
> page (#3).

For example:
```md
---
title: Jane Doe
layout: profile
role: Team Member
photo: assets/images/jane.jpg
bib_file: publications.bib
---

## About

## Research

## Publications
[PUBL]
```

**Page contents** are related to specific tasks in the group, including:

* Focus and specializations
* Completed and on-going projects
* List of publications
* Current and previous teaching
* Supervision of student thesis
* Organisation of current and previous events

**Contact information** includes the following:

* Office room number
* Office phone number
* Email form
* Publication overview, e.g. Orcid (if any)
* Code sharing platform, e.g. Github (if any)

### Making changes

Simple changes can be done directly in the Github editor.
For larger changes that affect more people (i.e. more than your personal
space), _pull requests_ are suggested.

https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests

Unfortunately there is no universal guide for `git`. Suggestions:

* https://git-scm.com/docs/gittutorial (text-oriented)
* https://wizardzines.com/zines/git/ (visual, commercial)
* https://docs.github.com/en/get-started/start-your-journey/hello-world (GitHub specific)

For a basic guide to Markdown, see the following:
* https://www.markdownguide.org/basic-syntax/
* https://www.markdownguide.org/cheat-sheet/

Several extensions are supported (tables, code highlighting, MathML.)
In particular you can write basic LaTeX formulas. For example:

```latex
Here is an inline math equation: $E = mc^2$.

Here is a block math equation:

$$
\frac{d}{dx} e^x = e^x
$$

And here is an alternative notation for a block math equation:

\[
x^n + y^n = z^n
\]
```


### Building the site

> **Note**: The `main` branch of his repository only contains the markdown files.
> On each commit, the corresponding `html` files are pushed to the `gh-pages` branch.
> The below can be used if you want to preview larger changes to the website locally.
 
Requirements: Python 3.9+

First, retrieve or update the repository:
```sh
# Fetch the repository
git clone https://github.com/mmm-hd/mmm-hd.github.io

# OR, if you already have the repository and want to update
cd mmm-hd.github.io
git pull

# Make sure the needed tools are installed
pip install -r requirements.txt
```

After making your changes in `md/...`, build the HTML files:
```sh
# Build the website
cd mmm-hd.github.io
doit

# Browser preview (optional: open a browser in localhost:8080 
# while this command is running)
python -m http.server 8080
```

Now you can push the changes to the repository:
```sh
# Record the changes
git commit md/ team/

# Push to the repository
git push
```

This is for macOS/Linux where Python and git should be pre-installed.
On Windows, it is easiest to use WSL.

* https://learn.microsoft.com/en-us/windows/wsl/install