# Firmware for the Piezo Insulin Pump v2 Rev B board

> **BENCH-ONLY PROTOTYPE.** Water or 0.9 % saline only. Never connect to a person or an animal. Never use insulin.
> **Not validated on hardware.** Nothing here has run on an STM32. See "Status" before relying on any of it.

Two firmwares, one per MCU on the board (`hardware/kicad/`):

| MCU | Role | Code |
| --- | --- | --- |
| STM32WBA55CGU6 (main) | dosing, PMD401 SPI, encoder, BLE commands, battery, charger, heartbeat | `main_wba55/` |
| STM32C031C6 (supervisor) | can only STOP: 48 V veto, PMD401 park, own encoder count, heartbeat watchdog | `supervisor_c031/` |

Both are plain C11 behind a hardware boundary (decision K-16, requirement F-01): `main_wba55/app/pump_port.h` and `supervisor_c031/app/sup_port.h`. The same application code runs on the PC simulator (`host_test/`) and, through `port/*.c`, on the STM32 HAL.

## Status (what has and has not been checked)

| Check | Result |
| --- | --- |
| Host build, gcc `-std=c11 -Wall -Wextra -Werror -Wshadow -Wconversion` | clean |
| Host tests (`make -C firmware/host_test`): both firmwares against an ASSUMED plant model | **21 / 21 pass** (list below) |
| Target compile, `arm-none-eabi-gcc` 13.2, Cortex-M33 / Cortex-M0+, against ST's HAL headers (`sh firmware/target_compile_check.sh`) | clean, `-Werror` |
| Linked target image | **not built**: needs the CubeMX-generated project (clock tree, `MX_*_Init`, startup file), see below |
| BLE GATT service | **not written**: must be generated with the STM32CubeWBA BLE middleware; the command layer it calls is done |
| Run on hardware | **no** |

## Architecture

```
main_wba55/app/            (portable C11)
  pump_config.h            every constant with its source (DECIDED / DS / CALC / ASSUMED / MEASURE)
  pump_port.h              hardware boundary
  pump_app.c               top level: battery (S-13), charger, basal scheduler, BLE command dispatch, log
  dose_ctrl.c              dose state machine, closed-loop position control, supervisor link (main side)
  dose_limits.c            S-05 limits + rolling-hour ledger + calibration (hardened, F-03)
  load_est.c               sensorless occlusion and stall detection from step length (K-13)
  pmd401.c                 SPI rate word, RS-485 servo-mode check (never sends run/stop over RS-485)
  charger.c                BQ25188 (I2C 0x6A): 4.20 V, charge current, watchdog service
  ble_cmd.c                command packets: secure link + CRC + strictly increasing counter (C-02, C-03)
  hardened.h               complement-stored values, jittered double checks, control-flow counter
main_wba55/port/port_stm32wba.c   HAL implementation + pump_main_init()/pump_main_poll()
supervisor_c031/app/sup_logic.c   supervisor state machine (portable)
supervisor_c031/port/port_stm32c0.c HAL implementation + sup_main_init()/sup_main_poll()
common/link_proto.[ch]     MCU-to-MCU frame format, CRC-16
host_test/                 plant model, simulated ports, test suite, Makefile
```

### One dose, step by step

| Main MCU state | Main does | Supervisor does |
| --- | --- | --- |
| IDLE | limits check (0.05–10 U, 15 U per rolling hour, battery > 3.4 V) | SAFE: veto ON, parked |
| REQUEST | sends dose id + encoder counts | checks its own limits (bolus, its own rolling-hour count) → GRANTED: veto OFF |
| RAIL_UP | drives MCU_48V_EN; waits FLY_PGOOD (soft start ~0.1 s); enables SPI pins; polls `X0Y13` over RS-485 until the PMD401 answers `3` (servo mode) | GRANTED |
| UNPARK_REQ | waits READY low + 80 ms | RUN: AEN released (unparked) |
| MOVE | 1 kHz loop: SPI rate word toward the absolute target, ≤ 15 steps/s, slowing near the target, one-sided; occlusion / stall / PGOOD / READY / FAULT / timeout checks | counts encoder: trips on > 30 counts per 10 ms, over-travel, reverse travel, timeout |
| SETTLE | rate 0 for 50 ms; checks delivered counts within ±1 % or ±4 counts (D-10) | RUN |
| PARKING | rate 0; after 300 ms drops MCU_48V_EN | parks at once, veto ON after 300 ms → SAFE |

