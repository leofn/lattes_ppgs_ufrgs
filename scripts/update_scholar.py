#!/usr/bin/env python3
"""
Atualiza o dataset PPGCS com dados do Google Scholar.
Lê o dataset consolidado, busca cada docente no Google Scholar,
e atualiza citações, h-index e i10-index.
"""
import json
import sys
import time
import random
from pathlib import Path

# Adicionar path do ppgcs para importar o scraper
sys.path.insert(0, '/home/hermes/ppgcs')
from google_scholar_scraper import GoogleScholarScholar

DATASET_PATH = Path('/home/hermes/scriptLattes/output/ppgcs/ppgcs_dataset.json')
OUTPUT_PATH = Path('/home/hermes/lattes_ppgcs/data/processed/ppgcs_dataset.json')
CACHE_DIR = '/home/hermes/ppgcs/scholar_cache'

# Carregar dataset
with open(DATASET_PATH) as f:
    dataset = json.load(f)

print(f"Dataset carregado: {len(dataset)} docentes")

# Inicializar scraper
scraper = GoogleScholarScholar(cache_dir=CACHE_DIR, delay_range=(3, 6))

# Buscar cada docente no Google Scholar
enhanced = []
for i, d in enumerate(dataset, 1):
    nome = d.get("nome", d.get("nome_site", ""))
    print(f"\n[{i}/{len(dataset)}] {nome}")
    
    # Dados já existentes do Lattes
    scholar_cit = d.get("scholar_citacoes", 0)
    scholar_trab = d.get("scholar_trabalhos", 0)
    
    try:
        # Buscar no Google Scholar
        profile = scraper.search_profile(nome, affiliation="UFBA")
        if profile:
            d["scholar_citacoes"] = profile.get("total_citations", 0)
            d["scholar_trabalhos"] = profile.get("total_publications", 0)
            d["scholar_h_index"] = profile.get("h_index", 0)
            d["scholar_i10_index"] = profile.get("i10_index", 0)
            d["scholar_url"] = profile.get("profile_url", "")
            print(f"  ✅ Citações: {d['scholar_citacoes']} | h-index: {d['scholar_h_index']} | i10: {d['scholar_i10_index']}")
        else:
            # Manter valores do Lattes se não encontrou no Scholar
            d["scholar_h_index"] = 0
            d["scholar_i10_index"] = 0
            d["scholar_url"] = ""
            print(f"  ⚠️  Perfil não encontrado no Google Scholar (mantendo Lattes: {scholar_cit} cit)")
    except Exception as e:
        d["scholar_h_index"] = 0
        d["scholar_i10_index"] = 0
        d["scholar_url"] = ""
        print(f"  ❌ Erro: {e}")
    
    enhanced.append(d)

# Salvar dataset atualizado
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(enhanced, f, ensure_ascii=False, indent=2)

print(f"\n{'='*60}")
print(f"Dataset atualizado salvo: {OUTPUT_PATH}")
print(f"Total: {len(enhanced)} docentes")

# Estatísticas
total_cit = sum(d.get("scholar_citacoes", 0) for d in enhanced)
total_h = sum(d.get("scholar_h_index", 0) for d in enhanced)
profiles_found = sum(1 for d in enhanced if d.get("scholar_url"))
print(f"Total citações: {total_cit}")
print(f"Perfis encontrados: {profiles_found}/{len(enhanced)}")