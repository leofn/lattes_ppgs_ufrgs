#!/usr/bin/env python3
"""Baixa currículos Lattes via browser (CDP) + 2Captcha.
Para cada docente: navega para a URL, resolve reCAPTCHA v2, submete form, salva HTML."""

import json
import os
import time
import urllib.request
import urllib.parse
from pathlib import Path

DOCENTES_FILE = Path(__file__).parent.parent / "data" / "ppgs_docentes.json"
OUTPUT_DIR = Path(__file__).parent.parent / "output" / "ppgs"
SITEKEY = "6LeDv6QUAAAAAP_ZK5AXrsNRQjxfbjgZLV5_YHyy"

def load_api_key():
    env_path = os.path.expanduser("~/.hermes/.env")
    with open(env_path) as f:
        for line in f:
            if line.startswith("TWOCAPTCHA_API_KEY="):
                return line.strip().split("=", 1)[1]
    raise Exception("TWOCAPTCHA_API_KEY não encontrada")

def solve_captcha(api_key, page_url, max_wait=120):
    """Resolve reCAPTCHA v2 via 2Captcha."""
    data = urllib.parse.urlencode({
        'key': api_key, 'method': 'userrecaptcha',
        'googlekey': SITEKEY, 'pageurl': page_url, 'json': 1
    }).encode()
    req = urllib.request.Request('https://2captcha.com/in.php', data=data)
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read())
    if result.get('status') != 1:
        raise Exception(f"2Captcha submit failed: {result}")
    captcha_id = result['request']
    
    for attempt in range(max_wait // 5):
        time.sleep(5)
        fetch_url = f"https://2captcha.com/res.php?key={api_key}&action=get&id={captcha_id}&json=1"
        with urllib.request.urlopen(fetch_url, timeout=15) as resp:
            r = json.loads(resp.read())
        if r.get('status') == 1:
            return r['request']
        if 'CAPCHA_NOT_READY' not in str(r.get('request', '')):
            raise Exception(f"2Captcha error: {r}")
    raise Exception("2Captcha timeout")

# Este script é executado dentro do browser_exec como código Python.
# Ele usa as funções js(), goto_url(), etc. disponíveis no contexto.
def download_all():
    api_key = load_api_key()
    
    with open(DOCENTES_FILE) as f:
        docentes = json.load(f)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    total = len(docentes)
    
    for i, docente in enumerate(docentes, 1):
        nome = docente["nome"]
        lattes_id = docente["lattes_id"]
        safe_name = nome.replace(" ", "-").replace("/", "-")
        out_file = OUTPUT_DIR / f"{i:02d}_{safe_name}_{lattes_id}.html"
        
        if out_file.exists() and out_file.stat().st_size > 50000:
            print(f"[{i}/{total}] SKIP {nome} (já baixado: {out_file.stat().st_size} bytes)")
            results.append({"nome": nome, "status": "skip", "size": out_file.stat().st_size})
            continue
        
        print(f"\n[{i}/{total}] {nome} — ID: {lattes_id}")
        
        # Navegar para a página
        url = f"https://buscatextual.cnpq.br/buscatextual/visualizacv.do?metodo=apresentar&id={lattes_id}"
        goto_url(url)
        time.sleep(4)
        
        # Verificar se já carregou sem CAPTCHA
        html_len = js("document.documentElement.outerHTML.length")
        if html_len > 50000:
            html = js("document.documentElement.outerHTML")
            out_file.write_text(html, encoding='utf-8')
            print(f"  ✓ OK sem CAPTCHA: {len(html)} bytes")
            results.append({"nome": nome, "status": "ok", "size": len(html)})
            continue
        
        # Verificar se é página de CAPTCHA
        page_text = js("document.body.innerText")
        if "Código de segurança" not in page_text and "captcha" not in page_text.lower():
            print(f"  ? Página inesperada: {page_text[:100]}")
            results.append({"nome": nome, "status": "unknown", "text": page_text[:100]})
            continue
        
        # Resolver CAPTCHA
        try:
            current_url = js("window.location.href")
            token = solve_captcha(api_key, current_url)
            print(f"  CAPTCHA resolvido: {token[:20]}...")
        except Exception as e:
            print(f"  ✗ Erro CAPTCHA: {e}")
            results.append({"nome": nome, "status": "captcha_error", "error": str(e)})
            continue
        
        # Setar token e submeter
        js(f"""
        (() => {{
            var tokenField = document.querySelector('#tokenCaptchar');
            if (tokenField) tokenField.value = '{token}';
            var grr = document.querySelector('textarea[name="g-recaptcha-response"]');
            if (grr) grr.value = '{token}';
            if (typeof visualizarCurriculo === 'function') {{
                visualizarCurriculo();
            }} else {{
                document.querySelector('form').submit();
            }}
        }})()
        """)
        time.sleep(12)
        
        # Verificar resultado
        new_html_len = js("document.documentElement.outerHTML.length")
        new_text = js("document.body.innerText")
        
        if new_html_len > 50000:
            html = js("document.documentElement.outerHTML")
            out_file.write_text(html, encoding='utf-8')
            print(f"  ✓ OK: {len(html)} bytes")
            results.append({"nome": nome, "status": "ok", "size": len(html)})
        elif "500" in new_text or "não permitida" in new_text:
            print(f"  ✗ Erro servidor: {new_text[:100]}")
            results.append({"nome": nome, "status": "server_error", "error": new_text[:100]})
        elif "Código de segurança" in new_text:
            print(f"  ✗ CAPTCHA rejeitado")
            results.append({"nome": nome, "status": "captcha_rejected"})
        else:
            print(f"  ? Resposta inesperada: {new_text[:100]}")
            results.append({"nome": nome, "status": "unknown", "text": new_text[:100]})
        
        # Pausa entre downloads
        time.sleep(2)
    
    # Salvar relatório
    report = OUTPUT_DIR / "download_report.json"
    with open(report, "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    ok = sum(1 for r in results if r["status"] == "ok")
    skip = sum(1 for r in results if r["status"] == "skip")
    err = sum(1 for r in results if r["status"] not in ("ok", "skip"))
    print(f"\n{'='*60}")
    print(f"RESUMO: {ok} OK, {skip} skip, {err} erros de {total} total")
    return results

# Executar
download_all()