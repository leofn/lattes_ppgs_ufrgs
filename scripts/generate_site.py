#!/usr/bin/env python3
"""
Generate static faculty site from processed Lattes data.
Outputs to docs/ directory for GitHub Pages.
"""

import json
import os
from pathlib import Path
from urllib.parse import quote
import html

def generate_site():
    """Generate the static site."""
    print("=" * 50)
    print("Generating PPGS Faculty Site")
    print("=" * 50)

    # Load processed data (enhanced with Google Scholar)
    data_path = Path('data/processed/ppgs_dataset.json')
    if not data_path.exists():
        print(f"Error: {data_path} not found. Run enhance_with_scholar_fixed.py first.")
        return

    with open(data_path, 'r', encoding='utf-8') as f:
        faculty_data = json.load(f)

    print(f"Loaded {len(faculty_data)} faculty members")

    # Create output directory
    output_dir = Path('docs')
    output_dir.mkdir(exist_ok=True)

    # Create assets directory
    assets_dir = output_dir / 'assets'
    assets_dir.mkdir(exist_ok=True)
    (assets_dir / 'css').mkdir(exist_ok=True)
    (assets_dir / 'js').mkdir(exist_ok=True)
    (assets_dir / 'images').mkdir(exist_ok=True)

    # Generate CSS
    css_content = """/* PPGS Faculty Site - Modern, Responsive Design */
:root {
    --primary-color: #2563eb;
    --primary-dark: #1d4ed8;
    --secondary-color: #64748b;
    --background-color: #f8fafc;
    --surface-color: #ffffff;
    --text-color: #1e293b;
    --text-muted: #64748b;
    --border-color: #e2e8f0;
    --radius: 0.5rem;
    --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
    --shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
    --shadow-md: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -2px rgb(0 0 0 / 0.1);
    --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: var(--font-sans);
    line-height: 1.6;
    color: var(--text-color);
    background-color: var(--background-color);
}

.container {
    width: 100%;
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 1rem;
}

header {
    background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
    color: white;
    padding: 3rem 0;
    text-align: center;
    position: relative;
    overflow: hidden;
}

header::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: url('data:image/svg+xml;utf8,<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 100 100\"><path fill=\"%23ffffff\" fill-opacity=\"0.1\" d=\"M0,0 L100,0 L100,100 L0,100 Z\"/></svg>');
}

header h1 {
    font-size: 2.5rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    position: relative;
    z-index: 1;
}

header p {
    font-size: 1.25rem;
    opacity: 0.9;
    position: relative;
    z-index: 1;
    max-width: 600px;
    margin: 0 auto;
}

.faculty-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 2rem;
    padding: 3rem 0;
}

.faculty-card {
    background: var(--surface-color);
    border-radius: var(--radius);
    box-shadow: var(--shadow-sm);
    overflow: hidden;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    border: 1px solid var(--border-color);
    height: 100%;
    display: flex;
    flex-direction: column;
}

.faculty-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow);
}

.faculty-card-image {
    height: 200px;
    background: linear-gradient(135deg, #e2e8f0, #f1f5f9);
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-muted);
    font-size: 1.1rem;
}

.faculty-card-image img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.faculty-card-content {
    flex: 1;
    padding: 1.5rem;
}

.faculty-card h2 {
    font-size: 1.5rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
    color: var(--text-color);
}

.faculty-card .title {
    font-size: 1rem;
    color: var(--primary-color);
    font-weight: 500;
    margin-bottom: 1rem;
}

.faculty-card .summary {
    font-size: 0.95rem;
    color: var(--text-muted);
    margin-bottom: 1.5rem;
    line-height: 1.5;
    flex-grow: 1;
}

.faculty-card .stats {
    display: flex;
    justify-content: space-between;
    font-size: 0.875rem;
    color: var(--text-muted);
    border-top: 1px var(--border-color);
    padding-top: 1rem;
}

.faculty-card .stat {
    text-align: center;
}

.faculty-card .stat-value {
    display: block;
    font-weight: 600;
    color: var(--text-color);
    font-size: 1rem;
}

.faculty-card .stat-label {
    display: block;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.faculty-card .btn {
    display: inline-block;
    background: var(--primary-color);
    color: white;
    text-decoration: none;
    padding: 0.5rem 1rem;
    border-radius: var(--radius);
    font-weight: 500;
    transition: background 0.2s ease;
    border: none;
    cursor: pointer;
    text-align: center;
    margin-top: 1rem;
}

.faculty-card .btn:hover {
    background: var(--primary-dark);
}

.faculty-detail {
    padding: 3rem 0;
}

.faculty-detail-header {
    text-align: center;
    margin-bottom: 3rem;
}

.faculty-detail-header h1 {
    font-size: 2.25rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
}

.faculty-detail-header .title {
    font-size: 1.125rem;
    color: var(--primary-color);
    margin-bottom: 1.5rem;
}

.faculty-detail-header .image {
    width: 200px;
    height: 200px;
    margin: 0 auto 1.5rem;
    border-radius: 50%;
    overflow: hidden;
    box-shadow: var(--shadow);
    border: 4px solid var(--primary-color);
}

.faculty-detail-header .image img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.faculty-detail-content {
    max-width: 800px;
    margin: 0 auto;
}

.section {
    margin-bottom: 2.5rem;
    padding: 0 1rem;
}

.section h2 {
    font-size: 1.75rem;
    font-weight: 600;
    color: var(--text-color);
    margin-bottom: 1.5rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid var(--primary-color);
    display: inline-block;
}

.content-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 1.5rem;
}

.card {
    background: var(--surface-color);
    border-radius: var(--radius);
    box-shadow: var(--shadow-sm);
    padding: 1.5rem;
    border: 1px solid var(--border-color);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow);
}

.card h3 {
    font-size: 1.25rem;
    font-weight: 600;
    margin-bottom: 1rem;
    color: var(--text-color);
}

.card ul {
    list-style: none;
}

.card li {
    padding: 0.5rem 0;
    border-bottom: 1px solid var(--border-color);
}

.card li:last-child {
    border-bottom: none;
}

.card li a {
    color: var(--text-color);
    text-decoration: none;
}

.card li a:hover {
    text-decoration: underline;
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1.5rem;
    margin-top: 1.5rem;
}

.stat-card {
    background: var(--surface-color);
    border-radius: var(--radius);
    box-shadow: var(--shadow-sm);
    text-align: center;
    padding: 1.5rem;
    border: 1px solid var(--border-color);
}

.stat-value {
    font-size: 2.25rem;
    font-weight: 700;
    color: var(--primary-color);
    display: block;
    margin-bottom: 0.5rem;
}

.stat-label {
    font-size: 0.875rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.back-link {
    display: inline-block;
    color: var(--primary-color);
    text-decoration: none;
    font-weight: 500;
    margin-bottom: 2rem;
}

.back-link:hover {
    text-decoration: underline;
}

footer {
    background-color: var(--surface-color);
    border-top: 1px solid var(--border-color);
    padding: 2rem 0;
    text-align: center;
    color: var(--text-muted);
    font-size: 0.875rem;
}

footer a {
    color: var(--primary-color);
    text-decoration: none;
}

footer a:hover {
    text-decoration: underline;
}

@media (max-width: 768px) {
    header {
        padding: 2rem 0;
    }
    
    header h1 {
        font-size: 2rem;
    }
    
    header p {
        font-size: 1.1rem;
    }
    
    .faculty-grid {
        grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
        gap: 1.5rem;
        padding: 2rem 0;
    }
    
    .faculty-card-content {
        padding: 1.25rem;
    }
    
    .faculty-detail {
        padding: 2rem 0;
    }
    
    .faculty-detail-header h1 {
        font-size: 1.75rem;
    }
    
    .section h2 {
        font-size: 1.5rem;
    }
}

@media (max-width: 480px) {
    .container {
        padding: 0 0.75rem;
    }
    
    header {
        padding: 1.5rem 0;
    }
    
    header h1 {
        font-size: 1.75rem;
    }
    
    header p {
        font-size: 1rem;
    }
    
    .faculty-grid {
        grid-template-columns: 1fr;
        gap: 1rem;
        padding: 1.5rem 0;
    }
}
"""

    # Write CSS
    css_path = assets_dir / 'css' / 'style.css'
    with open(css_path, 'w', encoding='utf-8') as f:
        f.write(css_content)
    print(f"✓ Generated CSS: {css_path}")

    # Generate index.html
    index_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PPGS Faculty - LABHDUFBA</title>
    <link rel="stylesheet" href="/assets/css/style.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
