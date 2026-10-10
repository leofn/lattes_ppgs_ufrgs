#!/usr/bin/env python3
"""Reprocessa todos os HTMLs Lattes corrigindo encoding (Latin-1 vs UTF-8)
e regera o dataset com contagens e textos corretos."""

import json, re, os, sys, unicodedata
from pathlib import Path
from bs4 import BeautifulSoup

OUTPUT_DIR = Path("/home/hermes/lattes_ppgs_ufrgs/output/ppgs")
DATASET_OUTPUT = Path("/home/hermes/lattes_ppgs_ufrgs/data/processed/ppgs_dataset.json")

def read_html_correct(path):
    """Lê HTML detectando encoding automaticamente."""
    raw = path.read_bytes()
    # Tentar UTF-8
    try:
        text = raw.decode('utf-8')
        if '\ufffd' not in text:
            return text
    except:
        pass
    # Latin-1 (ISO-8859-1) — usado pelo curl
    return raw.decode('latin-1', errors='replace')

def parse_lattes_correct(html):
    """Parser robusto do HTML do Lattes com encoding correto."""
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text(separator='\n', strip=True)
    
    # Normalizar quebras de linha
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Helper: encontrar seção pelo nome (flexível com acentos)
    def find_section(nome):
        # Pattern flexível: aceita com ou sem acentos
        pattern = re.escape(nome).replace(r'\ ', r'\s+')
        m = re.search(pattern, text, re.IGNORECASE)
        if not m:
            # Tentar sem acentos
            nome_norm = unicodedata.normalize('NFKD', nome).encode('ASCII', 'ignore').decode('ASCII')
            text_norm = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
            m = re.search(re.escape(nome_norm).replace(r'\ ', r'\s+'), text_norm, re.IGNORECASE)
            if m:
                # Mapear de volta para o texto original
                return text[m.start():]
        if m:
            return text[m.end():]
        return ''
    
    # Helper: contar ocorrências de um padrão numa seção
    def count_in_section(section, pattern):
        return len(re.findall(pattern, section, re.IGNORECASE))
    
    # Helper: encontrar a ÚLTIMA ocorrência (a primeira é o menu/índice)
    def find_section_last(nome):
        pattern = re.escape(nome).replace(r'\ ', r'\s+')
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        if not matches:
            # Tentar sem acentos
            nome_norm = unicodedata.normalize('NFKD', nome).encode('ASCII', 'ignore').decode('ASCII')
            text_norm = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
            matches = list(re.finditer(re.escape(nome_norm).replace(r'\ ', r'\s+'), text_norm, re.IGNORECASE))
            if matches:
                # Pegar o último match e converter posição
                m = matches[-1]
                return text[m.start():]
        if matches:
            m = matches[-1]
            return text[m.end():]
        return ''
    
    # Nome
    nome = ''
    m = re.search(r'(?:Nome|Nome em citações bibliográficas)[:\s]*([^\n]+)', text)
    if m:
        nome = m.group(1).strip()
    if not nome:
        # Tentar pegar do título da página
        title = soup.find('title')
        if title:
            nome = title.get_text(strip=True)
    
    # Resumo
    resumo = ''
    m = re.search(r'(?:Resumo|Resumo CV|Texto informado)[:\s]*\n*(.+?)(?:\n\n|\nFormação|\nGraduação)', text, re.DOTALL)
    if m:
        resumo = m.group(1).strip()[:500]
    
    # Formação
    formacao = ''
    m = re.search(r'(?:Formação Acadêmica|Formação)[:\s]*\n(.+?)(?:\n\n|\nAtuação|\nÁreas)', text, re.DOTALL)
    if m:
        formacao = m.group(1).strip()[:300]
    
    # Doutorado
    doutorado = bool(re.search(r'Doutorado', text, re.IGNORECASE))
    pos_doutorado = bool(re.search(r'Pós.Doutorado|Pos.Doutorado', text, re.IGNORECASE))
    mestrado = bool(re.search(r'Mestrado', text, re.IGNORECASE))
    
    # Áreas
    areas = ''
    m = re.search(r'(?:Áreas? de atuação|Areas? de atuação)[:\s]*\n(.+?)(?:\n\n|\nIdiomas|\nPrêmios)', text, re.DOTALL)
    if m:
        areas = m.group(1).strip()[:500]
    
    # Linhas de pesquisa
    linhas = ''
    m = re.search(r'(?:Linhas? de pesquisa)[:\s]*\n(.+?)(?:\n\n|\nProjetos|\nÁreas)', text, re.DOTALL)
    if m:
        linhas = m.group(1).strip()[:500]
    
    # ===== CONTAGENS =====
    # Usar a ÚLTIMA ocorrência de cada seção (a primeira é o índice/menu)
    
    # Artigos
    artigos_section = find_section_last('Artigos completos publicados')
    # Fim: próxima seção
    end = re.search(r'(?:Livros publicados|Capítulos|Textos em|Trabalhos completos)', artigos_section)
    if end:
        artigos_section = artigos_section[:end.start()]
    # Contar: padrão é NÚMERO.AUTOR ANO
    # Cada artigo começa com um número seguido de ponto
    artigo_nums = re.findall(r'(?:^|\n)\s*(\d+)\.\s*[A-Z]', artigos_section)
    num_artigos = len(artigo_nums)
    
    # Livros
    livros_section = find_section_last('Livros publicados')
    end = re.search(r'(?:Capítulos|Textos em|Trabalhos completos|Resumos|Apresentações)', livros_section)
    if end:
        livros_section = livros_section[:end.start()]
    livro_nums = re.findall(r'(?:^|\n)\s*(\d+)\.\s*[A-Z]', livros_section)
    num_livros = len(livro_nums)
    
    # Capítulos
    cap_section = find_section_last('Capítulos')
    end = re.search(r'(?:Textos em|Trabalhos completos|Resumos|Apresentações|Outras)', cap_section)
    if end:
        cap_section = cap_section[:end.start()]
    cap_nums = re.findall(r'(?:^|\n)\s*(\d+)\.\s*[A-Z]', cap_section)
    num_capitulos = len(cap_nums)
    
    # Textos em mídia
    midia_section = find_section_last('Textos em meios')
    if not midia_section:
        midia_section = find_section_last('Textos em jornais')
    midia_nums = re.findall(r'(?:^|\n)\s*(\d+)\.\s*[A-Z]', midia_section)
    num_textos_midia = len(midia_nums)
    
    # Projetos
    proj_section = find_section_last('Projetos de pesquisa')
    if not proj_section:
        proj_section = find_section_last('Projetos')
    end = re.search(r'(?:Projetos de extensão|Projetos de desenvolvimento|Áreas|Idiomas)', proj_section)
    if end:
        proj_section = proj_section[:end.start()]
    proj_nums = re.findall(r'(?:^|\n)\s*(\d+)\.\s*[A-Z]', proj_section)
    num_projetos = len(proj_nums)
    
    # Projetos extensão
    ext_section = find_section_last('Projetos de extensão')
    ext_nums = re.findall(r'(?:^|\n)\s*(\d+)\.\s*[A-Z]', ext_section)
    num_projetos_ext = len(ext_nums)
    
    # Projetos desenvolvimento
    dev_section = find_section_last('Projetos de desenvolvimento')
    dev_nums = re.findall(r'(?:^|\n)\s*(\d+)\.\s*[A-Z]', dev_section)
    num_projetos_dev = len(dev_nums)
    
    # Orientações
    orient_section = find_section_last('Orientações')
    # Contar por tipo
    num_orient_doutorado = len(re.findall(r'(?:Doutorado|Tese.*?Doutorado)', orient_section, re.IGNORECASE))
    num_orient_mestrado = len(re.findall(r'(?:Mestrado|Dissertação.*?Mestrado)', orient_section, re.IGNORECASE))
    num_orient_ic = len(re.findall(r'(?:Iniciação Científica|IC)', orient_section, re.IGNORECASE))
    num_orient_tcc = len(re.findall(r'(?:TCC|Trabalho de conclusão)', orient_section, re.IGNORECASE))
    # Total: contar entradas numeradas
    orient_nums = re.findall(r'(?:^|\n)\s*(\d+)\.\s*[A-Z]', orient_section)
    num_orient_total = len(orient_nums)
    
    # Bancas
    bancas_section = find_section_last('Participação em bancas')
    bancas_nums = re.findall(r'(?:^|\n)\s*(\d+)\.\s*[A-Z]', bancas_section)
    num_bancas_total = len(bancas_nums)
    num_bancas_doutorado = len(re.findall(r'Doutorado', bancas_section, re.IGNORECASE))
    num_bancas_mestrado = len(re.findall(r'Mestrado', bancas_section, re.IGNORECASE))
    
    # Eventos
    eventos_section = find_section_last('Participação em eventos')
    eventos_nums = re.findall(r'(?:^|\n)\s*(\d+)\.\s*[A-Z]', eventos_section)
    num_eventos = len(eventos_nums)
    
    # Premios
    premios_section = find_section_last('Prêmios')
    premios_nums = re.findall(r'(?:^|\n)\s*(\d+)\.\s*[A-Z]', premios_section)
    num_premios = len(premios_nums)
    
    # Idiomas
    idiomas_section = find_section('Idiomas')
    
    # Atuação
    atuacao_section = find_section('Atuação profissional')
    
    # Última atualização
    ultima_att = ''
    m = re.search(r'(?:Última atualização|atualizado)[:\s]*(\d{2}/\d{2}/\d{4})', text, re.IGNORECASE)
    if m:
        ultima_att = m.group(1)
    
    # Lattes ID e URL
    lattes_id = ''
    lattes_url = ''
    
    # Secoes encontradas
    secoes = []
    for s in ['Artigos completos', 'Livros publicados', 'Capítulos', 'Projetos de pesquisa',
              'Orientações', 'Bancas', 'Eventos', 'Prêmios', 'Idiomas']:
        if find_section(s):
            secoes.append(s)
    
    return {
        'nome': nome,
        'resumo': resumo,
        'formacao': formacao,
        'doutorado': doutorado,
        'pos_doutorado': pos_doutorado,
        'mestrado': mestrado,
        'areas': areas,
        'linhas_pesquisa': linhas,
        'ultima_atualizacao': ultima_att,
        'num_artigos': num_artigos,
        'num_livros': num_livros,
        'num_capitulos': num_capitulos,
        'num_textos_midia': num_textos_midia,
        'num_projetos': num_projetos,
        'num_projetos_extensao': num_projetos_ext,
        'num_projetos_dev': num_projetos_dev,
        'num_orient_doutorado': num_orient_doutorado,
        'num_orient_mestrado': num_orient_mestrado,
        'num_orient_ic': num_orient_ic,
        'num_orient_tcc': num_orient_tcc,
        'num_orient_total': num_orient_total,
        'num_bancas_total': num_bancas_total,
        'num_bancas_doutorado': num_bancas_doutorado,
        'num_bancas_mestrado': num_bancas_mestrado,
        'num_eventos': num_eventos,
        'num_premios': num_premios,
        'idiomas': idiomas_section[:500],
        'atuacao': atuacao_section[:500],
        'secoes': secoes,
        'num_secoes': len(secoes),
        'full_text_len': len(text),
    }

