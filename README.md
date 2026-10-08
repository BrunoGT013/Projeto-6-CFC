# Projeto 6 — DTMF (Camada Física da Computação)

Sistema de transmissão e recepção de teclas por som usando **DTMF**
(*Dual-Tone Multi-Frequency*): cada tecla vira a soma de duas senoides, o som é
emitido pelo alto-falante, captado pelo microfone, e o receptor descobre a tecla
pela **Transformada de Fourier** do sinal gravado.

## Arquivos

| arquivo | o que faz |
|---|---|
| `suaBibSignal.py` | biblioteca de apoio: `generateSin`, `calcFFT`, `plotFFT` |
| `dtmf.py` | tabela DTMF, leitura/escrita de WAV 16 bits, casamento de frequências |
| `encode.py` | **transmissor**: lê a tecla, gera e toca as 2 senoides, plota sinal + FFT |
| `decode.py` | **receptor**: grava o áudio, calcula a FFT, acha os picos e identifica a tecla |
| `teste_dtmf.py` | teste automático das 16 teclas, sem precisar de microfone |

## Tabela DTMF

|        | 1209 Hz | 1336 Hz | 1477 Hz | 1633 Hz |
|--------|---------|---------|---------|---------|
| **697 Hz** | 1 | 2 | 3 | A |
| **770 Hz** | 4 | 5 | 6 | B |
| **852 Hz** | 7 | 8 | 9 | C |
| **941 Hz** | * | 0 | # | D |

As frequências não são múltiplas entre si de propósito: assim nenhum tom cai
sobre o harmônico de outro e a FFT consegue separá-los sem ambiguidade.

## Como rodar

Dependências: `pip install numpy matplotlib sounddevice peakutils`

### Transmissão + recepção ao vivo (dois terminais)

```bash
# terminal 1 (receptor) — começa a gravar depois de 3 s de contagem
python decode.py --dur 3

# terminal 2 (transmissor) — toca o tom durante a gravação
python encode.py 5 --dur 3
```

### Sem microfone (verificação do algoritmo)

```bash
python encode.py 7 --dur 2 --sem-audio   # gera tom_7.wav + gráficos
python decode.py --wav tom_7.wav         # decodifica o arquivo
python decode.py --sim 9                 # simula transmissão ruidosa da tecla 9
python teste_dtmf.py                     # testa as 16 teclas
```

## Como funciona

**Encoder.** Com `fs = 44100` amostras/s e duração `T`, monta-se o vetor de tempo
com `T·fs` pontos e geram-se `sin(2πf₁t)` e `sin(2πf₂t)` com amplitude 1. O sinal
transmitido é a soma das duas. Como a soma chega a amplitude 2, ela é dividida por
2 antes de ir para a placa de áudio — senão satura (*clipping*) e aparecem
harmônicos que não existem no sinal original.

**Decoder.** O áudio gravado vem como matriz `numAmostras × canais`; os canais são
combinados em uma lista só. A FFT é calculada com janela de Hann (reduz o
vazamento espectral que alargaria os picos). Em seguida `peakutils.indexes` acha
os máximos do espectro; os picos são ordenados do mais forte ao mais fraco e
qualquer pico a menos de **5 Hz** de um pico maior já aceito é descartado — é o
mesmo tom alargado pela transmissão, não um tom novo. Dos 5 picos mais fortes,
procura-se o par que casa (tolerância de 20 Hz) com uma linha e uma coluna da
tabela: esse par identifica a tecla. Os demais picos são ruído (rede elétrica,
ruído ambiente).

## Resultados dos testes

`python teste_dtmf.py` — **todos passaram**:

- 16/16 teclas reconhecidas no sinal limpo;
- 16/16 com ruído branco + 3 tons parasitas (60 Hz, 310 Hz, 2050 Hz) mais fortes
  que os tons DTMF em parte do espectro;
- ida e volta pelo WAV de 16 bits (digitalização real) sem erro;
- a tecla 5 continua sendo reconhecida com ruído branco de σ = 4,0, ou seja,
  **8× a amplitude de cada senoide DTMF** — a FFT concentra a energia dos tons em
  duas raias, enquanto o ruído se espalha por todo o espectro.

Gráficos gerados: `encode_tecla_*.png` (sinal no tempo + FFT transmitida) e
`decode_fft.png` (sinal captado + FFT com os picos marcados).

---

## Exercícios do material "Digitalização"

**Memória para 1 hora de áudio estéreo** (44,1 kHz, 16 bits, 2 canais)

```
44100 amostras/s × 2 canais × 2 bytes = 176 400 B/s
176 400 × 3600 s = 635 040 000 B ≈ 635 MB  (≈ 605,6 MiB ≈ 5,08 Gbit)
```

**1) ECG** — 5 min, 1 kHz, 14 bits, enlace de 1000 bps com 10% de overhead

```
bits gerados = 300 s × 1000 amostras/s × 14 bits = 4 200 000 bits
taxa útil    = 1000 bps × 0,9 = 900 bps
tempo        = 4 200 000 / 900 ≈ 4 667 s ≈ 78 minutos
```

**2) Captador de guitarra** — faixa de −50 a +50 mV, resolução mínima de 10 µV

```
níveis necessários = 100 mV / 10 µV = 10 000
2^13 = 8 192  (insuficiente)      2^14 = 16 384  (suficiente)
→ 14 bits por amostra  (resolução real = 100 mV / 16 384 ≈ 6,1 µV)
```

**3) Senoide de 4400 Hz, Ts = 25 µs, reproduzida a 80 kHz**

```
fs de gravação = 1 / 25 µs = 40 000 Hz
4400 Hz < 20 000 Hz (Nyquist) → gravação sem aliasing
reprodução a 80 kHz = 2 × 40 kHz → as amostras saem no dobro da velocidade
→ frequência ouvida = 2 × 4400 = 8800 Hz
```
