"""
Entrada da tabela de páginas de um processo.
"""

from dataclasses import dataclass, field


@dataclass
class PageTableEntry:
    page_no: int                   # número da página virtual
    frame_no: int  = -1            # frame físico mapeado (-1 = não mapeado)
    valid: bool    = False         # True se a página está em memória principal
    dirty: bool    = False         # True se a página foi modificada (para extensões futuras)
    last_used: int = 0             # timestamp para LRU


class PageTable:
    """Tabela de páginas de um único processo."""

    def __init__(self, num_pages: int):
        self.entries: list[PageTableEntry] = [
            PageTableEntry(page_no=i) for i in range(num_pages)
        ]

    def get(self, page_no: int) -> PageTableEntry:
        return self.entries[page_no]

    def is_valid(self, page_no: int) -> bool:
        return self.entries[page_no].valid

    def map(self, page_no: int, frame_no: int, timestamp: int):
        e = self.entries[page_no]
        e.frame_no  = frame_no
        e.valid     = True
        e.last_used = timestamp

    def unmap(self, page_no: int):
        e = self.entries[page_no]
        e.frame_no = -1
        e.valid    = False

    def update_lru(self, page_no: int, timestamp: int):
        self.entries[page_no].last_used = timestamp

    # ── diagnóstico ──────────────────────────────────────────────────────────

    def dump(self, pid: int) -> str:
        lines = [f"  Tabela de páginas – PID {pid}"]
        lines.append(f"  {'PAG':<6} {'FRAME':<8} {'VÁLIDO':<8} {'LAST_USED'}")
        lines.append("  " + "─" * 36)
        for e in self.entries:
            valid_str = "SIM" if e.valid else "NÃO"
            frame_str = str(e.frame_no) if e.valid else "─"
            lines.append(f"  {e.page_no:<6} {frame_str:<8} {valid_str:<8} {e.last_used}")
        return "\n".join(lines)
