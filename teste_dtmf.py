# -*- coding: utf-8 -*-
"""
Teste automatico do sistema DTMF: para cada uma das 16 teclas, gera o tom com
o encoder, adiciona ruido, passa pelo decoder e confere se a tecla identificada
e a mesma que foi transmitida. Nao usa microfone nem alto-falante.

    python teste_dtmf.py
"""

import matplotlib
matplotlib.use("Agg")           # sem janela grafica

import numpy as np

from dtmf import DTMF, FS, salvar_wav, ler_wav
from encode import gerar_tom
from decode import simular, achar_picos, identificar_tecla
from suaBibSignal import signalMeu


def decodificar(dados, fs=FS):
    xf, yf = signalMeu().calcFFT(dados, fs)
    picos = achar_picos(xf, yf, n=5)
    res = identificar_tecla(picos)
    return (res[0] if res else None), picos


def main():
    print("=" * 62)
    print("TESTE 1 - sinal limpo (encoder -> decoder)")
    print("=" * 62)
    erros = 0
    for tecla in DTMF:
        _, tom, _, _ = gerar_tom(tecla, 1.0)
        achada, _ = decodificar(tom / 2.0)
        ok = achada == tecla
        erros += not ok
        print("  tecla {:>2} -> {:>4}   {}".format(tecla, str(achada), "OK" if ok else "FALHOU"))

    print()
    print("=" * 62)
    print("TESTE 2 - sinal com ruido branco + 3 tons parasitas")
    print("=" * 62)
    for tecla in DTMF:
        dados = simular(tecla, 1.0, ruido=0.25, semente=hash(tecla) % 1000)
        achada, picos = decodificar(dados)
        ok = achada == tecla
        erros += not ok
        print("  tecla {:>2} -> {:>4}   {}   picos: {}".format(
            tecla, str(achada), "OK" if ok else "FALHOU",
            ", ".join("{:.0f}".format(f) for f, _ in picos)))

    print()
    print("=" * 62)
    print("TESTE 3 - ida e volta pelo arquivo WAV (digitalizacao 16 bits)")
    print("=" * 62)
    for tecla in ["5", "9", "*", "D"]:
        nome = "teste_{}.wav".format({"*": "estrela", "#": "cerquilha"}.get(tecla, tecla))
        _, tom, _, _ = gerar_tom(tecla, 1.0)
        salvar_wav(nome, tom / 2.0)
        dados, fs = ler_wav(nome)
        achada, _ = decodificar(dados, fs)
        ok = achada == tecla
        erros += not ok
        print("  tecla {:>2} -> {:>4}   {}   ({})".format(
            tecla, str(achada), "OK" if ok else "FALHOU", nome))

    print()
    print("=" * 62)
    print("TESTE 4 - limite de ruido (tecla 5, ruido crescente)")
    print("=" * 62)
    for r in (0.1, 0.5, 1.0, 2.0, 4.0):
        dados = simular("5", 1.0, ruido=r, semente=1)
        achada, _ = decodificar(dados)
        print("  ruido sigma = {:.1f} -> {:>4}   {}".format(
            r, str(achada), "OK" if achada == "5" else "falhou"))

    print()
    if erros == 0:
        print("RESULTADO: todos os testes passaram.")
    else:
        print("RESULTADO: {} falha(s).".format(erros))
    return 0 if erros == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
