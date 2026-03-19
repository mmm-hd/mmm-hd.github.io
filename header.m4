define(`INSERT_HEADER', `
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>$3 - Mathematical Modelling in Medicine</title>
    <link rel="stylesheet" href="$2style.css">
</head>
<body>

<div class="header">
    <div class="logo">
        <img src="$2logo_uni_heidelberg.svg" alt="University of Heidelberg Logo">
        <span>Prof. Stefania Petra</span>
    </div>
    
    <div class="menu-icon" id="menu-icon">&#9776;</div>
    
    <div class="links" id="nav-links">
        <a href="$2index.html" ifelse($1, `home', `class="active"')>Home</a>
        <a href="$2projects.html" ifelse($1, `projects', `class="active"')>Projects</a>
        <a href="$2teaching.html" ifelse($1, `teaching', `class="active"')>Teaching</a>
        <a href="$2students.html" ifelse($1, `students', `class="active"')>Students</a>
        <a href="$2publications.html" ifelse($1, `publications', `class="active"')>Publications</a>
        <a href="$2links.html" ifelse($1, `links', `class="active"')>Links</a>
        <a href="$2contact.html" ifelse($1, `contact', `class="active"')>Contact</a>
        <span class="search-icon">&#9906;</span> 
    </div>
</div>
')dnl