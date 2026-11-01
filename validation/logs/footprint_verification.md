# Footprint verification against manufacturer drawings (1 Nov 2026)

Method: the land-pattern pages of the datasheets in `docs/datasheets/` were rendered (the drawings are vector
graphics, not extractable as text) and compared with the pad geometry of the **placed** footprints in
`hardware/kicad/pump_v2.kicad_pcb`, as extracted by script. Dimensions in mm, footprint frame, top view.

| Ref | Part / package | Manufacturer drawing | Board footprint | Result |
| --- | --- | --- | --- | --- |
| U101 | BQ25188 YBG0008-C01 DSBGA-8 | SLUSFJ3 §13.1 pp. 50–52: 2 × 4 balls, 0.4 pitch, A1 top-left; Ø0.23 metal NSMD (mask ≤ +0.05); paste 0.25 square R0.05 | Before: Ø0.20, SMD mask, paste = pad. **After 1 Nov: Ø0.23, mask +0.05, paste 0.25 square R0.05**; ball map = Table 5-1 | **Verified, corrected** (`scripts/fix_ybg_footprint.py`) |
| U301 | LM51551 DSS0012B WSON-12 | SNVSB75E p. 46: 12 × 0.5 × 0.25 pads, 0.5 pitch, row centres 1.9 apart; EP 1 × 2.65; pin 1 top-left, 6 bottom-left, 7 bottom-right, 12 top-right | 0.5 × 0.25 at x ±0.95, y −1.25…1.25; EP 1 × 2.65; same pin order | **Verified, matches** |
| U201 | TPS62840 DLC0008B VSON-HR-8 | SLVSEC6D p. 37: 8 × 0.6 × 0.25 pads, 0.5 pitch, row centres 1.3 apart (x ±0.65); pin 1 top-left, 4 bottom-left, 5 bottom-right, 8 top-right | KiCad `Texas_VSON-HR-8_1.5x2mm_P0.5mm`: 0.8 × 0.25 at x ±0.725 (land spans 0.325–1.125 vs TI 0.35–0.95) | **Pin order and pitch verified. Accepted deviation:** 0.175 mm longer toe; heel gap 0.65 vs 0.70 mm. Covers TI's lands entirely; not changed, to avoid disturbing routed copper. Revisit with the fab's DFM check |
| D301 | PNE20010ER CFP3 (SOD123W) | Nexperia Fig. 16: lands 1.2 × 1.2, centres 2.8 apart, paste 1.1 × 1.1, stencil 0.1; pin 1 = cathode | 1.2 × 1.2 at x ±1.4; paste = pad (1.2); pin 1 on +48V_RAW (cathode) | **Verified**; paste 0.05 mm per side larger than recommended (minor) |
| D302 | PMEG10020ELR CFP3 (SOD123W) | Nexperia Fig. 17: same as D301; pin 1 = cathode | Same footprint; pin 1 = FLY_CLAMP (cathode) | **Verified**; paste as D301 |
| Q301 | CSD16340Q3 (Q3, SON 3.3 × 3.3) | SLPS247E §7.2 | Matches within 5 µm (final engineering review) | Verified, **but the part is rejected** (U-41); the replacement needs its own check |

Not verified (no drawing in the repository): STM32WBA55 UFQFPN48, STM32C031 LQFP48, MAX3485 SOIC-8, JST SH
connectors, XT30, USB4125, U.FL, F101 fuse, TVS D701–D709, crystals, T301 (placeholder), BSS138 SOT-23
(Nexperia BSS138P datasheet is in the repo; SOT-23 is a standard KiCad footprint, not compared here).
