#!/usr/bin/env python3
"""
Consolida currículos Lattes de um programa de pós-graduação em um dataset único.

Pipeline Lattes → Dataset → Site (GitHub Pages)
===============================================

Este script é a etapa 2 de um pipeline de 4 etapas:

1. **Download**      — `batch_download_ppgcs.py`: baixa currículos Lattes via Selenium + 2Captcha
2. **Consolidação**  — `consolidate_ppgcs.py` (este arquivo): extrai métricas de cada CV
3. **Scholar**        — `update_scholar.py`: enriquece com dados do Google Scholar
4. **Site**           — `generate_site.py`: gera index.html com dashboard interativo

Projetado para ser reutilizável em qualquer programa de pós-graduação da UFBA.
Para adaptar a outro programa, altere apenas:
  - OUTPUT_DIR: diretório com os JSONs dos currículos
  - DOCENTES_FILE: JSON com a lista de docentes (nome, email, lattes_id)
  - PROGRAM_NAME: nome do programa (para títulos e metadados)

Author: Leonardo Fernandes Nascimento (LABHD-UFBA)
License: MIT
"""

import json
import re
from pathlib import Path
from collections import Counter

# ============================================================
# CONFIGURAÇÃO — Alterar这些 parâmetros para outros programas
# ============================================================
OUTPUT_DIR = Path("/home/hermes/lattes_ppgs_ufrgs/output/ppgs")
DOCENTES_FILE = Path("/home/hermes/lattes_ppgs_ufrgs/data/ppgs_docentes.json")
DATASET_OUTPUT = Path("/home/hermes/lattes_ppgs_ufrgs/data/processed/ppgs_dataset.json")
PROGRAM_NAME = "PPGS/UFRGS"
TOP_N_RANKINGS = 5  # Quantos professores mostrar em cada ranking

# ============================================================
# PARSER DE PRODUÇÃO BIBLIOGRÁFICA — v9
# ============================================================
# Lista de headers de seções de produção do Lattes.
# Usada para delimitar blocos e evitar que sub-headers sejam
# contados como itens individuais.
HEADERS_PROD = [
    'Artigos completos publicados em periódicos',
    'Artigos aceitos para publicação',
    'Livros publicados/organizados',
    'Capítulos de livros publicados',
    'Textos em jornais de notícias/revistas',
    'Textos em revistas ou periódicos',
    'Trabalhos completos publicados em anais de congressos',
    'Trabalhos em anais de congressos',
    'Resumos publicados em anais de congressos',
    'Apresentações de trabalhos',
    'Apresentações de Trabalho',
    'Demais tipos de produção bibliográfica',
    'Demais tipos de produção técnica',
    'Produção artística/cultural',
    'Processos ou técnicas',
    'Trabalhos técnicos',
    'Software',
    'Patente',
    'Organização de evento',
    'Participação em evento',
    'Editoração',
    'Outra produção técnica',
    'Outra produção bibliográfica',
    'Curadoria',
    'Maquete',
    'Programa de rádio',
    'Programa de TV',
    'Reportagem',
    'Tradução',
    'Revisão',
    'Prefácio',
    'Pós-textual',
]

# Prefixos de sub-campos que NÃO são números de item
# (evita contar "v.42", "p.15", "n.3", "ed.2", etc. como itens)
SUBFIELD_PREFIXES = ('v.', 'p.', 'n.', 'ed.', 'vol.', 'no.', 'fasc.')


