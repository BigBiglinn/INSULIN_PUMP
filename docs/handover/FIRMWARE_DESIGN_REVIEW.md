# Embedded system design review (Phase D), 1 Nov 2026

**No firmware exists in this repository.** The owner writes the firmware (K-16). A reference implementation exists outside the repository. Everything below is a review of the **requirements and the hardware interfaces** against the firmware that will need to exist. Nothing here has been implemented or tested.

## 1. Principle: firmware is never the only protection

| Hazard | Firmware layer (main MCU) | Independent layer | Hardware layer | Status of the independent layers |
| --- | --- | --- | --- | --- |
| Over-dose by runaway speed | Speed cap 15 steps/s (D-08); dose limits (S-05) | Supervisor TIM3 rate check | SPI gate on PMD_SS (proposed); PMD401 SPI timeout (about 10 ms); 48 V veto (R403 pull-up); park (R405 pull-up) | Veto and park are **designed**. The SPI gate and supervisor firmware are **proposals** (approval sheet decision 2) |
| 48 V over-voltage | — | Supervisor ADC monitor (proposed) | LM51551 FB OVP; independent comparator (proposed) | FB OVP designed; independent OVP **proposed** (decision 1) |
| Main MCU hang | IWDG | Heartbeat loss → supervisor veto and park | R401 pull-down on FLY_EN (48 V off when the main MCU is in reset) | Designed (hardware); firmware not written |
| Supervisor hang | — | Main MCU heartbeat check | Veto and park default **on** through pull-ups when the supervisor is in reset (IWDG) | Designed; IWDG period to be set ≤ 10 ms (`runaway_timing.py`; supervisor hang plus runaway is a double fault) |
| Low battery | Stop dosing at 3.4 V (S-13) | **None today**: the supervisor has no VBAT input | — | Gap: approval sheet decision 14 |

So, by design, a fault in the main MCU firmware alone cannot keep the motor running **once the SPI gate (decision 2) exists**. Today the only motor stops independent of the main MCU are the veto, which removes 48 V with a stop time limited by stored rail energy (`runaway_timing.py`: 23–87 ms at 15 mm/s), and park (250 ms). These are too slow for S-06 at full speed.

## 2. Review by function

| Function | Hardware provided | Firmware required | Findings |
| --- | --- | --- | --- |
| Dosing control | SPI3 to PMD401 servo mode (16-bit speed); TIM2 encoder (A/B/I); Ready/Fault inputs | Position loop on the encoder; dose state machine IDLE → UNPARK → MOVE → SETTLE → IDLE, FAULT from every state (F-02) | **New requirement FW-R1:** ramp PMD401 speed changes over ≥ 20 ms. A 100 mA load step below about 4 V trips the LM51551 hiccup; the same demand as a 20 ms ramp does not (report §27, simulation only) |
| Startup sequence | FLY_EN (PB7), FLY_PGOOD (PA12, still unrouted), veto and park from the supervisor | Supervisor releases the veto only after the heartbeat is valid. Main MCU enables 48 V, **waits for FLY_PGOOD**, then unparks | **New:** the 48 V soft start is now about 220 ms (C305 2.2 µF). Firmware must wait ≥ 300 ms or for PGOOD, never a fixed short delay, and must keep the PMD401 parked (idle load) until PGOOD: starting into a full 100 mA load at 3.0 V trips hiccup at the end of the soft start [SIM switching model] |
| Shutdown sequence | Speed 0 → park → FLY_EN low → veto | Order as in the report §23 sequence diagram | E-11 discharge needs the bleeder (decision 3) |
| PMD401 SPI | Mode 3, ≤ 500 kbit/s (manual) | Send a speed word every < 10 ms while moving, and none when stopped | The SPI timeout is the stop mechanism, so the main MCU must not send keep-alive frames when it intends to stop |
| Encoder | TIM2 (main), TIM3 (supervisor), both from the same encoder | 32-bit position extension; plausibility check of commanded against measured travel | An encoder failure defeats both counts; plausibility check is required (S-07) |
| Fault detection | PMD_FAULT, PMD_READY, FLY_PGOOD, CHG_INT_N | Map each to FAULT | FLY_PGOOD, PMD_READY_M and CHG_INT_N are still unrouted (U501 fan-out) |
| Battery monitoring | VBAT/2 into PB9 (ADC4_IN10), τ 50 ms | Sample ≤ a few Hz; low-voltage stop 3.4 V (S-13); ADC leakage check (A-27) | Supervisor copy missing (decision 14) |
| Charger | I²C3 to BQ25188; INT | Set ICHG (default 10 mA) and kick the I²C watchdog | Charge current is a firmware setting (decision 13) |
| Supervisor communication | LPUART1 ↔ USART2 heartbeat | Changing token, timeout → veto and park (F-09) | — |
| Watchdogs | — | IWDG and brown-out reset on both MCUs (F-07) | Supervisor IWDG ≤ 10 ms recommended |
| BLE | WBA55 radio, U.FL | LE Secure Connections, bonded; every command carries a counter and check value (C-02, C-03) | RF hardware blocked on ST documents |
| Error handling | — | Hardened values and control-flow counter (F-03); FAULT latches until power cycle | — |

## 3. Not implemented and not tested (complete list)

- All main MCU firmware: dosing, BLE, SPI, encoder, charger, ADC, heartbeat, fault handling.
- All supervisor firmware: heartbeat, rate check, veto, park, latch, IWDG.
- The SPI gate hardware it would control.
- Any hardware-in-the-loop or bench test (VALIDATION_PLAN groups SG, MT, DA).