Any fault: rate 0, rail off, state FAULT (latched). Any supervisor trip: veto ON + parked, latched; it clears only when the main MCU asks, is IDLE, and the encoder has been still for 1 s.

Heartbeat: one frame from the main MCU every 20 ms with a sequence number that must advance (a changing token, F-09). The supervisor answers each valid frame. No valid frame for 100 ms in GRANTED or RUN → trip. The main MCU refuses to start a dose without a live supervisor reply.

## Host test results (assumed plant, not hardware)

```
make -C firmware/host_test
```

| Check (validation plan ID) | Result in simulation |
| --- | --- |
| FW-04/DA-05 40 × 0.05 U | 20.0000 µL of 20 µL; every pulse within 1 count of target; max rate 14.97 Hz |
| FW-04 5 U bolus | 4.9999 U in 56 s |
| FW-04 step length 2 µm and 8 µm | 0.9999 U each |
| FT-07 SPI scale ±27 % | 0.9999 U each; **at +27 % the motor runs 19 Hz, above the 15 Hz cap** |
| OC-02 blocked line | occlusion alarm after 0.220 U, 1.10 bar (825 mmHg) |
| FT-11 bad sizes, 16th unit in the hour | all refused |
| BL-02/03/04 insecure, replayed, altered commands | all refused |
| FT-12 bit flips in limits and in the target | detected, dosing locked |
| FT-01 main MCU halted mid-bolus | motor stops in 11 ms (PMD401 SPI timeout); supervisor trips at 99 ms; 7 counts extra |
| FT-04 heartbeat wire cut | both sides stop within 100 ms; 70 counts extra |
| FT-03/SG-03 dead supervisor | no 48 V, no motion |
| FT-02 runaway with live heartbeat | supervisor detects in 2 ms, **but 0.57 U extra is delivered (> 0.5 U)** |
| BT-02 low battery | refused at 3.35 V; dose in progress at 3.39 V ends cleanly |
| MT-01 PMD401 not in servo mode | refused, no motion |
| FT-13 PMD401 FAULT | stops; supervisor trips |
| FT-05 encoder lost | stops within 0.032 U (reported as occlusion: a frozen encoder looks like zero step length) |
| SG-07 latch and clear | latched until cleared on purpose, then a new dose works |
| S-07 rod moved while parked | supervisor trips |
| DA-06 basal 1 U/h | 21 pulses, 1.0499 U |

## Known limitations (read before bench use)

1. **Runaway (S-06, open item U-03).** If the main MCU's logic is corrupted but its heartbeat keeps running, the supervisor detects over-speed within about 2 ms. It can only remove 48 V and park the motor, though, and the motor keeps stepping until the rail sags or parking completes. The simulation gives 0.57 U extra, against a 0.5 U limit. Firmware cannot close this gap; it needs a hardware gate on the SPI path.
2. **The speed cap depends on the unmeasured SPI scale.** The PMD401 manual gives no scale for the 16-bit word. The firmware assumes +32767 = 1500 Hz (`CFG_PMD_SPI_FULLSCALE`). Measure it (MT-03) before trusting the 15 steps/s cap.
3. **Occlusion threshold is a placeholder.** `CFG_OCC_RATIO_PERMILLE` (60 % of the no-load step) must come from the measured step-length-against-load curve (MT-05, OC-05). Set the no-load step per motor with `le_set_noload_nm()` (MT-04).
4. **No persistence.** Calibration (D-14), the rolling-hour ledger and the event log (F-08) live in RAM, so a reset clears the hour count. Writing them to flash with a CRC is still to do.
5. **No boot self-test** (flash CRC, RAM test, clock check, FW-09) yet.
6. **BLE integrity.** The packet CRC detects corruption, not tampering. Protection against an attacker relies on LE Secure Connections encryption. An application-level MAC (C-03) is open.
7. **PMD401 boot time is unknown** (MT-07). The firmware polls `X0Y13` for up to 5 s after the rail comes up, so each dose may take several seconds to start.