def count_itens_producao(prod_text, section_name):
    """
    Conta itens individuais numerados em uma seção de produção do Lattes.

    O Lattes estrutura a produção bibliográfica em 3 blocos duplicados
    (Ordenar por: Ordem de Importância, Cronológica, Citações), cada um
    contendo os mesmos itens em ordem diferente. O bloco "Ordem de Importância"
    é o mais confiável porque não tem contadores de citação no caminho.

    Problemas resolvidos (v9):
    1. Blocos duplicados — pegar max_count entre todos os blocos
    2. Contadores "Citações:N|M" grudados com números de item — remover antes de contar
    3. Sub-headers grudados com números ("271.Textos em jornais...") — lista expandida de headers
    4. Número secundário de ranking ("1.2AUTOR" = item 1, rank 2) — regex aceita rank opcional

    Args:
        prod_text: texto da seção "producoes" do JSON do Lattes
        section_name: nome da seção (ex: "Artigos completos publicados em periódicos")

    Returns:
        int: número de itens individuais na seção
    """
    if not prod_text:
        return 0

    # Normalizar whitespace
    norm = re.sub(r'\s+', ' ', prod_text).strip()

    # Encontrar todas as ocorrências do header da seção
    # (haverá 3: uma em cada bloco de ordenação)
    section_positions = [m.start() for m in re.finditer(re.escape(section_name), norm, re.I)]
    if not section_positions:
        return 0

    max_count = 0
    for pos in section_positions:
        # Delimitar o bloco: do header atual até o próximo header de outra seção
        end = len(norm)
        for h in HEADERS_PROD:
            if h.lower() == section_name.lower():
                continue
            for m in re.finditer(re.escape(h), norm, re.I):
                h_pos = m.start()
                if h_pos > pos + len(section_name) and h_pos < end:
                    end = h_pos
                    break

        block = norm[pos:end]

        # Remover contadores de citação que podem engolir números de item
        # Padrão: "Citações:12|109.AUTOR" → remove "Citações:12|10" e sobra "9.AUTOR"
        # ou "Citações:15.POSSAS" → remove "Citações:1" e sobra "5.POSSAS" (item 5)
        block_clean = re.sub(r'Citações?:\d+(?:\|\d+)*', '', block, flags=re.I)

        # Encontrar números de item: N.RANK_AUTOR ou N._AUTOR
        # Onde N = número do item (1-3 dígitos)
        #       RANK = número secundário opcional (1-2 dígitos, ranking de citação)
        #       AUTOR = letra maiúscula, aspa, colchete ou parêntese
        items = set()
        for m in re.finditer(
            r"(\d{1,3})\.(?:\d{1,2})?\s*(?=[A-ZÀ-Ú\"'\[(])",
            block_clean
        ):
            n = int(m.group(1))
            # Filtrar anos (1900+) e números inválidos
            if n > 1900 or n < 1:
                continue
            # Filtrar sub-campos bibliográficos (v., p., n., ed., etc.)
            before = block_clean[max(0, m.start()-8):m.start()].lower().rstrip()
            if before.endswith(SUBFIELD_PREFIXES):
                continue
            items.add(n)

        if not items:
            continue

        # Encontrar a sequência 1, 2, 3, ..., N mais longa
        # (o bloco pode ter saltos se um número foi engolido por "Citações:")
        count = 0
        expected = 1
        while expected in items:
            count = expected
            expected += 1

        max_count = max(max_count, count)

    return max_count


# ============================================================
# EXTRAÇÃO DE MÉTRICAS
# ============================================================

def find_json(lattes_id, output_dir=OUTPUT_DIR):
    """Encontra o arquivo JSON correto para um docente."""
    # Tentar arquivo direto
    jf = output_dir / f"{lattes_id}.json"
    if jf.exists():
        data = json.loads(jf.read_text(encoding='utf-8'))
        if data.get("nome") and data["nome"] != "N/A":
            return jf, data
    # Buscar em todos os arquivos
    for jf in sorted(output_dir.glob("*.json")):
        if jf.name.startswith("_"):
            continue
        data = json.loads(jf.read_text(encoding='utf-8'))
        sid = data.get("short_id", "")
        lid = data.get("lattes_id", "")
        if sid == lattes_id or lid == lattes_id:
            return jf, data
    return None, None