</head>
<body>
    <header>
        <div class="container">
            <h1>PPGS Faculty</h1>
            <p>Programa de Pós-Graduação em Ciências Sociais - UFBA</p>
        </div>
    </header>

    <main>
        <div class="container">
            <div class="faculty-grid">
"""

    # Add faculty cards
    for faculty in faculty_data:
        # Create a slug for the faculty member
        name = faculty.get('nome', 'Unknown')
        slug = quote(name.lower().replace(' ', '-'))
        
        # Get first name for title (simplified)
        first_name = name.split()[0] if name else ""
        last_name = name.split()[-1] if len(name.split()) > 1 else ""
        
        # Determine title/position from summary or professional address
        title = "Professor"
        if "Professor" in faculty.get('summary', ''):
            if "Adjunta" in faculty.get('summary', ''):
                title = "Adjunct Professor"
            elif "Associado" in faculty.get('summary', ''):
                title = "Associate Professor"
            elif "Titular" in faculty.get('summary', ''):
                title = "Full Professor"
            elif "Assistente" in faculty.get('summary', ''):
                title = "Assistant Professor"
        
        # Get summary (truncated)
        summary = faculty.get('summary', '')
        if len(summary) > 200:
            summary = summary[:200] + "..."
        
        # Get statistics
        stats = faculty.get('statistics', {})
        pubs = stats.get('journal_articles', 0) + stats.get('books', 0) + stats.get('book_chapters', 0)
        sup = stats.get('completed_supervisions', 0)
        
        index_html += f"""                <div class="faculty-card">
                    <div class="faculty-card-image">
                        <img src="/assets/images/placeholder.png" alt="{html.escape(name)}">
                    </div>
                    <div class="faculty-card-content">
                        <h2>{html.escape(name)}</h2>
                        <div class="title">{html.escape(title)}</div>
                        <p class="summary">{html.escape(summary)}</p>
                        <div class="stats">
                            <div class="stat">
                                <span class="stat-value">{pubs}</span>
                                <span class="stat-label">Publications</span>
                            </div>
                            <div class="stat">
                                <span class="stat-value">{sup}</span>
                                <span class="stat-label">Supervisions</span>
                            </div>
                        </div>
                        <a href="faculty/{slug}.html" class="btn">View Profile</a>
                    </div>
                </div>
