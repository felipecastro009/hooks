#!/usr/bin/env python3
"""
spotless_apply.py

Detecta se o projeto é Maven ou Gradle e executa o comando adequado para aplicar Spotless.

Coloque este arquivo no repositório e registre-o como um hook local no .pre-commit-config.yaml.

Funciona em Linux, macOS e Windows.
"""
import os
import sys
import shutil
import subprocess

# nomes de build files que indicam tipo de projeto
MAVEN_MARKERS = ["pom.xml"]
GRADLE_MARKERS = ["build.gradle", "build.gradle.kts"]

# wrappers / executáveis preferidos (ordem de tentativa)
MAVEN_WRAPPERS = ["mvnw", "mvnw.cmd", "mvn"]   # mvnw (unix), mvnw.cmd (win), fallback mvn
GRADLE_WRAPPERS = ["gradlew", "gradlew.bat", "gradle", "gradle.bat"]

def find_project_root_with(markers):
    """
    Sobe a partir do cwd até a raiz do filesystem procurando por qualquer arquivo em markers.
    Retorna o caminho onde encontrou ou None.
    """
    cur = os.path.abspath(os.getcwd())
    while True:
        for m in markers:
            if os.path.exists(os.path.join(cur, m)):
                return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            return None
        cur = parent

def which_in_dir(names, dirpath):
    """
    Verifica, na ordem, se existe um executável (ou wrapper) em dirpath ou no PATH.
    Retorna o comando (nome absoluto se encontrado em dirpath, senão o nome se estiver no PATH), ou None.
    """
    for name in names:
        # se tiver no dirpath (por exemplo ./gradlew)
        candidate = os.path.join(dirpath, name)
        if os.path.exists(candidate) and os.access(candidate, os.X_OK):
            return candidate
    # se não achou wrapper no repo, tenta no PATH
    for name in names:
        exe = shutil.which(name)
        if exe:
            return exe
    return None

def run_cmd(cmd, cwd):
    print("Executando:", " ".join(cmd))
    try:
        proc = subprocess.run(cmd, cwd=cwd)
        return proc.returncode
    except FileNotFoundError:
        print("Comando não encontrado:", cmd[0], file=sys.stderr)
        return 127
    except Exception as e:
        print("Erro ao executar comando:", e, file=sys.stderr)
        return 1

def main():
    # tenta detectar Maven
    mroot = find_project_root_with(MAVEN_MARKERS)
    if mroot:
        print("Projeto Maven detectado em:", mroot)
        mvn = which_in_dir(MAVEN_WRAPPERS, mroot)
        if not mvn:
            print("Maven (mvn/mvnw) não encontrado. Abortando.", file=sys.stderr)
            return 127
        # se usar wrapper mvnw no Unix, certifique-se de chamar diretamente; no Windows mvnw.cmd
        cmd = [mvn, "spotless:apply"]
        return run_cmd(cmd, cwd=mroot)

    # tenta detectar Gradle
    groot = find_project_root_with(GRADLE_MARKERS)
    if groot:
        print("Projeto Gradle detectado em:", groot)
        gradle = which_in_dir(GRADLE_WRAPPERS, groot)
        if not gradle:
            print("Gradle (gradle/gradlew) não encontrado. Abortando.", file=sys.stderr)
            return 127
        # gradle task é 'spotlessApply'
        cmd = [gradle, "spotlessApply"]
        return run_cmd(cmd, cwd=groot)

    print("Nenhum projeto Maven/Gradle encontrado. Nenhuma ação necessária.")
    # não falha: permite commits em projetos que não usam java/spotless
    return 0

if __name__ == "__main__":
    rc = main()
    sys.exit(rc)