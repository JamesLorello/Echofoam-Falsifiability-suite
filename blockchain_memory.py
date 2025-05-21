import hashlib
import json
import zlib
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Block:
    index: int
    data: bytes
    prev_hash: str
    hash: str

class BlockchainMemory:
    """Simple compressed memory chain with hashed references."""

    def __init__(self, path: str = "memory_chain.json"):
        self.path = path
        self.chain: List[Block] = []
        self.load()

    def _hash_block(self, index: int, data: bytes, prev_hash: str) -> str:
        h = hashlib.sha256()
        h.update(str(index).encode())
        h.update(prev_hash.encode())
        h.update(data)
        return h.hexdigest()

    def add_memory(self, text: str) -> Block:
        """Compress and store text as a new block."""
        compressed = zlib.compress(text.encode())
        prev_hash = self.chain[-1].hash if self.chain else "0" * 64
        index = len(self.chain)
        block_hash = self._hash_block(index, compressed, prev_hash)
        block = Block(index, compressed, prev_hash, block_hash)
        self.chain.append(block)
        self.persist()
        return block

    def get_block(self, block_hash: str) -> Optional[Block]:
        for block in self.chain:
            if block.hash == block_hash:
                return block
        return None

    def persist(self) -> None:
        serial = [
            {
                "index": b.index,
                "data": b.data.hex(),
                "prev_hash": b.prev_hash,
                "hash": b.hash,
            }
            for b in self.chain
        ]
        with open(self.path, "w") as f:
            json.dump(serial, f, indent=2)

    def load(self) -> None:
        try:
            with open(self.path) as f:
                serial = json.load(f)
            self.chain = [
                Block(
                    index=entry["index"],
                    data=bytes.fromhex(entry["data"]),
                    prev_hash=entry["prev_hash"],
                    hash=entry["hash"],
                )
                for entry in serial
            ]
        except FileNotFoundError:
            self.chain = []
