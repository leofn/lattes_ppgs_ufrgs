#!/usr/bin/env python3
"""Gera o site do PPGS/UFRGS com dashboard + páginas individuais + Qualis + citações."""

import json, re, html, os
from pathlib import Path
from urllib.parse import quote
from collections import Counter

BASE = Path("/home/hermes/lattes_ppgs_ufrgs")
DOCS = BASE / "docs"
FACULTY_DIR = DOCS / "faculty"

# Carregar dados
with open(BASE / "data/processed/faculty_data_enhanced.json") as f:
    faculty = json.load(f)

with open(BASE / "data/processed/qualis_data.json") as f:
    qualis_data = json.load(f)

with open(BASE / "data/processed/ppgs_rankings.json") as f:
    rankings = json.load(f)

with open(BASE / "data/ppgs_docentes.json") as f:
    docentes = json.load(f)

# Qualis scores
QUALIS_SCORES = {'A1': 100, 'A2': 90, 'A3': 80, 'A4': 70, 'B1': 60, 'B2': 50, 'B3': 40, 'B4': 30, 'C': 10, 'NI': 0}
QUALIS_COLORS = {'A1': '#1a472a', 'A2': '#2d5a3d', 'A3': '#3d7a4d', 'A4': '#4d9a5d',
                 'B1': '#b8650e', 'B2': '#d6780e', 'B3': '#f88017', 'B4': '#ffa500',
                 'C': '#888888', 'NI': '#cccccc'}

# Calcular score Qualis por docente
docente_scores = {}
for doc, counts in qualis_data.get('por_docente', {}).items():
    score = sum(QUALIS_SCORES.get(e, 0) * c for e, c in counts.items())
    docente_scores[doc] = score

# Adicionar email e score aos faculty
for f_item in faculty:
    name = f_item.get('name', '')
    for d in docentes:
        if d['lattes_id'] == f_item.get('id', ''):
            f_item['email'] = d.get('email', '')
            break
    f_item['qualis_score'] = docente_scores.get(name, 0)

# Stats
stats = {
    'docentes': len(faculty),
    'doutores': 30,
    'pos_doc': sum(1 for f in faculty if any('Pós' in e.get('type', '') or 'Pós' in e.get('description', '') for e in f.get('education', []))),
    'projetos': sum(len(f.get('research_projects', [])) for f in faculty),
    'orientacoes': sum(f.get('statistics', {}).get('completed_supervisions', 0) + f.get('statistics', {}).get('ongoing_supervisions', 0) for f in faculty),
    'artigos': sum(f.get('statistics', {}).get('journal_articles', 0) for f in faculty),
    'citacoes': sum(f.get('google_scholar', {}).get('citations', 0) for f in faculty),
}

# ============ GERAR PÁGINAS INDIVIDUAIS ============
FACULTY_DIR.mkdir(parents=True, exist_ok=True)

def esc(s):
    return html.escape(str(s)) if s else ''

for f_item in faculty:
    name = f_item.get('name', 'Unknown')
    slug = quote(name.lower().replace(' ', '-'))
    stats_f = f_item.get('statistics', {})
    gs = f_item.get('google_scholar', {})
    pubs = f_item.get('publications', {})
    
    # Artigos com Qualis
    articles = pubs.get('journal_articles', [])
    qualis_counts = Counter()
    for art in articles:
        # Buscar qualis pelo nome da revista
        q = 'NI'
        journal = art.get('journal', '')
        # Procurar no qualis_data
        for doc, counts in qualis_data.get('por_docente', {}).items():
            if doc == name:
                break
        qualis_counts[q] += 1
    
    # Score
    score = f_item.get('qualis_score', 0)
    
    page = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(name)} — PPGS/UFRGS</title>
