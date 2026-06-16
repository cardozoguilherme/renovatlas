# -*- coding: utf-8 -*-
"""Orquestra a etapa de CONTRIBUICAO (Ideias 1 e 2). Pressupoe que a reproducao ja foi
executada (run_all.py), pois reaproveita os dados coletados e o MM grid. Cada passo guarda
suas saidas, entao rodar de novo e barato. Ver CONTRIBUICAO.md."""
import subprocess, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")
PY = sys.executable  # usa o mesmo Python que esta executando este script

# Etapas da contribuicao, na ordem: covariaveis -> ML -> complementaridade -> indice -> figuras.
STEPS = [
    ("Covariaveis (elevacao e distancia a costa)", ["covariates.py"]),
    ("Interpolacao por ML vs Kriging (Ideia 2)", ["ml_interpolation.py"]),
    ("Complementaridade temporal vento-sol (Ideia 1)", ["complementarity.py"]),
    ("Indice hibrido IPH (Ideias 1 + 2)", ["hybrid_index.py"]),
    ("Figuras da contribuicao", ["plots_contrib.py"]),
]


def main():
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    for title, args in STEPS:
        print("\n" + "=" * 70 + "\n>>> " + title + "\n" + "=" * 70)
        r = subprocess.run([PY, os.path.join(SRC, args[0])] + args[1:], env=env)
        if r.returncode != 0:                 # se uma etapa falhar, interrompe tudo
            print("STEP FAILED:", title)
            sys.exit(r.returncode)
    print("\nCONTRIBUICAO DONE.")


if __name__ == "__main__":
    main()
