"""
Processo leve (thread): tem um PID, um tamanho (1 byte … 1 MB) e um "arquivo"
que simula seus dados em disco, usado quando uma página precisa ser carregada.

O conteúdo de cada página é gerado deterministicamente a partir do PID e do
número de página, de forma que ao exibir um byte qualquer seja possível
identificar claramente a qual processo ele pertence.
"""

import random
from constants import VIRT_MEM_SIZE, PAGE_SIZE


class Process:
    def __init__(self, pid: int, size: int | None = None, seed: int | None = None):
        rng = random.Random(seed if seed is not None else pid)

        # Tamanho em bytes: entre 1 byte e 1 MB (limitado ao espaço virtual)
        if size is None:
            size = rng.randint(1, VIRT_MEM_SIZE)
        self.size: int = max(1, min(size, VIRT_MEM_SIZE))
        self.pid: int = pid

        # Número de páginas que este processo efetivamente usa
        self.num_pages: int = (self.size + PAGE_SIZE - 1) // PAGE_SIZE

        # "Disco": dict page_no -> bytearray(PAGE_SIZE)
        # Gerado sob demanda para economizar memória real do simulador
        self._disk_cache: dict[int, bytearray] = {}
        self._rng = random.Random(seed if seed is not None else pid)

    # ── acesso ao "disco" ──────────────────────────────────────────────────

    def get_page_from_disk(self, page_no: int) -> bytearray:
        """Retorna os bytes da página 'page_no' como se lesse do disco."""
        if page_no not in self._disk_cache:
            rng = random.Random(self.pid * 10_000 + page_no)
            data = bytearray(rng.getrandbits(8) for _ in range(PAGE_SIZE))
            # Marca os primeiros bytes com PID e número de página (legibilidade)
            data[0] = self.pid & 0xFF
            data[1] = page_no & 0xFF
            self._disk_cache[page_no] = data
        return self._disk_cache[page_no]

    def valid_page(self, page_no: int) -> bool:
        return 0 <= page_no < self.num_pages

    def __repr__(self):
        return (f"Process(pid={self.pid}, size={self.size} bytes, "
                f"pages={self.num_pages})")
