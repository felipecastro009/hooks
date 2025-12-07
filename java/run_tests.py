#!/usr/bin/env python3
"""
run_tests.py

Detecta se o projeto é Maven ou Gradle e executa os testes (por padrão `test`).
Funciona em Linux, macOS e Windows.

Exemplos:
  python run_tests.py
  python run_tests.py --task integrationTest
  python run_tests.py --cwd /path/to/repo
  python run_tests.py --dry-run
"""
from __future__ import annotations
import os
import sys
import shutil
import subprocess
import argparse
from typing import List, Optional

MAVEN_MARKERS = ["pom.xml"]
GRADLE_MARKERS = ["build.gradle", "build.gradle.kts"]

MAVEN_WRAPPERS = ["mvnw", "mvnw.cmd", "mvn"]
GRADLE_WRAPPERS = ["gradlew", "gradlew.bat", "gradle", "gradle.bat"]

def find_project_root_with(markers: List[str], start: Optional[str] = None) -> Optional[str]:
    cur = os.path.abspath(start or os.getcwd())
    while True:
        for m in markers:
            if os.path.exists(os.path.join(cur, m)):
                return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            return None
        cur = parent

def which_in_dir(names: List[str], dirpath: str) -> Optional[str]:
    # procura no repo (dirpath) primeiro
    for name in names:
        candidate = os.path.join(dirpath, name)
        if os.path.exists(candidate):
            # no Windows o .bat/.cmd pode não ter bit executável, mas é invocável
            if os.access(candidate, os.X_OK) or candidate.lower().endswith(('.bat', '.cmd')):
                return candidate
    # fallback para PATH
    for name in names:
        exe = shutil.which(name)
        if exe:
            return exe
    return None

def run_cmd(cmd: List[str], cwd: str) -> int:
    print("Executando:", " ".join(cmd))
    try:
        # herdamos stdout/stderr para que o usuário veja o output dos testes
        proc = subprocess.run(cmd, cwd=cwd)
        return proc.returncode
    except FileNotFoundError:
        print(f"Comando não encontrado: {cmd[0]}", file=sys.stderr)
        return 127
    except KeyboardInterrupt:
        print("Interrompido pelo usuário.", file=sys.stderr)
        return 130
    except Exception as e:
        print("Erro ao executar comando:", e, file=sys.stderr)
        return 1

def detect_and_run_tests(start_dir: Optional[str], task: str, dry_run: bool = False) -> int:
    # Maven primeiro
    mroot = find_project_root_with(MAVEN_MARKERS, start=start_dir)
    if mroot:
        print("Projeto Maven detectado em:", mroot)
        mvn = which_in_dir(MAVEN_WRAPPERS, mroot)
        if not mvn:
            print("Maven (mvn/mvnw) não encontrado. Abortando.", file=sys.stderr)
            return 127
        # comando: mvn test  (ou outro 'task' passado)
        cmd = [mvn, task]
        if dry_run:
            print("[dry-run] Comando:", " ".join(cmd), "cwd=", mroot)
            return 0
        return run_cmd(cmd, cwd=mroot)

    # Gradle
    groot = find_project_root_with(GRADLE_MARKERS, start=start_dir)
    if groot:
        print("Projeto Gradle detectado em:", groot)
        gradle = which_in_dir(GRADLE_WRAPPERS, groot)
        if not gradle:
            print("Gradle (gradle/gradlew) não encontrado. Abortando.", file=sys.stderr)
            return 127
        # gradle task padrão: test (ou task informada)
        cmd = [gradle, task]
        if dry_run:
            print("[dry-run] Comando:", " ".join(cmd), "cwd=", groot)
            return 0
        return run_cmd(cmd, cwd=groot)

    print("Nenhum projeto Maven/Gradle encontrado a partir de", start_dir or os.getcwd())
    return 0

def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Detecta Maven/Gradle e roda testes.")
    p.add_argument("--task", "-t", default="test",
                   help="Nome da goal/task a executar (padrão: test). Para Maven informe 'test' ou outro goal; para Gradle a task (ex: spotlessApply, integrationTest).")
    p.add_argument("--cwd", "-C", default=None, help="Diretório onde começar a busca pelo projeto (padrão: cwd).")
    p.add_argument("--dry-run", action="store_true", help="Imprime o comando que seria executado sem rodar.")
    return p.parse_args(argv)

def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    return detect_and_run_tests(start_dir=args.cwd, task=args.task, dry_run=args.dry_run)

if __name__ == "__main__":
    rc = main()
    sys.exit(rc)