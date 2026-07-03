"""
MMU - Memory Management Unit

Responsabilidades:
  - Manter a tabela de páginas de cada processo registrado.
  - Traduzir endereço virtual -> endereço físico.
  - Detectar page fault e resolvê-lo (frames livres ou substituição LRU).
  - Registrar estatísticas de acesso.

Algoritmo de substituição: LRU (Least Recently Used)
  - A página residente com o menor timestamp 'last_used' é escolhida para sair.
  - O timestamp global (self._clock) avança a cada acesso bem-sucedido.
"""

import threading
from collections import defaultdict

from constants    import NUM_FRAMES, PAGE_SIZE, OFFSET_MASK, OFFSET_BITS
from physical_memory import PhysicalMemory
from page_table   import PageTable
from process      import Process


class MMU:
    def __init__(self, phys_mem: PhysicalMemory):
        self.phys_mem   = phys_mem
        self._tables:   dict[int, PageTable] = {}   # pid → PageTable
        self._processes: dict[int, Process]  = {}   # pid → Process
        self._lock      = threading.Lock()
        self._clock     = 0                          # contador global de acessos

        # Estatísticas
        self.stats = defaultdict(lambda: {"accesses": 0, "page_faults": 0})

    # ── registro de processo ──────────────────────────────────────────────────

    def register_process(self, proc: Process):
        with self._lock:
            self._processes[proc.pid] = proc
            self._tables[proc.pid]    = PageTable(proc.num_pages)

    # ── tradução de endereços (ponto central da MMU) ──────────────────────────

    def translate(self, pid: int, virtual_addr: int) -> dict:
        """
        Recebe um endereço virtual de 'pid' e retorna um dict com:
          - virtual_addr   : endereço virtual original
          - page_no        : número da página virtual
          - offset         : deslocamento dentro da página
          - page_fault     : True se houve falta de página
          - frame_no       : frame físico final
          - physical_addr  : endereço físico resultante
          - byte_value     : byte lido naquele endereço
          - evicted        : (pid, page_no) substituído, ou None
          - pid            : pid do processo
        """
        result = {
            "pid": pid, "virtual_addr": virtual_addr,
            "page_fault": False, "evicted": None,
        }

        with self._lock:
            self._clock += 1
            proc  = self._processes[pid]
            table = self._tables[pid]

            # ── decompõe o endereço virtual ──────────────────────────────────
            page_no = virtual_addr >> OFFSET_BITS          # bits superiores
            offset  = virtual_addr &  OFFSET_MASK          # 13 bits inferiores

            result["page_no"] = page_no
            result["offset"]  = offset

            # página existe no espaço do processo?
            if not proc.valid_page(page_no):
                raise ValueError(
                    f"PID {pid}: endereço virtual 0x{virtual_addr:06X} "
                    f"fora do espaço do processo (páginas 0..{proc.num_pages-1})"
                )

            self.stats[pid]["accesses"] += 1

            # ── page in memory? ───────────────────────────────────────────────
            if table.is_valid(page_no):
                frame_no = table.get(page_no).frame_no
                table.update_lru(page_no, self._clock)
            else:
                # ── PAGE FAULT ────────────────────────────────────────────────
                result["page_fault"] = True
                self.stats[pid]["page_faults"] += 1
                frame_no, evicted = self._load_page(pid, page_no)
                result["evicted"] = evicted

            phys_addr  = frame_no * PAGE_SIZE + offset
            byte_value = self.phys_mem.read_byte(frame_no, offset)

            result["frame_no"]     = frame_no
            result["physical_addr"]= phys_addr
            result["byte_value"]   = byte_value

        return result

    # ── carregamento de página ────────────────────────────────────────────────

    def _load_page(self, pid: int, page_no: int) -> tuple[int, tuple | None]:
        """
        Carrega a página 'page_no' do processo 'pid' na memória principal.
        Retorna (frame_no, evicted_owner).
        """
        free = self.phys_mem.free_frames()
        evicted = None

        if free:
            # ── caso a): frame livre disponível ──────────────────────────────
            frame_no = free[0]
        else:
            # ── caso b): substituição LRU ─────────────────────────────────────
            frame_no, evicted = self._lru_evict()

        # Copia dados do "disco" para o frame
        data = self._processes[pid].get_page_from_disk(page_no)
        self.phys_mem.write_frame(frame_no, data, pid, page_no)
        self._tables[pid].map(page_no, frame_no, self._clock)

        return frame_no, evicted

    # ── algoritmo LRU ────────────────────────────────────────────────────────

    def _lru_evict(self) -> tuple[int, tuple]:
        """
        Percorre todos os frames ocupados e escolhe o frame cujo dono tem
        o menor 'last_used' (menos recentemente usado).
        Invalida a entrada correspondente na tabela de páginas do dono.
        Retorna (frame_no, (owner_pid, owner_page)).
        """
        best_frame    = -1
        best_ts       = float("inf")
        best_owner    = None

        for frame_idx, owner in enumerate(self.phys_mem.frame_owner):
            if owner is None:
                continue
            o_pid, o_page = owner
            ts = self._tables[o_pid].get(o_page).last_used
            if ts < best_ts:
                best_ts    = ts
                best_frame = frame_idx
                best_owner = owner

        # Invalida a entrada da tabela do processo despejado
        evicted_pid, evicted_page = best_owner
        self._tables[evicted_pid].unmap(evicted_page)
        self.phys_mem.free_frame(best_frame)

        return best_frame, best_owner

    # ── utilitários de diagnóstico ────────────────────────────────────────────

    def dump_page_table(self, pid: int) -> str:
        return self._tables[pid].dump(pid)

    def dump_all_page_tables(self) -> str:
        parts = []
        for pid in sorted(self._tables):
            parts.append(self.dump_page_table(pid))
        return "\n\n".join(parts)

    def dump_stats(self) -> str:
        lines = [f"  {'PID':<6} {'ACESSOS':<12} {'PAGE FAULTS':<14} {'TAXA PF'}"]
        lines.append("  " + "─" * 44)
        for pid in sorted(self.stats):
            a  = self.stats[pid]["accesses"]
            pf = self.stats[pid]["page_faults"]
            taxa = f"{pf/a*100:.1f}%" if a else "─"
            lines.append(f"  {pid:<6} {a:<12} {pf:<14} {taxa}")
        return "\n".join(lines)
