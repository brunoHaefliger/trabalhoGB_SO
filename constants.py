# ─────────────────────────────────────────────
#  Parâmetros fixos do sistema fictício
# ─────────────────────────────────────────────

PHYS_MEM_SIZE  = 64  * 1024        # 64 KB  = 65 536 bytes
VIRT_MEM_SIZE  = 1024 * 1024       # 1 MB   = 1 048 576 bytes
PAGE_SIZE      = 8  * 1024         # 8 KB   = 8 192 bytes

NUM_FRAMES     = PHYS_MEM_SIZE // PAGE_SIZE   # 8 frames
NUM_PAGES      = VIRT_MEM_SIZE  // PAGE_SIZE  # 128 páginas virtuais

OFFSET_BITS    = 13                # 2^13 = 8 192  →  13 bits de offset
OFFSET_MASK    = PAGE_SIZE - 1     # 0x1FFF  (máscara para extrair offset)
