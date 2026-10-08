# -*- coding: utf-8 -*-
"""
suaBibSignal - biblioteca de apoio de Camada Fisica da Computacao.

Versao sem dependencia de scipy: a janela de Hann usada no calculo da FFT
vem do numpy (np.hanning).
"""

import numpy as np
from numpy.fft import fft
import matplotlib.pyplot as plt


class signalMeu:
    def __init__(self):
        self.santaCruz = 1906

    def generateSin(self, freq, amplitude, duration, fs):
        """Gera (tempo, senoide) com 'fs' amostras por segundo."""
        n = int(duration * fs)
        x = np.linspace(0.0, duration, n, endpoint=False)
        s = amplitude * np.sin(2 * np.pi * freq * x)
        return (x, s)

    def calcFFT(self, signal, fs):
        """Devolve (frequencias, amplitudes) do espectro de modulo do sinal."""
        N = len(signal)
        W = np.hanning(N)                       # janela reduz vazamento espectral
        T = 1 / fs
        xf = np.linspace(0.0, 1.0 / (2.0 * T), N // 2)
        yf = fft(signal * W)
        # normaliza pela energia da janela para a amplitude ter sentido fisico
        yf = np.abs(yf[: N // 2]) * (4.0 / N)
        return (xf, yf)

    def plotFFT(self, signal, fs, title="Transformada de Fourier", fmax=None):
        """Plota o espectro do sinal. fmax limita o eixo x (Hz)."""
        xf, yf = self.calcFFT(signal, fs)
        plt.figure()
        plt.plot(xf, yf)
        plt.grid(True)
        plt.title(title)
        plt.xlabel("Frequencia (Hz)")
        plt.ylabel("Amplitude")
        if fmax:
            plt.xlim(0, fmax)
        return (xf, yf)
