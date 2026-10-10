#!/usr/bin/env python3
"""Baixa currículos Lattes via requests (sem Selenium).
Fluxo: GET página → extrair JSESSIONID → resolver CAPTCHA via 2Captcha → POST com token → salvar HTML/JSON.

Uso:
    python3 download_lattes_requests.py <short_id> [--output dir]
    python3 download_lattes_requests.py K4445507Z7 --output /home/hermes/scriptLattes/output/ufba
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.request
import urllib.parse
from pathlib import Path

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("ERRO: bs4 não instalado. Use: pip install beautifulsoup4")
    sys.exit(1)

# ─── Config ───
SITE_KEY = '6LeDv6QUAAAAAP_ZK5AXrsNRQjxfbjgZLV5_YHyy'
BASE_URL = "http://buscatextual.cnpq.br"
VISUALIZACV_URL = f"{BASE_URL}/buscatextual/visualizacv.do"
UA = "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"


def load_api_key():
    env_path = os.path.expanduser("~/.hermes/.env")
    for line in open(env_path):
        line = line.strip()
        if line.startswith("TWOCAPTCHA_API_KEY="):
            return line.split("=", 1)[1]
    raise Exception("TWOCAPTCHA_API_KEY não encontrada em ~/.hermes/.env")


def solve_captcha(api_key, page_url, max_wait=120):
    """Resolve reCAPTCHA v2 via 2Captcha."""
    print("  [2Captcha] Enviando CAPTCHA para resolução...")
    data = urllib.parse.urlencode({
        'key': api_key,
        'method': 'userrecaptcha',
        'googlekey': SITE_KEY,
        'pageurl': page_url,
        'json': 1
    }).encode()
    req = urllib.request.Request('https://2captcha.com/in.php', data=data)
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read())
    if result.get('status') != 1:
        raise Exception(f"2Captcha submit failed: {result}")
    captcha_id = result['request']
    print(f"  [2Captcha] ID: {captcha_id}, aguardando...")

    start = time.time()
    while time.time() - start < max_wait:
        time.sleep(5)
        url = f'https://2captcha.com/res.php?key={api_key}&action=get&id={captcha_id}&json=1'
        with urllib.request.urlopen(url, timeout=30) as resp:
            result = json.loads(resp.read())
        if result.get('status') == 1:
            elapsed = int(time.time() - start)
            print(f"  [2Captcha] Resolvido em {elapsed}s")
            return result['request']
        elif 'NOT_READY' in str(result.get('request', '')):
            continue
        else:
            raise Exception(f"2Captcha error: {result}")
    raise Exception("2Captcha timeout")


def download_cv(short_id, output_dir):
    """Baixa um CV Lattes via requests."""
    api_key = load_api_key()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"Baixando: {short_id}")
    print(f"{'='*60}")

    # Step 1: GET the page to get session cookie
    url = f"{VISUALIZACV_URL}?metodo=apresentar&id={short_id}"
    print(f"  GET: {url}")
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        html = resp.read().decode('latin-1')
        cookie = resp.headers.get('Set-Cookie', '')
        # Extract JSESSIONID
        jsession_match = re.search(r'JSESSIONID=([^;]+)', cookie)
        if not jsession_match:
            print("  ERRO: Sem JSESSIONID")
            return None
        jsessionid = jsession_match.group(1)

    print(f"  JSESSIONID: {jsessionid[:20]}...")
    print(f"  HTML length: {len(html)}")

    # Check if CV loaded directly (no captcha)
    if 'nome' in html and len(html) > 50000:
        print("  CV carregado sem CAPTCHA!")
        return parse_and_save(html, short_id, output_dir)

    # Step 2: Resolve CAPTCHA
    print("  CAPTCHA detectado, resolvendo...")
    token = solve_captcha(api_key, url)

    # Step 3: POST form with token
    post_url = f"{VISUALIZACV_URL};jsessionid={jsessionid}"
    post_data = urllib.parse.urlencode({
        'metodo': 'apresentar',
        'id': short_id,
        'tokenCaptchar': token,
        'nomeCaptchar': 'V2',
        'idiomaExibicao': '',
        'tipo': '',
        'mostrarNroCitacoesScielo': '',
        'mostrarNroCitacoesScopus': '',
        'mostrarNroCitacoesISI': '',
        'filtros.paisAtividade': '0',
        'filtros.regiaoAtividade': '0',
        'filtros.ufAtividade': '0',
        'filtros.siglaInstAtividade': '',
        'filtros.nomeInstAtividade': '',
        'filtros.naturezaAtividade': '0',
        'filtros.atividadeAtual': 'false',
        'filtros.paisFormacao': '0',
        'filtros.regiaoFormacao': '0',
        'filtros.ufFormacao': '0',
        'filtros.siglaInstFormacao': '',
        'filtros.nomeInstFormacao': '',
        'filtros.naturezaFormacao': '0',
        'filtros.formacaoAtual': 'false',
        'filtros.paisProducao': '0',
        'filtros.regiaoProducao': '0',
        'filtros.ufProducao': '0',
        'filtros.siglaInstProducao': '',
        'filtros.nomeInstProducao': '',
        'filtros.naturezaProducao': '0',
        'filtros.producaoAtual': 'false',
        'filtros.origemProducao': '0',
        'filtros.areaProducao': '0',
        'filtros.subAreaProducao': '0',
        'filtros.especialidadeProducao': '0',
        'filtros.idioma': '',
        'filtros.tipoProducao': '0',
        'filtros.anoInicioProducao': '',
        'filtros.anoFimProducao': '',
        'filtros.areaConhecimento': '0',
    }).encode()

    req = urllib.request.Request(post_url, data=post_data, headers={
        'User-Agent': UA,
        'Cookie': f'JSESSIONID={jsessionid}',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': url,
    })

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            cv_html = resp.read().decode('latin-1')
    except Exception as e:
        print(f"  ERRO no POST: {e}")
        return None

    print(f"  CV HTML length: {len(cv_html)}")

    if len(cv_html) < 50000:
        # Check if it's still the captcha page
        if 'captcha' in cv_html.lower() or 'segurança' in cv_html.lower():
            print("  ERRO: CAPTCHA não resolvido, página retornou ao captcha")
            return None
        print(f"  AVISO: HTML pequeno ({len(cv_html)} chars), pode ser incompleto")

    return parse_and_save(cv_html, short_id, output_dir)


def parse_and_save(html, short_id, output_dir):
    """Parse HTML and save as JSON + HTML."""
    soup = BeautifulSoup(html, 'html.parser')
    result = {}

    # Nome
    nome_el = soup.find('h2', class_='nome')
    if nome_el:
        result['nome'] = nome_el.get_text(strip=True)

    # ID Lattes
    all_text = soup.get_text(separator='\n', strip=True)
    id_match = re.search(r'ID Lattes:\s*(\w+)', all_text)
    if id_match:
        result['id_lattes'] = id_match.group(1)

    atual_match = re.search(r'Última atualização.*?(\d{2}/\d{2}/\d{4})', all_text)
    if atual_match:
        result['ultima_atualizacao'] = atual_match.group(1)

    # Resumo
    title_wrapper = soup.find('div', class_='title-wrapper')
    if title_wrapper:
        result['resumo'] = title_wrapper.get_text(strip=True)

    # Sections
    sections = []
    for h1 in soup.find_all('h1'):
        section_name = h1.get_text(strip=True)
        if section_name:
            sections.append(section_name)
    result['_sections_found'] = sections

    # Full text
    result['_full_text'] = all_text[:80000]

    # IDs
    result['lattes_id'] = short_id
    result['short_id'] = short_id
    result['downloaded_at'] = time.strftime('%Y-%m-%dT%H:%M:%S')

    # Save HTML
    html_path = output_dir / f"{short_id}.html"
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)

    # Save JSON
    json_path = output_dir / f"{short_id}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"  ✅ Salvo: {result.get('nome', '?')} ({len(sections)} seções, {len(all_text)} chars)")
    print(f"     HTML: {html_path}")
    print(f"     JSON: {json_path}")

    return json_path


def main():
    parser = argparse.ArgumentParser(description='Download Lattes CV via requests')
    parser.add_argument('short_id', help='Lattes short ID (K...)')
    parser.add_argument('--output', default='/home/hermes/scriptLattes/output/ufba',
                       help='Output directory')
    args = parser.parse_args()

    result = download_cv(args.short_id, args.output)
    if result:
        print(f"\nSUCESSO: {result}")
    else:
        print(f"\nFALHA: {args.short_id}")
        sys.exit(1)


if __name__ == '__main__':
    main()