## Values to measure on the bench, then set

| Constant | File | Check |
| --- | --- | --- |
| `CFG_PMD_SPI_FULLSCALE` | pump_config.h | MT-03 |
| no-load step (`le_set_noload_nm`) | load_est.c | MT-04 |
| `CFG_OCC_RATIO_PERMILLE` | pump_config.h | MT-05, OC-05 |
| `CFG_COUNTS_PER_U_X10` | pump_config.h | DA-02 (weigh 5 × 10 U) |
| `CFG_PMD_BOOT_TIMEOUT_MS` | pump_config.h | MT-07 |
| `CFG_CHG_ICHG_MA` | pump_config.h | owner decision B.19 (cell rating) |
| PMD401 pull-up rail | hardware | IF-02, before connecting any signal |

## CubeMX set-up, main MCU (STM32WBA55CGUx, UFQFPN48)

Generate a STM32CubeWBA project, configure as below, then call `pump_main_init()` in `USER CODE BEGIN 2` and `pump_main_poll()` in the main loop, next to the BLE sequencer. Add `firmware/main_wba55/app/*.c`, `firmware/common/link_proto.c` and `firmware/main_wba55/port/port_stm32wba.c` to the build.

| Peripheral | Pins | Settings |
| --- | --- | --- |
| SPI3 | PA0 SCK, PB8 MOSI, PA5 NSS | Transmit-only master, 16-bit, CPOL high, CPHA 2nd edge (mode 3), ≤ 500 kbit/s, hardware NSS output with NSS pulse |
| TIM2 | PB6 CH1, PA8 CH2 | Encoder mode TI1 and TI2, period 0xFFFFFFFF (TIM2 is 32-bit per ST's device header) |
| USART2 | PB0 TX, PA11 RX, PB1 DE | 115200 8N1, RS-485 hardware flow control (DE active high), global interrupt on |
| LPUART1 | PB5 TX, PA1 RX | 115200 8N1, interrupt on |
| USART1 | PB12 TX | 115200 8N1, TX only |
| I2C3 | PA6 SCL, PA7 SDA | 100 kHz (board has 10 kΩ pull-ups) |
| ADC4 | PB9 (IN10), VREFINT | 12-bit, common sampling time 1 ≥ 39.5 cycles |
| GPIO out | PB7 MCU_48V_EN (initial **LOW**), PB2 LED | push-pull |
| GPIO in | PA12 FLY_PGOOD, PB15 READY, PB4 FAULT, PA2 CHG_INT_N | no pull (board resistors) |
| IWDG | – | about 50 ms timeout |
| RNG | – | enabled |
| Clocks | HSE 32 MHz (NX1612SA, internal load trim), LSE 32.768 kHz | per AN5948; SMPS on, VDDRFPA on VDD11 (TX ≈ +3 dBm) |
| BLE | – | custom service: one write characteristic (11-byte command) that calls `pump_app_ble_rx()`; one notify characteristic for the 8-byte reply. Security: LE Secure Connections, bonding, MITM; call `pump_ble_set_secure()` on encryption change |
| Option bytes | – | brown-out reset enabled (F-07); read-out protection on Rev B (C-06) |

## CubeMX set-up, supervisor (STM32C031C6Tx, LQFP48)

Call `sup_main_init()` in `USER CODE BEGIN 2` and `sup_main_poll()` in the main loop. Add `firmware/supervisor_c031/app/sup_logic.c`, `firmware/common/link_proto.c` and `firmware/supervisor_c031/port/port_stm32c0.c`.

| Peripheral | Pins | Settings |
| --- | --- | --- |
| GPIO out | PB0 SUP_VETO, PB1 SUP_PARK | push-pull, **initial level HIGH** (veto on, parked) |
| GPIO out | PB2 LED | push-pull |
| TIM3 | PA6 CH1, PA7 CH2 | Encoder mode TI1 and TI2, period 0xFFFF |
| USART2 | PA2 TX, PA3 RX | 115200 8N1, interrupt on |
| USART1 | PA9 TX, PA10 RX | 115200 8N1 console |
| IWDG | – | about 50 ms timeout |
| Clock | HSI48 | 48 MHz system clock |
| Option bytes | – | brown-out reset enabled |
