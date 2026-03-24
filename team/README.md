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

<div class="container profile-container">
    <div class="profile-sidebar">
        <img src="../../assets/images/placeholder.jpeg" alt="Your Name" class="profile-photo">
        <h3 style="margin-top: 15px;">Your Role/h3>
    </div>

    <div class="profile-content">
        <h2>About</h2>
    </div>
</div>

<!-- FOOTER TEMPLATE BEGIN -->
<!-- FOOTER TEMPLATE END -->

</body>
</html>
```

Header and footer can be populated with `template/build.py`.