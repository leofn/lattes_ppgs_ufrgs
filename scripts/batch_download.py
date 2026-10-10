#!/usr/bin/env python3
"""Download em lote dos currículos Lattes dos docentes do PPGS/UFRGS."""

import json
import os
import sys
import time
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR.parent / "output" / "ppgs"
DOWNLOADER = str(SCRIPT_DIR / "download_lattes_requests.py")
DOCENTES_FILE = SCRIPT_DIR.parent / "data" / "ppgs_docentes.json"

# Load env
env_path = os.path.expanduser("~/.hermes/.env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

def main():
    with open(DOCENTES_FILE) as f:
        docentes = json.load(f)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    results = []
    total = len(docentes)
    
    for i, docente in enumerate(docentes, 1):
        nome = docente["nome"]
        lattes_id = docente["lattes_id"]
        
        # Verificar se já existe
        existing = list(OUTPUT_DIR.glob(f"*{lattes_id}*"))
        if existing:
            print(f"[{i}/{total}] SKIP {nome} (já existe)")
            results.append({"nome": nome, "status": "skip", "file": str(existing[0])})
            continue
        
        print(f"\n{'='*60}")
        print(f"[{i}/{total}] {nome} — ID: {lattes_id}")
        
        try:
            cmd = [sys.executable, DOWNLOADER, lattes_id, "--output", str(OUTPUT_DIR)]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=300, env=os.environ)
            
            if r.returncode == 0:
                files = list(OUTPUT_DIR.glob(f"*{lattes_id}*"))
                fname = files[0].name if files else "unknown"
                print(f"  ✓ OK: {fname}")
                results.append({"nome": nome, "status": "ok", "file": fname})
            else:
                print(f"  ✗ ERRO: {r.stderr[:200]}")
                results.append({"nome": nome, "status": "error", "error": r.stderr[:200]})
        except subprocess.TimeoutExpired:
            print(f"  ✗ TIMEOUT")
            results.append({"nome": nome, "status": "timeout"})
        except Exception as e:
            print(f"  ✗ EXCEPTION: {e}")
            results.append({"nome": nome, "status": "error", "error": str(e)})
        
        # Pausa entre downloads
        if i < total:
            time.sleep(3)
    
    # Salvar relatório
    report_path = OUTPUT_DIR / "download_report.json"
    with open(report_path, "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    ok = sum(1 for r in results if r["status"] == "ok")
    skip = sum(1 for r in results if r["status"] == "skip")
    err = sum(1 for r in results if r["status"] in ("error", "timeout"))
    print(f"\n{'='*60}")
    print(f"RESUMO: {ok} OK, {skip} skip, {err} erros de {total} total")

if __name__ == "__main__":
    main()