def extract_metrics(data, docente_info):
    """
    Extrai métricas-chave do JSON do Lattes.

    Usa o parser v9 para contagem de produções bibliográficas (artigos, livros,
    capítulos), que conta itens individuais numerados em vez de ocorrências
    do header da seção — corrigindo o bug que fazia todos os docentes terem
    valores idênticos (3 artigos, 2 livros, 2 capítulos).
    """
    metrics = {}

    # Campos estruturados
    metrics["nome"] = data.get("nome", docente_info.get("nome", "N/A"))
    metrics["nome_site"] = docente_info.get("nome", "")
    metrics["email"] = docente_info.get("email", "")
    metrics["lattes_url"] = f"http://lattes.cnpq.br/{docente_info.get('lattes_id', '')}"
    metrics["id_lattes"] = data.get("lattes_id", data.get("id_lattes", ""))
    metrics["short_id"] = data.get("short_id", "")
    metrics["ultima_atualizacao"] = data.get("ultima_atualizacao", "")

    # Resumo
    resumo = data.get("resumo", "")
    metrics["resumo"] = resumo[:800] if resumo else ""

    # Formação
    formacao = data.get("formacao_academica", "")
    metrics["formacao"] = formacao[:2000] if formacao else ""

    # Extrair graus
    metrics["doutorado"] = bool(re.search(r'Doutorado', formacao, re.I))
    metrics["pos_doutorado"] = bool(re.search(r'Pós-doutorado|Pós-Doutorado|Post-doctoral|Postdoctoral', formacao, re.I))
    metrics["mestrado"] = bool(re.search(r'Mestrado', formacao, re.I))

    # Áreas de atuação
    areas = data.get("areas_atuacao", "")
    metrics["areas"] = areas[:800] if areas else ""

    # Linhas de pesquisa
    linhas = data.get("linhas_pesquisa", "")
    metrics["linhas_pesquisa"] = linhas[:1500] if linhas else ""

    # Produções (texto completo para o parser)
    prod = data.get("producoes", "")
    metrics["producoes"] = prod[:5000] if prod else ""

    # Google Scholar — extrair do texto se disponível
    scholar = re.search(r'Total de trabalhos:\s*(\d+).*?Total de citações:\s*(\d+)', prod, re.DOTALL)
    if scholar:
        metrics["scholar_trabalhos"] = int(scholar.group(1))
        metrics["scholar_citacoes"] = int(scholar.group(2))
    else:
        metrics["scholar_trabalhos"] = 0
        metrics["scholar_citacoes"] = 0

    # ============================================================
    # CONTAGEM DE PRODUÇÃO BIBLIOGRÁFICA — PARSER v9
    # ============================================================
    # Conta itens individuais numerados, não ocorrências de header.
    # Ver count_itens_producao() para documentação completa dos problemas resolvidos.
    metrics["num_artigos"] = count_itens_producao(prod, 'Artigos completos publicados em periódicos')
    metrics["num_livros"] = count_itens_producao(prod, 'Livros publicados/organizados')
    metrics["num_capitulos"] = count_itens_producao(prod, 'Capítulos de livros publicados')
    metrics["num_textos_midia"] = count_itens_producao(prod, 'Textos em jornais de notícias/revistas')

    # Projetos
    proj = data.get("projetos_pesquisa", "")
    metrics["projetos"] = proj[:3000] if proj else ""
    metrics["num_projetos"] = len(re.findall(r'(?:20\d{2}|19\d{2})\s*-\s*(?:Atual|\d{2,4})', proj))

    # Projetos de extensão
    proj_ext = data.get("projetos_extensao", "")
    metrics["num_projetos_extensao"] = len(re.findall(r'(?:20\d{2}|19\d{2})\s*-\s*(?:Atual|\d{2,4})', proj_ext)) if proj_ext else 0

    # Projetos de desenvolvimento
    proj_dev = data.get("projetos_desenvolvimento", "")
    metrics["num_projetos_dev"] = len(re.findall(r'(?:20\d{2}|19\d{2})\s*-\s*(?:Atual|\d{2,4})', proj_dev)) if proj_dev else 0

    # Orientações
    orient = data.get("orientacoes", "")
    metrics["orientacoes"] = orient[:3000] if orient else ""
    metrics["num_orient_doutorado"] = len(re.findall(r'Tese de doutorado', orient))
    metrics["num_orient_mestrado"] = len(re.findall(r'Dissertação de mestrado|Dissertação \(Mestrado', orient))
    metrics["num_orient_ic"] = len(re.findall(r'Iniciação científica', orient, re.I))
    metrics["num_orient_tcc"] = len(re.findall(r'TCC|Trabalho de conclusão', orient, re.I))
    metrics["num_orient_total"] = (
        metrics["num_orient_doutorado"]
        + metrics["num_orient_mestrado"]
        + metrics["num_orient_ic"]
        + metrics["num_orient_tcc"]
    )

    # Bancas
    bancas = data.get("bancas", "")
    metrics["bancas"] = bancas[:1500] if bancas else ""
    metrics["num_bancas_doutorado"] = len(re.findall(r'Tese de doutorado', bancas))
    metrics["num_bancas_mestrado"] = len(re.findall(r'Dissertação de mestrado|Dissertação \(Mestrado', bancas))
    metrics["num_bancas_total"] = metrics["num_bancas_doutorado"] + metrics["num_bancas_mestrado"]

    # Eventos
    eventos = data.get("eventos", "")
    metrics["eventos"] = eventos[:1000] if eventos else ""

    # Prêmios
    premios = data.get("premios_titulos", "")
    metrics["premios"] = premios[:500] if premios else ""

    # Idiomas
    idiomas = data.get("idiomas", "")
    metrics["idiomas"] = idiomas[:400] if idiomas else ""

    # Atuação profissional
    atuacao = data.get("atuacao_profissional", "")
    metrics["atuacao"] = atuacao[:2000] if atuacao else ""

    # Inovação
    inovacao = data.get("inovacao", "")
    metrics["inovacao"] = inovacao[:500] if inovacao else ""

    # Educação e popularização
    educ = data.get("educacao_popularizacao", "")
    metrics["educacao"] = educ[:1000] if educ else ""

    # Seções
    metrics["secoes"] = data.get("_sections_found", [])
    metrics["num_secoes"] = len(metrics["secoes"])

    # Full text length
    metrics["full_text_len"] = len(data.get("_full_text", ""))

    return metrics


