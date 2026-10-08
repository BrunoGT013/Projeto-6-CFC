# -*- coding: utf-8 -*-
"""
Projeto 6 - Camada Fisica da Computacao
DECODER DTMF: grava o audio pelo microfone (ou le um WAV), calcula a FFT,
acha os picos de frequencia e descobre qual tecla foi pressionada.

Uso:
    python decode.py                  # grava 3 s do microfone
    python decode.py --dur 5          # grava 5 s
    python decode.py --wav tom_5.wav  # decodifica um arquivo (sem microfone)
    python decode.py --sim 7          # simula a transmissao da tecla 7 com ruido
"""

import argparse
import sys
import time

import numpy as np
import matplotlib.pyplot as plt

from suaBibSignal import signalMeu
from dtmf import DTMF, FS, LINHAS, COLUNAS, tecla_de, tabela_str, ler_wav

try:
    import peakutils
    TEM_PEAKUTILS = True
except ImportError:
    TEM_PEAKUTILS = False


def todB(s):
    """Transforma intensidade acustica em dB."""
    return 10 * np.log10(s)


# ---------------------------------------------------------------- aquisicao
def gravar(duracao, fs=FS, canais=1, espera=3):
    """Grava audio do microfone e devolve uma lista unica de amostras."""
    import sounddevice as sd

    sd.default.samplerate = fs
    sd.default.channels = canais

    numAmostras = int(duracao * fs)

    for n in range(espera, 0, -1):
        print("A captacao comecara em {} segundo(s)...".format(n))
        time.sleep(1)

    print("GRAVACAO INICIALIZADA ({:.1f} s)".format(duracao))
    audio = sd.rec(int(numAmostras), fs, channels=canais)
    sd.wait()
    print("...     FIM")

    # a gravacao volta como matriz (numAmostras x canais): extrai uma lista so
    dados = np.asarray(audio, dtype=float)
    if dados.ndim > 1:
        dados = dados.mean(axis=1)
    return dados.flatten()


def simular(tecla, duracao=3.0, fs=FS, ruido=0.25, semente=0):
    """Gera um sinal DTMF sujo (ruido branco + 3 tons parasitas) para teste."""
    rng = np.random.default_rng(semente)
    signal = signalMeu()
    f_baixa, f_alta = DTMF[tecla]

    t, s1 = signal.generateSin(f_baixa, 1.0, duracao, fs)
    _, s2 = signal.generateSin(f_alta, 1.0, duracao, fs)
    dados = (s1 + s2) / 2.0

    # ruidos que imitam a transmissao acustica real
    for f, a in ((60, 0.30), (310, 0.22), (2050, 0.18)):
        _, r = signal.generateSin(f, a, duracao, fs)
        dados = dados + r
    dados = dados + rng.normal(0, ruido, len(dados))
    return dados


# ------------------------------------------------------------------- picos
def achar_picos(xf, yf, n=5, dist_hz=5.0, fmin=50.0):
    """
    Devolve os n maiores picos de yf como [(freq, amplitude), ...].
    Picos a menos de dist_hz de um pico maior ja aceito sao descartados
    (sao o mesmo pico alargado pela transmissao).
    """
    df = xf[1] - xf[0]

    if TEM_PEAKUTILS:
        idx = peakutils.indexes(yf, thres=0.05, min_dist=max(1, int(dist_hz / df)))
    else:
        # fallback: maximos locais simples, caso peakutils nao esteja instalado
        idx = np.where((yf[1:-1] > yf[:-2]) & (yf[1:-1] >= yf[2:]))[0] + 1
        idx = idx[yf[idx] > 0.05 * yf.max()]

    idx = [i for i in idx if xf[i] >= fmin]
    idx.sort(key=lambda i: yf[i], reverse=True)   # do mais forte ao mais fraco

    picos = []
    for i in idx:
        if all(abs(xf[i] - f) > dist_hz for f, _ in picos):
            picos.append((float(xf[i]), float(yf[i])))
        if len(picos) == n:
            break
    return picos