"""
    
    index_html += """            </div>
        </div>
    </main>

    <footer>
        <div class="container">
            <p>&copy; 2026 LABHDUFBA - Programa de Pós-Graduação em Ciências Sociais</p>
            <p>Data sourced from Lattes Platform</p>
        </div>
    </footer>
</body>
</html>"""

    # Write index.html
    with open(output_dir / 'index.html', 'w', encoding='utf-8') as f:
        f.write(index_html)
    print(f"✓ Generated index.html")
    
    # Generate faculty detail pages
    for faculty in faculty_data:
        name = faculty.get('nome', 'Unknown')
        slug = quote(name.lower().replace(' ', '-'))
        
        # Build faculty page
        faculty_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(name)} - PPGS Faculty</title>
    <link rel="stylesheet" href="/assets/css/style.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
</head>
<body>
    <header>
        <div class="container">
            <h1>{html.escape(name)}</h1>
            <div class="title">Professor of Sociology</div>
        </div>
    </header>

    <main>
        <div class="container faculty-detail">
            <a href="/" class="btn">← Back to Faculty List</a>
            
            <div class="faculty-detail-header">
                <div class="image">
                    <img src="/assets/images/placeholder.png" alt="{html.escape(name)}">
                </div>
                <h1>{html.escape(name)}</h1>
                <div class="title">Professor of Sociology</div>
            </div>
            
            <div class="faculty-detail-content">
                <div class="section">
                    <h2>Biography</h2>
                    <div class="card">
                        <p>{html.escape(faculty.get('summary', 'No biography available.'))}</p>
                    </div>
                </div>
                
                <div class="section">
                    <h2>Education</h2>
                    <div class="content-grid">
"""

        # Education
        for edu in faculty.get('education', []):
            faculty_html += f"""                        <div class="card">
                            <h3>{html.escape(edu.get('type', ''))}</h3>
                            <p><strong>{html.escape(edu.get('institution', ''))}</strong></p>
                            <p>{html.escape(edu.get('start_year', ''))} - {html.escape(edu.get('end_year', ''))}</p>
                            {f'<p>{html.escape(edu.get("description", ""))}</p>' if edu.get('description') else ''}
                        </div>
"""
        
        faculty_html += """                    </div>
                </div>
                
                <div class="section">
                    <h2>Publications</h2>
                    <div class="content-grid">
"""

        # Journal Articles
        pubs = faculty.get('publications', {}).get('journal_articles', [])
        if pubs:
            faculty_html += f"""                        <div class="card">
                            <h3>Journal Articles ({len(pubs)})</h3>
                            <ul>
"""
            for pub in pubs[:5]:  # Show first 5
                faculty_html += f"""                                <li>
                                    <strong>{html.escape(pub.get('title', ''))}</strong><br>
                                    <em>{html.escape(pub.get('journal', ''))}</em>, {html.escape(pub.get('year', ''))}
                                    {f': Vol. {html.escape(pub.get("volume", ""))}' if pub.get('volume') else ''}
                                    {f', pp. {html.escape(pub.get("pages", ""))}' if pub.get('pages') else ''}
                                    {f' | DOI: <a href="https://doi.org/{html.escape(pub.get("doi", ""))}" target="_blank">{html.escape(pub.get("doi", ""))}</a>' if pub.get('doi') else ''}
                                </li>
"""
            faculty_html += """                            </ul>
                            {f'<p><a href="#">View all {len(pubs)} articles</a></p>' if len(pubs) > 5 else ''}
                        </div>
"""
        else:
            faculty_html += """                        <div class="card">
                            <p>No journal articles found.</p>
                        </div>
"""
        
        # Books
        books = faculty.get('publications', {}).get('books', [])
        if books:
            faculty_html += f"""                        <div class="card">
                            <h3>Books ({len(books)})</h3>
                            <ul>
"""
            for book in books[:5]:
                faculty_html += f"""                                <li>
                                    <strong>{html.escape(book.get('title', ''))}</strong><br>
                                    {html.escape(book.get('publisher', ''))}, {html.escape(book.get('year', ''))}
                                    {f' | ISBN: {html.escape(book.get("isbn", ""))}' if book.get('isbn') else ''}
                                </li>
"""
            faculty_html += """                            </ul>
                            {f'<p><a href="#">View all {len(books)} books</a></p>' if len(books) > 5 else ''}
                        </div>
"""
        else:
            faculty_html += """                        <div class="card">
                            <p>No books found.</p>
                        </div>
"""
        
        # Book Chapters
        chapters = faculty.get('publications', {}).get('book_chapters', [])
        if chapters:
            faculty_html += f"""                        <div class="card">
                            <h3>Book Chapters ({len(chapters)})</h3>
                            <ul>
"""
            for chap in chapters[:5]:
                faculty_html += f"""                                <li>
                                    <strong>{html.escape(chap.get('title', ''))}</strong><br>
                                    In: {html.escape(chap.get('book_title', ''))}<br>
                                    {html.escape(chap.get('publisher', ''))}, {html.escape(chap.get('year', ''))}
                                    {f' | pp. {html.escape(chap.get("pages", ""))}' if chap.get('pages') else ''}
                                </li>
"""
            faculty_html += """                            </ul>
                            {f'<p><a href="#">View all {len(chapters)} chapters</a></p>' if len(chapters) > 5 else ''}
                        </div>
"""
        else:
            faculty_html += """                        <div class="card">
                            <p>No book chapters found.</p>
                        </div>
"""
        
        faculty_html += """                    </div>
                </div>
                
                <div class="section">
                    <h2>Supervision</h2>
                    <div class="content-grid">
"""

        # Completed supervisions
        completed = faculty.get('supervision', {}).get('completed', [])
        if completed:
            faculty_html += f"""                        <div class="card">
                            <h3>Completed Supervisions ({len(completed)})</h3>
                            <ul>
"""
            for sup in completed[:5]:
                faculty_html += f"""                                <li>
                                    <strong>{html.escape(sup.get('title', ''))}</strong><br>
                                    Student: {html.escape(sup.get('student', ''))} ({html.escape(sup.get('level', ''))})<br>
                                    Year: {html.escape(sup.get('year', ''))}
                                </li>
"""
            faculty_html += """                            </ul>
                            {f'<p><a href="#">View all {len(completed)} supervisions</a></p>' if len(completed) > 5 else ''}
                        </div>
"""
        else:
            faculty_html += """                        <div class="card">
                            <p>No completed supervisions found.</p>
                        </div>
"""
        
        # Ongoing supervisions
        ongoing = faculty.get('supervision', {}).get('ongoing', [])
        if ongoing:
            faculty_html += f"""                        <div class="card">
                            <h3>Ongoing Supervisions ({len(ongoing)})</h3>
                            <ul>
"""
            for sup in ongoing[:5]:
                faculty_html += f"""                                <li>
                                    <strong>{html.escape(sup.get('title', ''))}</strong><br>
                                    Student: {html.escape(sup.get('student', ''))} ({html.escape(sup.get('level', ''))})<br>
                                    Since: {html.escape(sup.get('start_year', ''))}
                                </li>
"""
            faculty_html += """                            </ul>
                            {f'<p><a href="#">View all {len(ongoing)} supervisions</a></p>' if len(ongoing) > 5 else ''}
                        </div>
"""
        else:
            faculty_html += """                        <div class="card">
                            <p>No ongoing supervisions found.</p>
                        </div>
"""
        
        faculty_html += """                    </div>
                </div>
                
                <div class="section">
                    <h2>Statistics</h2>
                    <div class="stats-grid">
"""

        stats = faculty.get('statistics', {})
        faculty_html += f"""                        <div class="stat-card">
                            <span class="stat-value">{stats.get('journal_articles', 0)}</span>
                            <span class="stat-label">Journal Articles</span>
                        </div>
                        <div class="stat-card">
                            <span class="stat-value">{stats.get('books', 0)}</span>
                            <span class="stat-label">Books</span>
                        </div>
                        <div class="stat-card">
                            <span class="stat-value">{stats.get('book_chapters', 0)}</span>
                            <span class="stat-label">Book Chapters</span>
                        </div>
                        <div class="stat-card">
                            <span class="stat-value">{stats.get('completed_supervisions', 0)}</span>
                            <span class="stat-label">Completed Supervisions</span>
                        </div>
                        <div class="stat-card">
                            <span class="stat-value">{stats.get('ongoing_supervisions', 0)}</span>
                            <span class="stat-label">Ongoing Supervisions</span>
                        </div>
"""
        
        faculty_html += """                    </div>
                </div>
            </div>
        </div>
    </main>

    <footer>
        <div class="container">
            <p>&copy; 2026 LABHDUFBA - Programa de Pós-Graduação em Ciências Sociais</p>
            <p>Data sourced from Lattes Platform</p>
        </div>
    </footer>
</body>
</html>"""

        # Create faculty directory
        faculty_dir = output_dir / 'faculty'
        faculty_dir.mkdir(exist_ok=True)
        
        with open(faculty_dir / f'{slug}.html', 'w', encoding='utf-8') as f:
            f.write(faculty_html)
        print(f"✓ Generated faculty page: {slug}.html")
    
    # Create a placeholder image
    placeholder_path = assets_dir / 'images' / 'placeholder.png'
    if not placeholder_path.exists():
        # Create a simple colored placeholder using CSS in HTML instead
        pass  # We'll handle this in the HTML with CSS
    
    # Create a simple README for the docs folder
    readme_content = """# PPGS Faculty Site

This site is automatically generated from Lattes data.

To regenerate:
1. Run `python3 process_lattes_final.py` to process Lattes JSON files
2. Run `python3 generate_site.py` to generate the static site
3. Commit and push to GitHub (the docs folder is served by GitHub Pages)

Last updated: $(date)
"""
    with open(output_dir / 'README.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print(f"✓ Generated README.md")
    
    print()
    print("=" * 50)
    print("Site generation complete!")
    print(f"Output directory: {output_dir.absolute()}")
    print("To deploy to GitHub Pages:")
    print("  1. Commit the docs/ folder to your repository")
    print("  2. Go to repo Settings → Pages")
    print("  3. Select source: Deploy from a branch → main branch → /docs folder")
    print("  4. Save and wait for deployment")
    print("=" * 50)

if __name__ == '__main__':
    generate_site()