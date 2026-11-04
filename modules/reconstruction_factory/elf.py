"""Minimal big-endian ELF32 reader: sections, symbols, RELA entries. No third-party dependency."""
import struct

R_NAMES = {1: "R_PPC_ADDR32", 2: "R_PPC_ADDR24", 3: "R_PPC_ADDR16", 4: "R_PPC_ADDR16_LO", 5: "R_PPC_ADDR16_HI", 6: "R_PPC_ADDR16_HA",
           7: "R_PPC_ADDR14", 10: "R_PPC_REL24", 11: "R_PPC_REL14", 26: "R_PPC_REL32", 109: "R_PPC_EMB_SDA21", 4 + 1000: "?"}
# relocation type -> (kind, mask) : "half" masks 2 bytes at the reloc offset; "word" masks bits of the 4-byte word at the offset
_MASK = {1: ("word", 0xFFFFFFFF), 2: ("word", 0x03FFFFFC), 3: ("half", 0xFFFF), 4: ("half", 0xFFFF), 5: ("half", 0xFFFF), 6: ("half", 0xFFFF),
         7: ("word", 0xFFFC), 8: ("word", 0xFFFC), 9: ("word", 0xFFFC), 10: ("word", 0x03FFFFFC), 11: ("word", 0xFFFC), 12: ("word", 0xFFFC),
         13: ("word", 0xFFFC), 26: ("word", 0xFFFFFFFF), 109: ("word", 0x001FFFFF)}


class ElfError(ValueError):
    pass


class Elf:
    def __init__(self, data):
        if data[:4] != b"\x7fELF" or data[4] != 1 or data[5] != 2:
            raise ElfError("not a big-endian ELF32 object")
        self.data = data
        (_, self.machine, _, _, _, shoff, _, _, _, _, shentsize, shnum, shstrndx) = struct.unpack(">HHIIIIIHHHHHH", data[16:52])
        self.sections = []
        for i in range(shnum):
            o = shoff + i * shentsize
            n, t, fl, addr, off, size, link, info, align, entsize = struct.unpack(">IIIIIIIIII", data[o:o + 40])
            self.sections.append({"i": i, "name_off": n, "type": t, "flags": fl, "off": off, "size": size, "link": link, "info": info, "entsize": entsize})
        strtab = self.sections[shstrndx]
        for s in self.sections:
            s["name"] = self._cstr(strtab["off"], s["name_off"])
        self.symbols = []
        for s in self.sections:
            if s["type"] == 2:
                st = self.sections[s["link"]]
                for k in range(s["size"] // 16):
                    n, value, size, info, other, shndx = struct.unpack(">IIIBBH", data[s["off"] + k * 16:s["off"] + k * 16 + 16])
                    self.symbols.append({"name": self._cstr(st["off"], n), "value": value, "size": size, "bind": info >> 4, "type": info & 15, "shndx": shndx})
        self.relocs = {}                       # section index -> [(offset, type, sym index, addend)]
        for s in self.sections:
            if s["type"] == 4:
                lst = []
                for k in range(s["size"] // 12):
                    off, info, add = struct.unpack(">IIi", data[s["off"] + k * 12:s["off"] + k * 12 + 12])
                    lst.append((off, info & 255, info >> 8, add))
                self.relocs[s["info"]] = lst

    def _cstr(self, base, off):
        end = self.data.index(b"\0", base + off)
        return self.data[base + off:end].decode("ascii", "replace")

    def section(self, name):
        for s in self.sections:
            if s["name"] == name:
                return s
        return None

    def section_bytes(self, s):
        return b"" if s["type"] == 8 else self.data[s["off"]:s["off"] + s["size"]]

    def symbol(self, name):
        for s in self.symbols:
            if s["name"] == name and s["shndx"] not in (0,):
                return s
        return None

    def defined_function_symbols(self):
        return [s for s in self.symbols if s["type"] == 2 and s["shndx"] not in (0, 0xFFF1) and s["bind"] in (1, 2)]

    def extent(self, symname):
        """(section dict, offset, size) the symbol covers, or None. A zero-size symbol covers the rest of its section."""
        s = self.symbol(symname)
        if s is None or s["shndx"] >= len(self.sections):
            return None
        sec = self.sections[s["shndx"]]
        size = s["size"] or (sec["size"] - s["value"])
        return sec, s["value"], size

    def sym_identity(self, idx):
        """Stable identity of a relocation target: an undefined/global symbol by name, a section symbol by section name."""
        s = self.symbols[idx]
        if s["type"] == 3 and 0 < s["shndx"] < len(self.sections):
            return "sec:" + self.sections[s["shndx"]]["name"]
        return s["name"]

    def masked(self, sec, off, size):
        """Bytes of [off, off+size) of a section with the bit fields its relocations cover cleared. -> (bytes, unknown relocation types)."""
        b = bytearray(self.section_bytes(sec)[off:off + size])
        unknown = []
        for (ro, rt, _si, _ad) in self.relocs.get(sec["i"], []):
            if not (off <= ro < off + size):
                continue
            m = _MASK.get(rt)
            if m is None:
                unknown.append(rt)
                continue
            p = ro - off
            if m[0] == "half":
                b[p:p + 2] = b"\0\0"
            else:
                w = struct.unpack(">I", bytes(b[p:p + 4]))[0] & ~m[1] & 0xFFFFFFFF
                b[p:p + 4] = struct.pack(">I", w)
        return bytes(b), unknown

    def reloc_rows(self, sec, off, size):
        return sorted((ro - off, rt, self.sym_identity(si), ad) for (ro, rt, si, ad) in self.relocs.get(sec["i"], []) if off <= ro < off + size)