# Carregar lista de docentes
with open("/home/hermes/lattes_ppgs_ufrgs/data/ppgs_docentes.json") as f:
    docentes = json.load(f)

# Processar cada HTML
dataset = []
htmls = sorted(OUTPUT_DIR.glob("*.html"))

for i, hf in enumerate(htmls):
    # Extrair ID do nome do arquivo
    m = re.search(r'_(\d{16})\.html$', hf.name)
    lattes_id = m.group(1) if m else ''
    
    # Encontrar o docente correspondente
    docente = None
    for d in docentes:
        if d['lattes_id'] == lattes_id:
            docente = d
            break
    
    # Ler HTML com encoding correto
    html = read_html_correct(hf)
    
    # Parse
    data = parse_lattes_correct(html)
    
    # Adicionar metadados
    data['lattes_id'] = lattes_id
    data['lattes_url'] = f"http://lattes.cnpq.br/{lattes_id}"
    data['email'] = docente['email'] if docente else ''
    data['nome'] = docente['nome'] if docente else data.get('nome', '')
    data['nome_site'] = data['nome']
    data['arquivo'] = hf.name
    
    dataset.append(data)
    
    print(f"[{i+1:02d}] {data['nome'][:35]:35s} art={data['num_artigos']:3d} liv={data['num_livros']:3d} cap={data['num_capitulos']:3d} proj={data['num_projetos']:3d} orient={data['num_orient_total']:3d} bancas={data['num_bancas_total']:3d}")

# Salvar
DATASET_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
with open(DATASET_OUTPUT, 'w', encoding='utf-8') as f:
    json.dump(dataset, f, ensure_ascii=False, indent=2)

# Estatísticas
total_art = sum(d['num_artigos'] for d in dataset)
total_liv = sum(d['num_livros'] for d in dataset)
total_cap = sum(d['num_capitulos'] for d in dataset)
total_proj = sum(d['num_projetos'] for d in dataset)
total_orient = sum(d['num_orient_total'] for d in dataset)
total_bancas = sum(d['num_bancas_total'] for d in dataset)

print(f"\n{'='*60}")
print(f"TOTAL: {len(dataset)} docentes")
print(f"  Artigos: {total_art}")
print(f"  Livros: {total_liv}")
print(f"  Capítulos: {total_cap}")
print(f"  Projetos: {total_proj}")
print(f"  Orientações: {total_orient}")
print(f"  Bancas: {total_bancas}")