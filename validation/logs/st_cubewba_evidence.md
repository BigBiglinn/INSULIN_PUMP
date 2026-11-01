# STM32WBA55: evidence from ST's public GitHub repositories (1 Nov 2026)

st.com is unreachable from the design environment; raw.githubusercontent.com is reachable. ST publishes its
STM32CubeWBA reference projects and HAL drivers there. These are **ST reference firmware configurations**, not
the datasheet: they show how ST configures its own NUCLEO-WBA55CG board, not the external component values.

| Item | Quoted line | Source |
| --- | --- | --- |
| MCU / package of the reference board | `Mcu.UserName=STM32WBA55CGUx`, `Mcu.Package=UFQFPN48` | `STMicroelectronics/STM32CubeWBA` main, `Projects/NUCLEO-WBA55CG/Applications/BLE/BLE_HeartRate/BLE_HeartRate.ioc` |
| Core supply mode | `RCC.SupplySource=PWR_SMPS_SUPPLY` | same file |
| HSE | `OSC_IN.Mode=HSE-External-Oscillator`, `RCC.HSE_VALUE=32000000`, `RCC.SYSCLKSourceVirtual=RCC_SYSCLKSOURCE_HSE`, `RCC.HseDiv=RCC_HSE_DIV2` | same file |
| LSE | `PC14-OSC32_IN.Mode=LSE-External-Oscillator`, `RCC.RTCClockSelection=RCC_RTCCLKSOURCE_LSE`, `RCC.RSTClockSelectionVirtual=RCC_RADIOSTCLKSOURCE_LSE` | same file |
| Supply options in the HAL | `#define PWR_LDO_SUPPLY (0U)`, `#define PWR_SMPS_SUPPLY PWR_CR3_REGSEL` | `STMicroelectronics/stm32wbaxx-hal-driver` main, `Inc/stm32wbaxx_hal_pwr_ex.h` lines 129-130 |
| HSE load trimming | `@brief Set HSE clock trimming` / `@note user-programmable capacitor trimming value.` / `@rmtoll ECSCR1 HSETRIM` / `Value Between Min_Data = 0 and Max_Data = 63` | same driver, `Inc/stm32wbaxx_ll_rcc.h` lines 950-958 |

**What this supports (classification: reference-design backed, firmware configuration only):**
- SMPS supply mode is ST's own choice on the reference board -> recommended mode for Rev B (decision 1a).
- 32 MHz HSE crystal and a 32.768 kHz LSE crystal used by RTC and the radio sleep timer -> fit Y502 (LSE) rather than leaving it DNP (decision 1c).
- The HSE has on-chip programmable load trimming -> whether C516/C517 are needed must still be read in the datasheet / AN5948.

**What it does not give:** SMPS inductor value and type, VDD11/VDDRF/VDDRFPA decoupling, RF matching/filter network,
crystal part numbers and load capacitance, exposed-pad and RF layout rules. These remain blocked on DS14127 (datasheet),
AN5948, AN6373 and the MB1803 (NUCLEO-WBA55CG) schematic.
