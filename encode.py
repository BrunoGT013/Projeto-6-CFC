# -*- coding: utf-8 -*-
"""
Projeto 6 - Camada Fisica da Computacao
ENCODER DTMF: le uma tecla do teclado numerico, gera as duas senoides
correspondentes, soma, emite o som e plota o sinal no tempo e sua FFT.

Uso:
    python encode.py                 # pergunta a tecla, toca 3 s
    python encode.py 5               # tecla 5
    python encode.py 5 --dur 4       # 4 segundos de tom
    python encode.py 5 --sem-audio   # so gera o WAV e os graficos
"""

import argparse
import sys

import numpy as np
import matplotlib.pyplot as plt

from suaBibSignal import signalMeu
from dtmf import DTMF, FS, FMIN, FMAX, tabela_str, salvar_wav


def signal_handler(signal, frame):
    print("You pressed Ctrl+C!")
    sys.exit(0)


def todB(s):
    """Converte intensidade em dB."""
    return 10 * np.log10(s)


def pedir_tecla():
    print("\nTabela DTMF:")
    print(tabela_str())
    while True:
        t = input("\nDigite a tecla a transmitir: ").strip().upper()
        if t in DTMF:
            return t
        print("Tecla invalida. Use 0-9, *, # ou A-D.")


def gerar_tom(tecla, duracao, fs=FS):
    """Gera a soma das duas senoides DTMF da tecla. Devolve (t, soma, s1, s2)."""
    signal = signalMeu()
    f_baixa, f_alta = DTMF[tecla]

    # amplitude 1 em cada senoide, conforme o enunciado
    t, s1 = signal.generateSin(f_baixa, 1.0, duracao, fs)
    _, s2 = signal.generateSin(f_alta, 1.0, duracao, fs)

    return t, s1 + s2, s1, s2


def plotar(t, tom, s1, s2, tecla, fs=FS):
    f_baixa, f_alta = DTMF[tecla]
    signal = signalMeu()

    # as frequencias sao altas: plota apenas ~5 periodos da senoide mais lenta
    janela = 5.0 / f_baixa
    n = int(janela * fs)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7))

    ax1.plot(t[:n], s1[:n], "--", lw=1, alpha=0.7, label="{} Hz".format(f_baixa))
    ax1.plot(t[:n], s2[:n], "--", lw=1, alpha=0.7, label="{} Hz".format(f_alta))
    ax1.plot(t[:n], tom[:n], lw=2, color="k", label="soma (transmitido)")
    ax1.set_title("Tecla '{}' - sinal no tempo ({:.0f} Hz + {:.0f} Hz)".format(
        tecla, f_baixa, f_alta))
    ax1.set_xlabel("Tempo (s)")
    ax1.set_ylabel("Amplitude")
    ax1.grid(True)
    ax1.legend(loc="upper right", fontsize=8)

    xf, yf = signal.calcFFT(tom, fs)
    ax2.plot(xf, yf)
    for f in (f_baixa, f_alta):
        ax2.axvline(f, color="r", ls=":", alpha=0.6)
        ax2.annotate("{} Hz".format(f), (f, yf.max() * 0.9),
                     ha="center", fontsize=8, color="r")
    ax2.set_title("Transformada de Fourier do sinal transmitido")
    ax2.set_xlabel("Frequencia (Hz)")
    ax2.set_ylabel("Amplitude")
    ax2.set_xlim(FMIN, FMAX)
    ax2.grid(True)

    fig.tight_layout()
    fig.savefig("encode_tecla_{}.png".format(
        {"*": "estrela", "#": "cerquilha"}.get(tecla, tecla)), dpi=120)


def main():
    ap = argparse.ArgumentParser(description="Encoder DTMF")
    ap.add_argument("tecla", nargs="?", help="tecla a transmitir (0-9, *, #, A-D)")
    ap.add_argument("--dur", type=float, default=3.0, help="duracao do tom em s")
    ap.add_argument("--sem-audio", action="store_true",
                    help="nao toca o som; apenas gera WAV e graficos")
    args = ap.parse_args()

    print("Inicializando encoder")

    print("Aguardando usuario")
    tecla = args.tecla.strip().upper() if args.tecla else pedir_tecla()
    if tecla not in DTMF:
        print("Tecla invalida: {}".format(tecla))
        return 1
    NUM = tecla

    print("Gerando Tons base")
    f_baixa, f_alta = DTMF[NUM]
    t, tom, s1, s2 = gerar_tom(NUM, args.dur)
    print("  freq. baixa (linha)  : {} Hz".format(f_baixa))
    print("  freq. alta  (coluna) : {} Hz".format(f_alta))
    print("  fs = {} Hz | {} amostras | {:.1f} s".format(FS, len(tom), args.dur))

    # a soma tem amplitude 2; divide por 2 para nao saturar a placa de audio
    tom_norm = tom / 2.0

    arquivo = "tom_{}.wav".format({"*": "estrela", "#": "cerquilha"}.get(NUM, NUM))
    salvar_wav(arquivo, tom_norm)
    print("Audio salvo em {} (para testar o decoder sem microfone)".format(arquivo))

    if not args.sem_audio:
        import sounddevice as sd
        print("Executando as senoides (emitindo o som)")
        print("Gerando Tom referente ao simbolo : {}".format(NUM))
        sd.play(tom_norm, FS)
        sd.wait()   # aguarda fim do audio

    plotar(t, tom, s1, s2, NUM)
    print("Graficos gerados. Feche a janela para encerrar.")
    plt.show()
    return 0


if __name__ == "__main__":
    sys.exit(main())
