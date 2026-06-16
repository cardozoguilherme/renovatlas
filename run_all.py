# -*- coding: utf-8 -*-
"""Orquestra o pipeline completo de REPRODUCAO. Roda cada etapa na ordem certa, chamando os
scripts de src/. Cada etapa guarda suas saidas e reaproveita o que ja foi baixado (CSVs da
NASA por ponto, zips anuais do INMET, malha do IBGE), entao rodar de novo fica rapido."""
import subprocess, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")
PY = sys.executable  # usa o mesmo Python que esta executando este script

# Lista de etapas, na ordem: (titulo a mostrar, [script, argumentos...]).
STEPS = [
    ("Download IBGE boundaries", ["data_ibge.py"]),
    ("Collect NASA POWER (0.5deg grid)", ["data_nasa.py"]),
    ("Collect INMET stations (2003-2022)", ["data_inmet.py"]),
    ("Preprocess (historical means)", ["preprocess.py", "all"]),
    ("Table 2 — IDW vs Kriging (LOOCV)", ["interpolation.py"]),
    ("Build MM grid (kriging)", ["mm_grid.py", "all"]),
    ("IP-PB index, groups & rankings", ["ip_pb.py", "all"]),
    ("Figures", ["plots.py", "all"]),
]


def main():
    # PYTHONIOENCODING=utf-8 garante que os acentos saiam corretos no terminal.
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    for title, args in STEPS:
        print("\n" + "=" * 70 + "\n>>> " + title + "\n" + "=" * 70)
        r = subprocess.run([PY, os.path.join(SRC, args[0])] + args[1:], env=env)
        if r.returncode != 0:                 # se uma etapa falhar, interrompe tudo
            print("STEP FAILED:", title)
            sys.exit(r.returncode)
    print("\nALL DONE.")


if __name__ == "__main__":
    main()
