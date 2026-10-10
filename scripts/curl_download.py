#!/usr/bin/env python3
"""Baixa currículos Lattes via curl + 2Captcha (sem browser, sem CDP)."""

import json, os, time, re, subprocess, urllib.parse, urllib.request
from pathlib import Path

OUTPUT_DIR = Path("/home/hermes/lattes_ppgs_ufrgs/output/ppgs")
SITEKEY = "6LeDv6QUAAAAAP_ZK5AXrsNRQjxfbjgZLV5_YHyy"
BASE_URL = "https://buscatextual.cnpq.br"
UA = "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"

with open(os.path.expanduser("~/.hermes/.env")) as f:
    for line in f:
        if line.startswith("TWOCAPTCHA_API_KEY="):
            api_key = line.strip().split("=", 1)[1]
            break

with open("/home/hermes/lattes_ppgs_ufrgs/data/ppgs_docentes.json") as f:
    docentes = json.load(f)

short_ids_map = {
    6: "K4762998A9", 7: "K4710766D8", 8: "K4470985Y0", 9: "K4496868D0",
    10: "K4733993Y2", 11: "K4707306A9", 12: "K4783189H2", 13: "K4767041U6",
    14: "K4707047E8", 15: "K4744498E7", 16: "K4753133U7", 17: "K4701492U1",
    18: "K4773762J8", 19: "K4255478A5", 20: "K4763262Z1", 21: "K4425852J2",
    22: "K4718982Z6", 23: "K4794312U3", 24: "K4764223E1", 25: "K4704480E2",
    26: "K4739083A8", 27: "K4794889J6", 28: "K4782682P1", 29: "K4783524Z5",
    30: "K4423511E8",
}

def download_cv(short_id, numeric_id, nome, idx):
    safe = nome.replace(" ", "-").replace("/", "-")
    out_file = OUTPUT_DIR / f"{idx+1:02d}_{safe}_{numeric_id}.html"
    
    if out_file.exists() and out_file.stat().st_size > 50000:
        return "skip", out_file.stat().st_size
    
    url = f"{BASE_URL}/buscatextual/visualizacv.do?metodo=apresentar&id={short_id}"
    
    # GET para pegar JSESSIONID
    r = subprocess.run([
        'curl', '-s', '-D', '-', '-o', '/tmp/lattes_get.html',
        '-A', UA, url
    ], capture_output=True, text=True, timeout=30)
    
    m = re.search(r'JSESSIONID=([^;]+)', r.stdout)
    if not m:
        return "no_session", 0
    jsessionid = m.group(1)
    
    with open('/tmp/lattes_get.html', 'r', errors='replace') as f:
        get_html = f.read()
    if len(get_html) > 50000:
        out_file.write_text(get_html, encoding='utf-8')
        return "ok_direct", len(get_html)
    
    # Resolver CAPTCHA
    data = urllib.parse.urlencode({
        'key': api_key, 'method': 'userrecaptcha',
        'googlekey': SITEKEY, 'pageurl': url, 'json': 1
    }).encode()
    req = urllib.request.Request('https://2captcha.com/in.php', data=data)
    with urllib.request.urlopen(req, timeout=30) as resp:
        r2 = json.loads(resp.read())
    
    if r2.get('status') != 1:
        return "captcha_submit_fail", 0
    
    captcha_id = r2['request']
    token = None
    for attempt in range(24):
        time.sleep(5)
        fetch_url = f"https://2captcha.com/res.php?key={api_key}&action=get&id={captcha_id}&json=1"
        with urllib.request.urlopen(fetch_url, timeout=15) as resp:
            r3 = json.loads(resp.read())
        if r3.get('status') == 1:
            token = r3['request']
            break
    
    if not token:
        return "captcha_timeout", 0
    
    # POST com token
    post_url = f"{BASE_URL}/buscatextual/visualizacv.do;jsessionid={jsessionid}"
    post_data = (
        f"metodo=apresentar&id={short_id}&tokenCaptchar={token}&nomeCaptchar=V2"
        f"&idiomaExibicao=&tipo=&mostrarNroCitacoesScielo=&mostrarNroCitacoesScopus="
        f"&mostrarNroCitacoesISI=&filtros.paisAtividade=0&filtros.regiaoAtividade=0"
        f"&filtros.ufAtividade=0&filtros.siglaInstAtividade=&filtros.nomeInstAtividade="
        f"&filtros.naturezaAtividade=0&filtros.atividadeAtual=false&filtros.paisFormacao=0"
        f"&filtros.regiaoFormacao=0&filtros.ufFormacao=0&filtros.siglaInstFormacao="
        f"&filtros.nomeInstFormacao=&filtros.naturezaFormacao=0&filtros.formacaoAtual=false"
        f"&filtros.paisProducao=0&filtros.regiaoProducao=0&filtros.ufProducao=0"
        f"&filtros.siglaInstProducao=&filtros.nomeInstProducao=&filtros.naturezaProducao=0"
        f"&filtros.producaoAtual=false&filtros.origemProducao=0&filtros.areaProducao=0"
        f"&filtros.subAreaProducao=0&filtros.especialidadeProducao=0&filtros.idioma="
        f"&filtros.tipoProducao=0&filtros.anoInicioProducao=&filtros.anoFimProducao="
        f"&filtros.areaConhecimento=0"
    )
    
    subprocess.run([
        'curl', '-s', '-o', str(out_file),
        '-A', UA,
        '-H', f'Cookie: JSESSIONID={jsessionid}',
        '-H', 'Content-Type: application/x-www-form-urlencoded',
        '-H', f'Referer: {url}',
        '-d', post_data,
        post_url
    ], capture_output=True, text=True, timeout=60)
    
    if out_file.exists() and out_file.stat().st_size > 50000:
        return "ok", out_file.stat().st_size
    else:
        if out_file.exists():
            content = out_file.read_text(errors='replace')[:200]
            out_file.unlink()
            return f"fail:{content[:60]}", 0
        return "fail_empty", 0

# Processar
results = []
for k in sorted(short_ids_map.keys()):
    idx = k - 1
    d = docentes[idx]
    nome = d["nome"]
    numeric_id = d["lattes_id"]
    sid = short_ids_map[k]
    
    status, size = download_cv(sid, numeric_id, nome, idx)
    print(f"[{k:02d}] {nome[:35]:35s} → {status} ({size} bytes)", flush=True)
    results.append({"idx": k, "nome": nome, "status": status, "size": size})
    time.sleep(2)

# Salvar relatório
with open(OUTPUT_DIR / "download_report.json", "w") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

ok = sum(1 for r in results if r["status"] in ("ok", "ok_direct", "skip"))
print(f"\nRESUMO: {ok} OK de {len(results)} processados", flush=True)