def identificar_tecla(picos, tol=20):
    """
    Procura entre os picos encontrados um par (linha, coluna) da tabela DTMF.
    Testa os pares do mais forte para o mais fraco.
    """
    cand_baixas = [(f, a) for f, a in picos
                   if any(abs(f - fl) <= tol for fl in LINHAS)]
    cand_altas = [(f, a) for f, a in picos
                  if any(abs(f - fc) <= tol for fc in COLUNAS)]

    melhor = None
    for fb, ab in cand_baixas:
        for fa, aa in cand_altas:
            tecla = tecla_de(fb, fa, tol)
            if tecla and (melhor is None or ab + aa > melhor[3]):
                melhor = (tecla, fb, fa, ab + aa)
    if melhor is None:
        return None
    return melhor[0], melhor[1], melhor[2]


# ------------------------------------------------------------------ plots
def plotar(dados, xf, yf, picos, fs=FS, tecla=None):
    t = np.linspace(0, len(dados) / fs, len(dados), endpoint=False)
    n = int(0.01 * fs)          # ~10 ms: da para ver a forma de onda

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7))

    ax1.plot(t[:n], dados[:n])
    ax1.set_title("Sinal captado (primeiros {:.0f} ms)".format(1000 * n / fs))
    ax1.set_xlabel("Tempo (s)")
    ax1.set_ylabel("Amplitude")
    ax1.grid(True)

    ax2.plot(xf, yf)
    for f, a in picos:
        ax2.plot(f, a, "rv")
        ax2.annotate("{:.0f} Hz".format(f), (f, a), textcoords="offset points",
                     xytext=(0, 8), ha="center", fontsize=8, color="r")
    titulo = "FFT do sinal captado"
    if tecla:
        titulo += " - tecla identificada: '{}'".format(tecla)
    ax2.set_title(titulo)
    ax2.set_xlabel("Frequencia (Hz)")
    ax2.set_ylabel("Amplitude")
    ax2.set_xlim(0, 2500)
    ax2.grid(True)

    fig.tight_layout()
    fig.savefig("decode_fft.png", dpi=120)


# ------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="Decoder DTMF")
    ap.add_argument("--dur", type=float, default=3.0, help="tempo de gravacao (s)")
    ap.add_argument("--wav", help="decodifica um arquivo WAV em vez do microfone")
    ap.add_argument("--sim", help="simula a transmissao desta tecla (teste sem audio)")
    ap.add_argument("--sem-grafico", action="store_true")
    args = ap.parse_args()

    signal = signalMeu()
    fs = FS

    if args.sim:
        tecla_sim = args.sim.strip().upper()
        if tecla_sim not in DTMF:
            print("Tecla invalida para simulacao: {}".format(tecla_sim))
            return 1
        print("[modo simulacao] gerando sinal da tecla '{}' com ruido".format(tecla_sim))
        dados = simular(tecla_sim, args.dur, fs)
    elif args.wav:
        dados, fs = ler_wav(args.wav)
        print("[arquivo] {} | fs = {} Hz | {} amostras".format(args.wav, fs, len(dados)))
    else:
        dados = gravar(args.dur, fs)

    # --- Fourier do sinal captado
    xf, yf = signal.calcFFT(dados, fs)

    picos = achar_picos(xf, yf, n=5)
    print("\nPicos encontrados (do mais forte ao mais fraco):")
    for i, (f, a) in enumerate(picos, 1):
        print("  {}. {:8.1f} Hz   amplitude {:.4f}".format(i, f, a))

    res = identificar_tecla(picos)
    print()
    if res:
        tecla, fb, fa = res
        print("Frequencias DTMF casadas: {:.1f} Hz (linha) + {:.1f} Hz (coluna)".format(fb, fa))
        print(">>> TECLA PRESSIONADA: {} <<<".format(tecla))
        if args.sim and tecla != args.sim.strip().upper():
            print("ATENCAO: diferente da tecla simulada ({})".format(args.sim))
    else:
        tecla = None
        print("Nao foi possivel casar os picos com a tabela DTMF.")
        print("Tabela de referencia:")
        print(tabela_str())

    if not args.sem_grafico:
        plotar(dados, xf, yf, picos, fs, tecla)
        plt.show()
    return 0 if res else 2


if __name__ == "__main__":
    sys.exit(main())
