# -*- coding: utf-8 -*-
"""Tabela DTMF e utilitarios compartilhados pelo encoder e pelo decoder."""

import wave
import numpy as np

FS = 44100          # taxa de amostragem (Hz) - padrao das placas de audio
BITS = 16           # bits por amostra na digitalizacao

LINHAS = [697, 770, 852, 941]        # frequencias baixas  (linhas do teclado)
COLUNAS = [1209, 1336, 1477, 1633]   # frequencias altas   (colunas do teclado)

# Faixa util do espectro (Hz). Cobre as 8 frequencias DTMF com folga para a
# tolerancia de 20 Hz (677..1653) e descarta o que nao pode ser tom DTMF:
# zumbido de 60 Hz da rede, ruido grave e ruido agudo.
FMIN = 600
FMAX = 1800

TECLADO = [
    ["1", "2", "3", "A"],
    ["4", "5", "6", "B"],
    ["7", "8", "9", "C"],
    ["*", "0", "#", "D"],
]

# tecla -> (freq_baixa, freq_alta)
DTMF = {
    TECLADO[i][j]: (LINHAS[i], COLUNAS[j])
    for i in range(4)
    for j in range(4)
}


def tecla_de(f_baixa, f_alta, tol=20):
    """Volta a tecla cujas frequencias DTMF casam com o par dado (+- tol Hz)."""
    for tecla, (fb, fa) in DTMF.items():
        if abs(fb - f_baixa) <= tol and abs(fa - f_alta) <= tol:
            return tecla
    return None


def tabela_str():
    cab = "        " + "".join("{:>8}".format(c) for c in COLUNAS)
    linhas = [cab]
    for i, f in enumerate(LINHAS):
        linhas.append("{:>5} Hz".format(f) + "".join("{:>8}".format(t) for t in TECLADO[i]))
    return "\n".join(linhas)


def salvar_wav(caminho, sinal, fs=FS):
    """Grava um sinal float em [-1, 1] como WAV PCM 16 bits mono."""
    dados = np.clip(np.asarray(sinal, dtype=float), -1.0, 1.0)
    inteiros = (dados * (2 ** (BITS - 1) - 1)).astype("<i2")
    with wave.open(caminho, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(BITS // 8)
        w.setframerate(fs)
        w.writeframes(inteiros.tobytes())


def ler_wav(caminho):
    """Le um WAV PCM 16 bits e devolve (sinal float mono em [-1,1], fs)."""
    with wave.open(caminho, "rb") as w:
        fs = w.getframerate()
        canais = w.getnchannels()
        quadros = w.readframes(w.getnframes())
    dados = np.frombuffer(quadros, dtype="<i2").astype(float) / (2 ** (BITS - 1))
    if canais > 1:                       # estereo -> media dos canais
        dados = dados.reshape(-1, canais).mean(axis=1)
    return dados, fs
