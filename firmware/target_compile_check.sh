#!/bin/sh
# Compile-check both firmwares for their real targets against ST's HAL headers (no linking: the
# CubeMX-generated init code and startup files are not in this repository yet).
# Needs: arm-none-eabi-gcc, git, network access to github.com.  Usage: sh firmware/target_compile_check.sh
set -e
cd "$(dirname "$0")"
C=${ST_CACHE:-/tmp/st_hal_cache}
mkdir -p "$C"
for r in stm32wbaxx-hal-driver cmsis-device-wba stm32c0xx-hal-driver cmsis-device-c0 cmsis-core; do
  [ -d "$C/$r" ] || git clone -q --depth 1 "https://github.com/STMicroelectronics/$r.git" "$C/$r"
done
B="$C/build"; mkdir -p "$B/wba" "$B/c0"
cp "$C/stm32wbaxx-hal-driver/Inc/stm32wbaxx_hal_conf_template.h" "$B/wba/stm32wbaxx_hal_conf.h"
cp "$C/stm32c0xx-hal-driver/Inc/stm32c0xx_hal_conf_template.h" "$B/c0/stm32c0xx_hal_conf.h"
echo '#include "stm32wbaxx_hal.h"' > "$B/wba/main.h"
echo '#include "stm32c0xx_hal.h"' > "$B/c0/main.h"
CORE="$C/cmsis-core/CMSIS/Core/Include"
F="-std=c11 -O2 -Wall -Wextra -Werror -Wshadow -Wconversion -Wno-sign-conversion -mthumb"
for f in main_wba55/port/port_stm32wba.c main_wba55/app/*.c common/link_proto.c; do
  arm-none-eabi-gcc $F -mcpu=cortex-m33 -mfloat-abi=hard -mfpu=fpv5-sp-d16 -DSTM32WBA55xx -DUSE_HAL_DRIVER \
    -I"$B/wba" -I"$C/stm32wbaxx-hal-driver/Inc" -I"$C/cmsis-device-wba/Include" -I"$CORE" -c "$f" -o "$B/wba/$(basename "$f").o"
done
echo "main MCU (STM32WBA55, Cortex-M33): OK"
for f in supervisor_c031/port/port_stm32c0.c supervisor_c031/app/*.c common/link_proto.c; do
  arm-none-eabi-gcc $F -mcpu=cortex-m0plus -DSTM32C031xx -DUSE_HAL_DRIVER \
    -I"$B/c0" -I"$C/stm32c0xx-hal-driver/Inc" -I"$C/cmsis-device-c0/Include" -I"$CORE" -c "$f" -o "$B/c0/$(basename "$f").o"
done
echo "supervisor (STM32C031, Cortex-M0+): OK"
arm-none-eabi-size "$B"/c0/*.o | tail -n +1
