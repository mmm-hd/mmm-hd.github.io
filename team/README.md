## Employee pages

This directory contains the websites for specific employees.
The contents are related to specific tasks in the group, including:

* Focus and specializations
* Completed and on-going projects
* List of publications
* Current and previous teaching
* Supervision of student thesis
* Organisation of current and previous events

Contact information includes the following:

* Office room number
* Office phone number
* Email form
* Publication overview, e.g. Orcid (if any)
* Code sharing platform, e.g. Github (if any)

To create an employee website, you may use the following template:

```html
<!DOCTYPE html>
<html lang="en">
<!-- HEAD TEMPLATE BEGIN -->
<!-- HEAD TEMPLATE END -->

<body>

<!-- HEADER TEMPLATE BEGIN -->
<!-- HEADER TEMPLATE END -->

<div class="banner-slim">
    <h1>Your Name</h1>
</div>

<div class="profile-layout">

    <aside class="profile-sidebar">
        <img src="../../assets/images/placeholder.jpeg" alt="Your Name" class="profile-photo">
        <h3 style="margin-top: 15px; margin-bottom: 20px;">Role</h3>

        <div class="toc-toggle" id="toc-toggle">&#9776; Contents</div>

        <nav class="toc-nav" id="toc-nav">
            <ul>
                <li><a href="#about">About</a></li>
                <li><a href="#research">Research</a></li>
                <li><a href="#publications">Publications</a></li>
            </ul>
        </nav>
    </aside>

    <main class="profile-content">
        <h2 id="about">About</h2>
        <p></p>
        <h2 id="research">Research</h2>
        <p></p>
        <h2 id="publications">Publications</h2>
        <p></p>
    </main>
</div>

<!-- FOOTER TEMPLATE BEGIN -->
<!-- FOOTER TEMPLATE END -->

</body>
</html>
```

Header and footer can be populated with `template/build.py`.