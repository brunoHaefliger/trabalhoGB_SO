import random
import sys
import threading
import time
from constants       import PAGE_SIZE, OFFSET_BITS, VIRT_MEM_SIZE
from physical_memory import PhysicalMemory
from process         import Process
from mmu             import MMU

# Especifica UTF-8, se não for rodar no Ubuntu e sim no Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ─────────────────────────────────────────────────────────────────
#  Parâmetros de simulação
# ─────────────────────────────────────────────────────────────────
NUM_PROCESSES      = 3      # número de processos
ACCESSES_PER_PROC  = 12     # quantas instruções cada processo gera
THREAD_DELAY_S     = 0.05   # pequena pausa para ser mais legível

# Tamanhos fixos (bytes) para reprodução determinística na demonstração
PROCESS_SIZES = [
    96  * 1024,   # PID 1 – 96 KB  -> 12 páginas
    40  * 1024,   # PID 2 – 40 KB  ->  5 páginas
    128 * 1024,   # PID 3 – 128 KB -> 16 páginas
]

# ─────────────────────────────────────────────────────────────────
#  Saída formatada
# ─────────────────────────────────────────────────────────────────
_print_lock = threading.Lock()

def cprint(msg: str):
    with _print_lock:
        print(msg, flush=True)

def section(title: str):
    cprint(f"\n{'═'*64}")
    cprint(f"  {title}")
    cprint(f"{'═'*64}")

def divider():
    cprint("─" * 64)

# ─────────────────────────────────────────────────────────────────
#  Formatação de um resultado de acesso
# ─────────────────────────────────────────────────────────────────

def format_result(r: dict, access_no: int) -> str:
    lines = []
    lines.append(f"\n[PID {r['pid']}] Instrução #{access_no}")
    lines.append(
        f"  Endereço virtual : 0x{r['virtual_addr']:06X}"
        f"  (página {r['page_no']:>3d} | offset {r['offset']:>4d})"
    )

    if r["page_fault"]:
        lines.append("  *** PAGE FAULT ***")
        if r["evicted"]:
            ep, epg = r["evicted"]
            lines.append(
                f"  -> Substituição LRU: PID {ep} página {epg} removida do frame {r['frame_no']}"
            )
        else:
            lines.append(f"  -> Frame livre {r['frame_no']} utilizado")
        lines.append(f"  -> Página {r['page_no']} carregada do disco -> frame {r['frame_no']}")
    else:
        lines.append(f"  -> Página {r['page_no']} já em memória (frame {r['frame_no']})")

    lines.append(
        f"  Endereço físico  : 0x{r['physical_addr']:05X}"
        f"  (frame {r['frame_no']} | offset {r['offset']:>4d})"
    )
    lines.append(f"  Conteúdo lido    : 0x{r['byte_value']:02X}  ({r['byte_value']})")
    return "\n".join(lines)

# ─────────────────────────────────────────────────────────────────
#  Thread de processo leve
# ─────────────────────────────────────────────────────────────────

def thread_worker(proc: Process, mmu: MMU, num_accesses: int, seed: int):
    rng = random.Random(seed)
    max_addr = proc.size - 1

    for i in range(1, num_accesses + 1):
        virt_addr = rng.randint(0, max_addr)
        try:
            result = mmu.translate(proc.pid, virt_addr)
            cprint(format_result(result, i))
        except ValueError as exc:
            cprint(f"[PID {proc.pid}] ERRO: {exc}")
        time.sleep(THREAD_DELAY_S)

# ─────────────────────────────────────────────────────────────────
#  Entrada principal
# ─────────────────────────────────────────────────────────────────

def main():
    section("SIMULADOR DE MEMÓRIA VIRTUAL")
    cprint(f"  Memória principal : 64 KB  ({64*1024} bytes)")
    cprint(f"  Memória virtual   : 1 MB   ({VIRT_MEM_SIZE} bytes)")
    cprint(f"  Tamanho de página : 8 KB   ({PAGE_SIZE} bytes)")
    cprint(f"  Frames disponíveis: {64*1024 // PAGE_SIZE}")
    cprint(f"  Páginas virtuais  : {VIRT_MEM_SIZE // PAGE_SIZE}")
    cprint(f"  Algoritmo subst.  : LRU (Least Recently Used)")

    # ── instância única de memória física e MMU ───────────────────
    phys_mem = PhysicalMemory()
    mmu      = MMU(phys_mem)

    # ── criação dos processos ─────────────────────────────────────
    section("PROCESSOS CRIADOS")
    processes = []
    for pid, size in enumerate(PROCESS_SIZES[:NUM_PROCESSES], start=1):
        proc = Process(pid=pid, size=size, seed=pid * 7)
        mmu.register_process(proc)
        processes.append(proc)
        cprint(f"  {proc}")

    # ── lançamento das threads ────────────────────────────────────
    section("EXECUÇÃO DAS THREADS (acesso concorrente à memória)")
    threads = []
    for proc in processes:
        t = threading.Thread(
            target=thread_worker,
            args=(proc, mmu, ACCESSES_PER_PROC, proc.pid * 99),
            name=f"T-PID{proc.pid}",
            daemon=True,
        )
        threads.append(t)

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # ── estado final ──────────────────────────────────────────────
    section("ESTADO FINAL – MEMÓRIA FÍSICA")
    cprint(phys_mem.dump())

    section("TABELAS DE PÁGINAS (páginas residentes)")
    for proc in processes:
        cprint(mmu.dump_page_table(proc.pid))
        cprint("")

    section("ESTATÍSTICAS DE ACESSO")
    cprint(mmu.dump_stats())

    cprint(f"\n{'═'*64}")
    cprint("  Simulação concluída.")
    cprint(f"{'═'*64}\n")


if __name__ == "__main__":
    main()
