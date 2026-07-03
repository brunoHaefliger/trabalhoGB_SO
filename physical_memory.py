"""
Representa a memória principal (física) com NUM_FRAMES frames de PAGE_SIZE bytes.
Cada frame é um bytearray; frame_owner rastreia qual (pid, page) ocupa cada frame.
"""

from constants import NUM_FRAMES, PAGE_SIZE


class PhysicalMemory:
    def __init__(self):
        # Cada frame é um bytearray de PAGE_SIZE bytes inicializado com zeros
        self.frames: list[bytearray] = [bytearray(PAGE_SIZE) for _ in range(NUM_FRAMES)]
        # Qual processo / página virtual ocupa cada frame (None = livre)
        self.frame_owner: list[tuple | None] = [None] * NUM_FRAMES

    # ── leitura / escrita de um byte ──────────────────────────────────────────

    def read_byte(self, frame_idx: int, offset: int) -> int:
        return self.frames[frame_idx][offset]

    def write_frame(self, frame_idx: int, data: bytes | bytearray, pid: int, page: int):
        """Copia data (exatamente PAGE_SIZE bytes) para o frame e registra o dono."""
        self.frames[frame_idx][:] = data[:PAGE_SIZE]
        self.frame_owner[frame_idx] = (pid, page)

    # ── controle de frames livres ─────────────────────────────────────────────

    def free_frames(self) -> list[int]:
        """Retorna índices dos frames ainda não ocupados."""
        return [i for i, owner in enumerate(self.frame_owner) if owner is None]

    def free_frame(self, frame_idx: int):
        """Marca um frame como livre (sem apagar os bytes – economiza CPU)."""
        self.frame_owner[frame_idx] = None

    # ── diagnóstico ──────────────────────────────────────────────────────────

    def dump(self) -> str:
        lines = [f"{'FRAME':<6} {'DONO':<22} {'PRIMEIROS 16 BYTES (hex)'}"]
        lines.append("─" * 60)
        for i, (frame, owner) in enumerate(zip(self.frames, self.frame_owner)):
            owner_str = f"PID={owner[0]} PAG={owner[1]}" if owner else "LIVRE"
            hex_preview = " ".join(f"{b:02X}" for b in frame[:16])
            lines.append(f"  {i:<4} {owner_str:<22} {hex_preview}")
        return "\n".join(lines)
