@unnumbered References

Datasheets and application notes are cited at the revision recorded in the project. Where a field is not recorded in the project files, it is marked as such and has not been guessed.

[1] R. N. Bergman, Y. Z. Ider, C. R. Bowden and C. Cobelli, "Quantitative estimation of insulin sensitivity," *American Journal of Physiology – Endocrinology and Metabolism*, vol. 236, no. 6, pp. E667–E677, 1979.

[2] Kaçar, Özer and Taşçıoğlu, paper on a piezoelectric valveless micropump simulated in COMSOL and Simulink with PID control of a Bergman-model plant, *Proc. International Conference on Advanced Technologies (ICAT'19)*, 2019. [Full author initials, title and pages to be completed from the copy studied in the project on 21 Sep 2026.]

[3] Texas Instruments, LM5155 / LM51551 boost, SEPIC and flyback controller, datasheet SNVSB75E, Aug. 2023. (`docs/datasheets/lm51551.pdf`)

[4] Texas Instruments, BQ25188 1-cell battery charger, datasheet SLUSFJ3, Nov. 2024. (`docs/datasheets/bq25188.pdf`)

[5] Texas Instruments, TPS62840 step-down converter, datasheet SLVSEC6D, Mar. 2020. (`docs/datasheets/tps62840.pdf`)

[6] PiezoMotor Uppsala AB, "PMD401 Technical Manual," document 150025-01. (`docs/datasheets/PMD401_150025_Technical_Manual.pdf`)

[7] IEC 60601-2-24:2012, *Medical electrical equipment – Part 2-24: Particular requirements for the basic safety and essential performance of infusion pumps and controllers*, ed. 2.0, International Electrotechnical Commission, 2012.

[8] ISO 14971:2019, *Medical devices – Application of risk management to medical devices*, International Organization for Standardization, 2019.

[9] IEC 62304:2006+A1:2015, *Medical device software – Software life cycle processes*, International Electrotechnical Commission.

[10] MISRA C:2025, *Guidelines for the use of the C language in critical systems*, The MISRA Consortium, 2025.

[11] Bluetooth SIG, *Insulin Delivery Service*, specification v1.0.1.

[12] STMicroelectronics, STM32WBA55 datasheet DS14127; reference manual RM0493; errata sheet ES0592; application notes AN6373 (power supply / SMPS design guidance as cited in ECO1) and AN5948 (hardware getting started, crystals); MLPF-WB-04D3 datasheet DS14446; NUCLEO-WBA55CG user manual UM3301 and board schematic MB1803. [Revision letters not recorded in the project.]

[13] STMicroelectronics, STM32C031C6 datasheet. [Not read in the project; decoupling values assumed.]

[14] Coilcraft, HPH6 series six-winding coupled inductors, Document 613 (revision 11/23/21).

[15] Alpha and Omega Semiconductor, AONR34332C 30 V N-channel MOSFET datasheet, rev. 2.0. (`docs/datasheets/AONR34332C.pdf`, cited in the handover documents)

[16] Nexperia, PNE20010ER 200 V hyperfast rectifier; PMEG10020ELR 100 V Schottky rectifier; BSS138P N-channel MOSFET; PESD5V0S1BA ESD protection diode – datasheets and product data. (`docs/datasheets/`)

[17] Texas Instruments, CSD16340Q3 25 V N-channel NexFET datasheet. (`docs/datasheets/csd16340q3.pdf`)

[18] Vishay, BZX84B51-E3-08 zener diode, and Littelfuse SMAJ15A TVS diode – distributor data as recorded in `scripts/design.py`. [Manufacturer datasheets not retrieved.]

[19] Murata, DFE201612E and LQM21PN2R2MGH power inductors, LQG15HS10NJ02D RF inductor, GRM-series capacitors; NDK NX1612SA and NX1610SE crystals; Taiyo Yuden LSMGA160808T470RG ferrite bead – manufacturer part data as recorded in `scripts/design.py`.

[20] PiezoMotor, "Piezo LEGS Linear LL06" product page and data, https://piezomotor.com/linear-direct-drive-piezo-actuators/legs-linear-ll06-piezo-motor/ (link recorded 29–30 Sep 2026).

[21] Analog Devices, DC2628A demo manual (LT8362); Pololu, U3V70x step-up regulator family; Microchip MCP1700; Molicel INR18650-P28A – as recorded in `requirements/COMPONENTS_AND_BOM.md`.

[22] IPC-2221C, *Generic Standard on Printed Board Design*, 2023; IPC-2152, *Standard for Determining Current-Carrying Capacity in Printed Board Design*; IPC-7351, *Generic Requirements for Surface Mount Design and Land Pattern Standard*.

[23] AAMI TIR101, *Fluid delivery performance testing for infusion pumps*; ISO 8655-6, *Piston-operated volumetric apparatus – Gravimetric methods*.

[24] KiCad EDA 10.0.3 (kicad-cli); Analog Devices LTspice 26.1.1; ngspice 42; Freerouting 2.1.0; STMicroelectronics STM32CubeMX 6.18.1 – software used for design and verification.

[25] Project repository BigBiglinn/INSULIN_PUMP: `requirements/`, `decisions/DECISION_LOG.md`, `docs/handover/`, `docs/review/INDEPENDENT_DESIGN_REVIEW.md`, `validation/` – primary record of all design data and results in this report.

[26] "Technical and Clinical Architecture of Modern Insulin Infusion Pumps," background note uploaded to the project on 4 Aug 2026 (author not recorded). Background only.
