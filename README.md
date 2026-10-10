# Currículos Lattes — PPGS/UFRGS

Análise dos currículos Lattes dos **docentes permanentes** do Programa de Pós-Graduação em Sociologia da Universidade Federal do Rio Grande do Sul (UFRGS).

## 📊 Visão Geral

| Métrica | Valor |
|---|---|
| **Docentes permanentes** | 30 |
| **Currículos baixados** | 30/30 (100%) |
| **Projetos de pesquisa** | 1.284 |
| **Orientações** | 446 |
| **Bancas** | 188 |
| **Artigos** | 153 |
| **Data da coleta** | 09/10/2026 |

## 🌐 Página

A página interativa está disponível em:

**[leofn.com/lattes_ppgs_ufrgs](https://leofn.github.io/lattes_ppgs_ufrgs/)**

### Funcionalidades

- **Cards individuais** com nome, formação, áreas, resumo, link Lattes
- **Rankings** por projetos, orientações e citações
- **Busca** por nome, área ou tema
- **Ordenação** por nome, projetos, citações ou orientações
- **Estatísticas agregadas** do programa
- **Gráficos** de produção bibliográfica ao longo do tempo

## 📁 Estrutura

```
lattes_ppgs_ufrgs/
├── docs/                    # GitHub Pages (dashboard interativo)
│   └── index.html
├── data/
│   ├── ppgs_docentes.json   # Lista de 30 docentes
│   └── processed/           # Dataset consolidado + rankings
├── output/ppgs/             # HTMLs + JSONs dos currículos
├── scripts/
│   ├── curl_download.py     # Download via curl + 2Captcha
│   ├── consolidate_ppgs.py  # Extração de métricas
│   └── generate_site.py     # Gerador do dashboard
└── README.md
```

## Licença

Dados públicos (Plataforma Lattes/CNPq). Compilado pelo LABHDUFBA para fins de pesquisa.