<link rel="stylesheet" href="../assets/css/style.css">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
.profile-header {{ background: linear-gradient(135deg, #1a237e, #283593); color: white; padding: 40px 30px; border-radius: 12px; margin-bottom: 30px; }}
.profile-header h1 {{ margin: 0 0 8px; font-size: 1.8em; }}
.profile-header .subtitle {{ opacity: 0.9; font-size: 1.05em; }}
.profile-section {{ background: white; border-radius: 10px; padding: 24px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
.profile-section h2 {{ color: #1a237e; font-size: 1.25em; margin: 0 0 16px; border-bottom: 2px solid #e8eaf6; padding-bottom: 8px; }}
.stat-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 12px; }}
.stat-card {{ background: #f5f5f5; border-radius: 8px; padding: 16px; text-align: center; }}
.stat-card .num {{ font-size: 1.8em; font-weight: 700; color: #1a237e; }}
.stat-card .label {{ font-size: 0.85em; color: #666; margin-top: 4px; }}
.pub-list {{ list-style: none; padding: 0; }}
.pub-list li {{ padding: 10px 0; border-bottom: 1px solid #eee; }}
.pub-list li:last-child {{ border-bottom: none; }}
.pub-title {{ font-weight: 600; color: #333; }}
.pub-journal {{ color: #666; font-size: 0.9em; }}
.pub-year {{ color: #999; font-size: 0.85em; }}
.qualis-badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; font-weight: 700; color: white; margin-left: 8px; }}
.back-link {{ display: inline-block; margin-bottom: 20px; color: #1a237e; text-decoration: none; font-weight: 600; }}
.back-link:hover {{ text-decoration: underline; }}
.score-card {{ background: linear-gradient(135deg, #1a472a, #2d5a3d); color: white; }}
.score-card .num {{ color: #a5d6a7; }}
</style>
</head>
<body style="background:#f0f0f5; margin:0; padding:20px; font-family:system-ui,sans-serif; max-width:900px; margin:0 auto;">

<a href="../index.html" class="back-link">← Voltar ao dashboard</a>

<div class="profile-header">
  <h1>{esc(name)}</h1>
  <div class="subtitle">
    {'<br>'.join([esc(e.get('type','')) + ' — ' + esc(e.get('institution','')) for e in f_item.get('education', [])[:3]])}
  </div>
  <div style="margin-top:12px;">
    <a href="{esc(f_item.get('lattes_url',''))}" target="_blank" style="color:#90caf9;text-decoration:none;">📋 Currículo Lattes ↗</a>
    {f' &nbsp; <a href="mailto:{esc(f_item.get("email",""))}" style="color:#90caf9;text-decoration:none;">✉️ {esc(f_item.get("email",""))}</a>' if f_item.get('email') else ''}
    {f' &nbsp; <a href="https://www.semanticscholar.org/author/{esc(gs.get("scholar_id",""))}" target="_blank" style="color:#90caf9;text-decoration:none;">📚 Semantic Scholar ({gs.get("citations",0)} citações) ↗</a>' if gs.get('scholar_id') else ''}
  </div>
</div>

<div class="stat-grid">
  <div class="stat-card"><div class="num">{stats_f.get('journal_articles',0)}</div><div class="label">Artigos</div></div>
  <div class="stat-card"><div class="num">{stats_f.get('books',0)}</div><div class="label">Livros</div></div>
  <div class="stat-card"><div class="num">{stats_f.get('book_chapters',0)}</div><div class="label">Capítulos</div></div>
  <div class="stat-card"><div class="num">{len(f_item.get('research_projects',[]))}</div><div class="label">Projetos</div></div>
  <div class="stat-card"><div class="num">{stats_f.get('completed_supervisions',0)+stats_f.get('ongoing_supervisions',0)}</div><div class="label">Orientações</div></div>
  <div class="stat-card"><div class="num">{gs.get('citations',0)}</div><div class="label">Citações</div></div>
  <div class="stat-card score-card"><div class="num">{score}</div><div class="label">Score Qualis</div></div>
</div>

{f'<div class="profile-section"><h2>📖 Resumo</h2><p>{esc(f_item.get("summary",""))}</p></div>' if f_item.get('summary') else ''}

{f'''<div class="profile-section"><h2>🎓 Formação</h2><ul>
{chr(10).join([f'<li><strong>{esc(e.get("type",""))}</strong> — {esc(e.get("institution",""))} ({esc(e.get("start_year",""))}-{esc(e.get("end_year",""))})</li>' for e in f_item.get('education',[])])}
</ul></div>''' if f_item.get('education') else ''}

{f'''<div class="profile-section"><h2>🔬 Áreas de Atuação</h2><ul>
{chr(10).join([f'<li>{esc(a.get("area",""))}</li>' for a in f_item.get('areas_of_expertise',[])[:10]])}
</ul></div>''' if f_item.get('areas_of_expertise') else ''}

{f'''<div class="profile-section"><h2>📄 Artigos Publicados ({len(articles)})</h2>
<ul class="pub-list">
{chr(10).join([f'<li><div class="pub-title">{esc(a.get("title",""))}</div><div class="pub-journal">{esc(a.get("journal",""))} • v. {esc(a.get("volume",""))}, p. {esc(a.get("pages",""))} • <span class="pub-year">{esc(a.get("year",""))}</span></div></li>' for a in articles[:30]])}
</ul>
{f'<p style="color:#999;font-size:0.9em;margin-top:10px;">+ {len(articles)-30} artigos não exibidos</p>' if len(articles) > 30 else ''}
</div>''' if articles else ''}

{f'''<div class="profile-section"><h2>📚 Livros Publicados ({len(pubs.get("books",[]))})</h2>
<ul class="pub-list">
{chr(10).join([f'<li><div class="pub-title">{esc(b.get("title",""))}</div><div class="pub-journal">{esc(b.get("publisher",""))}, {esc(b.get("place",""))} • <span class="pub-year">{esc(b.get("year",""))}</span></div></li>' for b in pubs.get('books',[])[:20]])}
</ul></div>''' if pubs.get('books') else ''}

{f'''<div class="profile-section"><h2>🔧 Projetos de Pesquisa ({len(f_item.get("research_projects",[]))})</h2>
<ul class="pub-list">
{chr(10).join([f'<li><div class="pub-title">{esc(p.get("name",""))}</div><div class="pub-year">{esc(p.get("start_year",""))}-{esc(p.get("end_year",""))}</div></li>' for p in f_item.get('research_projects',[])[:20]])}
</ul></div>''' if f_item.get('research_projects') else ''}

<div style="text-align:center;margin-top:30px;color:#999;font-size:0.85em;">
  PPGS/UFRGS · LABHD-UFRGS · Dados extraídos da Plataforma Lattes (CNPq)
</div>
</body>
</html>"""
    
    with open(FACULTY_DIR / f"{slug}.html", 'w', encoding='utf-8') as f:
        f.write(page)

print(f"✓ {len(faculty)} páginas individuais geradas em {FACULTY_DIR}")

# ============ GERAR DASHBOARD ============
template = Path("/home/hermes/lattes_ppgcs/docs/index.html").read_text()

# Cards
cards = []
for f_item in faculty:
    name = f_item.get('name', '')
    slug = quote(name.lower().replace(' ', '-'))
    s = f_item.get('statistics', {})
    gs = f_item.get('google_scholar', {})
    cards.append({
        'nome': name, 'name': name,
        'slug': slug,
        'lattes_url': f_item.get('lattes_url', ''),
        'email': f_item.get('email', ''),
        'formacao': '; '.join([e.get('type', '') + ' - ' + e.get('institution', '') for e in f_item.get('education', [])[:3]]),
        'areas': '; '.join([a.get('area', '') for a in f_item.get('areas_of_expertise', [])[:3]]),
        'resumo': f_item.get('summary', '')[:300],
        'doutorado': any('Doutorado' in e.get('type', '') for e in f_item.get('education', [])),
        'pos_doutorado': any('Pós' in e.get('type', '') or 'Pós' in e.get('description', '') for e in f_item.get('education', [])),
        'ultima_atualizacao': f_item.get('last_update', ''),
        'num_projetos': len(f_item.get('research_projects', [])),
        'num_orient_total': s.get('completed_supervisions', 0) + s.get('ongoing_supervisions', 0),
        'num_artigos': s.get('journal_articles', 0),
        'num_livros': s.get('books', 0),
        'num_capitulos': s.get('book_chapters', 0),
        'scholar_citacoes': gs.get('citations', 0),
        'qualis_score': f_item.get('qualis_score', 0),
    })

data_json = json.dumps(cards, ensure_ascii=False)
data_start = template.find("const DATA = [")
data_end = template.find("\n];", data_start) + 3
html_content = template[:data_start] + f"const DATA = {data_json};" + template[data_end:]

# Rankings
rank_json = json.dumps(rankings, ensure_ascii=False)
rank_start = html_content.find("const RANK")
if rank_start > 0:
    rank_end = html_content.find("};", rank_start) + 2
    html_content = html_content[:rank_start] + f"const RANKINGS = {rank_json};" + html_content[rank_end:]

# Textos
html_content = html_content.replace("PPGCS/UFBA", "PPGS/UFRGS")
html_content = html_content.replace("PPGCS", "PPGS")
html_content = html_content.replace("Ciências Sociais da UFBA", "Sociologia da UFRGS")
html_content = html_content.replace("Ciências Sociais — UFBA", "Sociologia — UFRGS")
html_content = html_content.replace("UFBA", "UFRGS")
html_content = html_content.replace("LABHD-UFBA", "LABHD-UFRGS")

# Stats bar
for old, new in [('23', str(stats['docentes'])), ('20', str(stats['pos_doc'])),
                 ('736', str(stats['projetos'])), ('1692', str(stats['orientacoes'])),
                 ('1084', '0'), ('69', str(stats['artigos'])), ('9360', str(stats['citacoes']))]:
    html_content = re.sub(f'<div class="num">{old}</div>', f'<div class="num">{new}</div>', html_content, count=1)

# Doutores
html_content = html_content.replace('class="num">23</div><div class="label">Doutores', 
                                     f'class="num">{stats["doutores"]}</div><div class="label">Doutores')

# Subtítulo
html_content = re.sub(
    r'\d+ docentes · \d+ projetos · \d+ orientações · \d+ citações · Coleta: \d+/\d+/\d+',
    f'{stats["docentes"]} docentes · {stats["projetos"]} projetos · {stats["orientacoes"]} orientações · {stats["citacoes"]} citações · Coleta: 09/10/2026',
    html_content)

# Adicionar ranking Qualis Score + seção Qualis
estrato_order = ['A1', 'A2', 'A3', 'A4', 'B1', 'B2', 'B3', 'B4', 'C', 'NI']
dist = qualis_data['distribuicao']
dist_sorted = {e: dist.get(e, 0) for e in estrato_order if e in dist}

qualis_section = f'''
<!-- Qualis Section -->
<div class="charts-section" id="qualis-section">
  <h2>📊 Classificação Qualis CAPES + Pontuação</h2>
  <p style="color:#666;margin-bottom:20px;">Distribuição dos artigos por estrato Qualis (quadriênio 2017-2020). Pontuação: A1=100, A2=90, A3=80, A4=70, B1=60, B2=50, B3=40, B4=30, C=10.</p>
  <canvas id="qualisChart" style="max-height:400px;margin-bottom:30px;"></canvas>
  
  <h3>🏆 Ranking Pontuação Qualis</h3>
  <div id="qualisRanking"></div>
  
  <h3>📋 Qualis por Docente</h3>
  <div style="overflow-x:auto;">
    <table id="qualisTable" style="width:100%;border-collapse:collapse;font-size:13px;">
      <thead><tr style="border-bottom:2px solid #557EB5;">
        <th style="text-align:left;padding:8px;">Docente</th>
        {''.join(f'<th style="text-align:center;padding:8px;">{e}</th>' for e in estrato_order if e in dist)}
        <th style="text-align:center;padding:8px;">Score</th>
        <th style="text-align:center;padding:8px;">Total</th>
      </tr></thead>
      <tbody id="qualisTableBody"></tbody>
    </table>
  </div>
</div>
<script>
const QUALIS_DATA = {json.dumps(qualis_data, ensure_ascii=False)};
const QUALIS_SCORES = {json.dumps(QUALIS_SCORES)};
const ESTRATO_ORDER = {json.dumps(estrato_order)};
const ESTRATO_COLORS = {json.dumps(QUALIS_COLORS)};
const distSorted = {json.dumps(dist_sorted)};
const qualisScoreRank = {json.dumps(rankings.get('qualis_score', []))};

new Chart(document.getElementById("qualisChart"),{{type:"bar",data:{{labels:Object.keys(distSorted),datasets:[{{label:"Artigos",data:Object.values(distSorted),backgroundColor:Object.keys(distSorted).map(e=>ESTRATO_COLORS[e]||"#888")}}]}},options:{{responsive:true,scales:{{y:{{beginAtZero:true}}}}}}}});

// Ranking score
const qr = document.getElementById("qualisRanking");
qualisScoreRank.forEach((r,i) => {{
  const div = document.createElement("div");
  div.style.cssText = "display:flex;align-items:center;gap:12px;padding:8px 0;border-bottom:1px solid #eee;";
  div.innerHTML = '<span style="font-weight:700;color:#1a237e;width:30px;">' + (i+1) + 'º</span>' +
    '<span style="flex:1;">' + r.nome + '</span>' +
    '<span style="font-weight:700;color:#1a472a;">' + r.val + ' pts</span>';
  qr.appendChild(div);
}});

// Tabela por docente
const tb=document.getElementById("qualisTableBody");
Object.keys(QUALIS_DATA.por_docente).sort().forEach(doc=>{{
  const c=QUALIS_DATA.por_docente[doc];
  const total=Object.values(c).reduce((a,b)=>a+b,0);
  const score=Object.entries(c).reduce((a,[e,n])=>a+(QUALIS_SCORES[e]||0)*n,0);
  let cells="<td style='padding:6px;'>" + doc + "</td>";
  ESTRATO_ORDER.forEach(e=>{{
    if(QUALIS_DATA.distribuicao[e]){{
      const n=c[e]||0;
      cells+="<td style='text-align:center;padding:6px;" + (n>0?"color:"+ESTRATO_COLORS[e]+";font-weight:bold;":"color:#ccc;") + "'>" + (n>0?n:"") + "</td>";
    }}
  }});
  cells+="<td style='text-align:center;padding:6px;font-weight:bold;color:#1a472a;'>" + score + "</td>";
  cells+="<td style='text-align:center;padding:6px;font-weight:bold;'>" + total + "</td>";
  const row=document.createElement("tr");
  row.style.borderBottom="1px solid #eee";
  row.innerHTML=cells;
  tb.appendChild(row);
}});
</script>
'''

body_end = html_content.rfind('</body>')
html_content = html_content[:body_end] + qualis_section + html_content[body_end:]

# Adicionar link "Ver Perfil" nos cards
# O template do PPGCS tem cards com link Lattes. Vou adicionar link para a página individual.
# Procurar por "Lattes" no template e adicionar "Perfil" ao lado
html_content = html_content.replace(
    '<a href="\' + d.lattes_url + \'" target="_blank"',
    '<a href="faculty/\' + (d.slug || d.nome.toLowerCase().replace(/\\s/g, \'-\')) + \'.html" class="btn">Ver Perfil</a> <a href="\' + d.lattes_url + \'" target="_blank"'
)

# Salvar
with open(DOCS / "index.html", 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"✓ Dashboard gerado: {len(html_content)} chars")
print(f"✓ Stats: {stats}")
print(f"✓ {len(cards)} cards com link para perfil individual")
print(f"✓ Qualis score ranking + tabela com pontuação")
print(f"✓ Citações: {stats['citacoes']} total")