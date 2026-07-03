# Simulador de Memória Virtual

Trabalho de Sistemas Operacionais — GB

## Sistema fictício simulado

| Parâmetro | Valor |
|---|---|
| Memória principal (física) | 64 KB |
| Memória virtual | 1 MB |
| Tamanho de página / frame | 8 KB |
| Número de frames | 8 |
| Número de páginas virtuais | 128 |
| Algoritmo de substituição | LRU |

## Estrutura do projeto

```
TrabalhoSO_GB/
├── constants.py        # Constantes do sistema (tamanhos, bits de offset, máscaras)
├── physical_memory.py  # Memória principal: 8 frames de 8 KB
├── process.py          # Processo leve: tamanho, páginas, dados em "disco"
├── page_table.py       # Tabela de páginas por processo + entradas PageTableEntry
├── mmu.py              # MMU: tradução de endereços, page fault, LRU
└── simulator.py        # Orquestrador: threads, saída formatada, estatísticas
```

## Como rodar (Ubuntu)

```bash
# Instalar Python 3 
sudo apt update && sudo apt install -y python3

# Clona ou copia os arquivos, depois:
python3 simulator.py
```

Não há dependências externas, usa apenas a biblioteca padrão do Python 3.

## Arquitetura

### Memória física (`PhysicalMemory`)
- 8 frames de 8192 bytes cada (total 65536 bytes = 64 KB)
- `frame_owner[i]` registra qual `(pid, page)` ocupa cada frame
- Suporta leitura de byte individual e escrita de frame inteiro

### Processo leve (`Process`)
- Tamanho entre 1 byte e 1 MB, limitado ao espaço virtual
- Dados em "disco" gerados deterministicamente (RNG com semente `pid × pagina`)
- Byte 0 = PID, Byte 1 = número da página -> fácil identificação visual

### Tabela de páginas (`PageTable` / `PageTableEntry`)
- Uma entrada por página virtual do processo
- Campos: `frame_no`, `valid`, `dirty`, `last_used` (timestamp para LRU)

### MMU (`MMU`)
Fluxo de `translate(pid, virtual_addr)`:
1. Extrai `page_no = virtual_addr >> 13` e `offset = virtual_addr & 0x1FFF`
2. Consulta a tabela de páginas do processo
3. **Página presente** -> atualiza LRU e retorna o byte
4. **Page fault** -> chama `_load_page`:
   - Se há frame livre -> usa o primeiro livre
   - Caso contrário -> `_lru_evict`: percorre todos os frames ocupados, escolhe aquele cujo `last_used` é o menor, invalida na tabela do processo dono e libera o frame
5. Copia dados do "disco" para o frame e atualiza a tabela de páginas

### Algoritmo LRU
Cada acesso bem-sucedido incrementa um relógio global (`_clock`) e salva o valor em `last_used` da entrada. Ao precisar substituir, percorre todos os frames e escolhe o menor `last_used`.

### Threads
- `NUM_PROCESSES` threads são disparadas simultaneamente
- Cada thread simula `ACCESSES_PER_PROC` acessos aleatórios
- Um mutex (`threading.Lock`) serializa acesso à MMU e à saída
- `THREAD_DELAY_S` adiciona pausa para tornar o output legível

## Saída esperada

Para cada instrução gerada:
```
[PID 1] Instrução #4
  Endereço virtual : 0x0132E9  (página   9 | offset 4841)
  *** PAGE FAULT ***
  -> Substituição LRU: PID 2 página 0 removida do frame 1
  -> Página 9 carregada do disco -> frame 1
  Endereço físico  : 0x032E9  (frame 1 | offset 4841)
  Conteúdo lido    : 0x36  (54)
```

Ao final: estado da memória física, tabelas de páginas e estatísticas por processo.
