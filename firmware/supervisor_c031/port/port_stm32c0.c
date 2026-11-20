/* sup_port.h on the STM32C031C6 using the ST HAL. Handles come from STM32CubeMX (firmware/README.md,
 * section "CubeMX set-up, supervisor").
 *
 * SAFETY: PB0 (SUP_VETO) and PB1 (SUP_PARK) must be configured in CubeMX with initial output level HIGH.
 * During reset the pins are high-impedance and the board pull-ups R403/R405 hold veto ON and the motor
 * parked; the firmware keeps them HIGH until it has a valid authorisation.
 *
 * Status: compiles against the ST HAL headers (stm32c0xx-hal-driver); NOT run on hardware.
 */
#include "main.h"
#include "../app/sup_port.h"
#include "../app/sup_logic.h"

#include <string.h>

extern TIM_HandleTypeDef htim3;     /* encoder mode TI1+TI2 on PA6/PA7, 16-bit */
extern UART_HandleTypeDef huart2;   /* link to the main MCU: PA2 TX / PA3 RX, 115200 8N1 */
extern UART_HandleTypeDef huart1;   /* console: PA9 TX / PA10 RX */
extern IWDG_HandleTypeDef hiwdg;

uint32_t sport_ms(void) { return HAL_GetTick(); }
void sport_set_veto(bool veto_on) { HAL_GPIO_WritePin(GPIOB, GPIO_PIN_0, veto_on ? GPIO_PIN_SET : GPIO_PIN_RESET); }
void sport_set_parked(bool parked) { HAL_GPIO_WritePin(GPIOB, GPIO_PIN_1, parked ? GPIO_PIN_SET : GPIO_PIN_RESET); }
void sport_led(bool on) { HAL_GPIO_WritePin(GPIOB, GPIO_PIN_2, on ? GPIO_PIN_SET : GPIO_PIN_RESET); }
uint16_t sport_enc_raw16(void) { return (uint16_t)__HAL_TIM_GET_COUNTER(&htim3); }
void sport_wdg_kick(void) { (void)HAL_IWDG_Refresh(&hiwdg); }
void sport_log(const char *s) { (void)HAL_UART_Transmit(&huart1, (const uint8_t *)s, (uint16_t)strlen(s), 5u); }

static volatile uint8_t rx_buf[256];
static volatile uint16_t rx_h, rx_t;
static uint8_t rx_byte, tx_buf[32];

void HAL_UART_RxCpltCallback(UART_HandleTypeDef *h)
{
    if (h == &huart2) {
        uint16_t n = (uint16_t)((rx_h + 1u) & 0xFFu);
        if (n != rx_t) { rx_buf[rx_h] = rx_byte; rx_h = n; }
        (void)HAL_UART_Receive_IT(&huart2, &rx_byte, 1u);
    }
}

void HAL_UART_ErrorCallback(UART_HandleTypeDef *h)
{
    if (h == &huart2) { (void)HAL_UART_Receive_IT(&huart2, &rx_byte, 1u); }
}

void sport_link_send(const uint8_t *p, size_t n)
{
    if (n > sizeof tx_buf || huart2.gState != HAL_UART_STATE_READY) { return; }
    memcpy(tx_buf, p, n);
    (void)HAL_UART_Transmit_IT(&huart2, tx_buf, (uint16_t)n);
}

size_t sport_link_recv(uint8_t *p, size_t max)
{
    size_t n = 0u;
    while (n < max && rx_t != rx_h) { p[n++] = rx_buf[rx_t]; rx_t = (uint16_t)((rx_t + 1u) & 0xFFu); }
    return n;
}

/* Call sup_main_init() in USER CODE BEGIN 2 and sup_main_poll() inside while(1). */
void sup_main_init(void)
{
    sport_set_veto(true);
    sport_set_parked(true);
    (void)HAL_TIM_Encoder_Start(&htim3, TIM_CHANNEL_ALL);
    (void)HAL_UART_Receive_IT(&huart2, &rx_byte, 1u);
    sup_init();
}

void sup_main_poll(void)
{
    static uint32_t last;
    uint32_t now = HAL_GetTick();
    if (now != last) {
        last = now;
        sup_tick();
        sport_led(sup_state() == SST_TRIP ? ((now / 100u) & 1u) != 0u : sup_state() != SST_SAFE);
    }
}