# ============================================================
# GERAÇÃO DE RANKINGS
# ============================================================

def generate_rankings(dataset, top_n=TOP_N_RANKINGS):
    """
    Gera rankings ordenados por valor (descendente) para o dashboard.

    Cada ranking é uma lista de {nome, val} ordenada do maior para o menor.
    Os rankings são usados pelo JavaScript no index.html para renderizar
    os cards de "Top 5" em cada categoria.

    Args:
        dataset: lista de métricas de docentes
        top_n: número de entradas em cada ranking (default 5)

    Returns:
        dict: {"citacoes": [...], "projetos": [...], "orientacoes": [...]}
    """
    rankings = {
        'citacoes': sorted(
            [{'nome': d['nome'], 'val': d.get('scholar_citacoes', 0)} for d in dataset],
            key=lambda x: x['val'], reverse=True
        )[:top_n],
        'projetos': sorted(
            [{'nome': d['nome'], 'val': d.get('num_projetos', 0)} for d in dataset],
            key=lambda x: x['val'], reverse=True
        )[:top_n],
        'orientacoes': sorted(
            [{'nome': d['nome'], 'val': d.get('num_orient_total', 0)} for d in dataset],
            key=lambda x: x['val'], reverse=True
        )[:top_n],
    }
    return rankings


# ============================================================
# MAIN
# ============================================================

def main():
    """Executa a consolidação completa: ler docentes → extrair métricas → salvar dataset."""

    # Carregar lista de docentes
    with open(DOCENTES_FILE, encoding='utf-8') as f:
        docentes = json.load(f)

    print(f"Docentes carregados: {len(docentes)}")
    print(f"Programa: {PROGRAM_NAME}")
    print(f"Output: {OUTPUT_DIR}")
    print()

    # Consolidar
    dataset = []
    for d in docentes:
        jf, data = find_json(d["lattes_id"])
        if data:
            metrics = extract_metrics(data, d)
            metrics["nome_site"] = d["nome"]
            metrics["email"] = d["email"]
            metrics["lattes_url"] = f"http://lattes.cnpq.br/{d['lattes_id']}"
            metrics["arquivo"] = jf.name if jf else ""
            dataset.append(metrics)
            print(
                f"OK  {d['nome'][:35]:35s} | "
                f"{metrics['num_secoes']:2d} sec | "
                f"{metrics['full_text_len']:6d} chars | "
                f"art={metrics['num_artigos']:3d} liv={metrics['num_livros']:2d} cap={metrics['num_capitulos']:2d} | "
                f"{metrics['num_projetos']:3d} proj | "
                f"{metrics['num_orient_total']:3d} orient | "
                f"{metrics['scholar_citacoes']:5d} cit"
            )
        else:
            print(f"ERR {d['nome'][:35]:35s} | NAO ENCONTRADO")

    # Salvar dataset consolidado
    DATASET_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(DATASET_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    print(f"\nDataset salvo: {DATASET_OUTPUT}")
    print(f"Total: {len(dataset)} docentes")

    # Gerar rankings
    rankings = generate_rankings(dataset)
    rankings_path = DATASET_OUTPUT.parent / "ppgcs_rankings.json"
    with open(rankings_path, "w", encoding="utf-8") as f:
        json.dump(rankings, f, ensure_ascii=False, indent=2)
    print(f"Rankings salvos: {rankings_path}")

    # Estatísticas agregadas
    print(f"\n=== ESTATÍSTICAS ===")
    total_artigos = sum(d["num_artigos"] for d in dataset)
    total_livros = sum(d["num_livros"] for d in dataset)
    total_capitulos = sum(d["num_capitulos"] for d in dataset)
    total_projetos = sum(d["num_projetos"] for d in dataset)
    total_orient = sum(d["num_orient_total"] for d in dataset)
    total_bancas = sum(d["num_bancas_total"] for d in dataset)
    total_citacoes = sum(d["scholar_citacoes"] for d in dataset)
    print(f"Total artigos: {total_artigos}")
    print(f"Total livros: {total_livros}")
    print(f"Total capítulos: {total_capitulos}")
    print(f"Total projetos: {total_projetos}")
    print(f"Total orientações: {total_orient}")
    print(f"Total bancas: {total_bancas}")
    print(f"Total citações: {total_citacoes}")
    print(f"Média artigos/docente: {total_artigos/len(dataset):.1f}")
    print(f"Média projetos/docente: {total_projetos/len(dataset):.1f}")
    print(f"Média orientações/docente: {total_orient/len(dataset):.1f}")


if __name__ == "__main__":
    main()
