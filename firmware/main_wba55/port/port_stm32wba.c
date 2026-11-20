/* pump_port.h on the STM32WBA55CGU6 using the ST HAL. Peripheral handles are the ones STM32CubeMX
 * generates from the configuration in firmware/README.md (section "CubeMX set-up, main MCU").
 * Pin map: hardware/kicad (sheet "Main MCU STM32WBA55"), verified against the CubeMX 6.18.1 database.
 *
 * Status: compiles against the ST HAL headers (stm32wbaxx-hal-driver); NOT run on hardware.
 */
#include "main.h"                 /* CubeMX: includes stm32wbaxx_hal.h and the handle declarations */
#include "../app/pump_port.h"
#include "../app/pump_app.h"

#include <string.h>

extern SPI_HandleTypeDef hspi3;     /* PMD401 servo SPI: mode 3, 16-bit, <= 500 kbit/s, HW NSS output (PA5) */
extern TIM_HandleTypeDef htim2;     /* LL06 encoder: TIM2 encoder mode TI1+TI2 on PB6/PA8 */
extern UART_HandleTypeDef huart2;   /* RS-485 set-up link: 115200 8N1, HW DE on PB1 (MAX3485) */
extern UART_HandleTypeDef hlpuart1; /* supervisor link: 115200 8N1, PB5 TX / PA1 RX */
extern UART_HandleTypeDef huart1;   /* console: TX only on PB12 */
extern I2C_HandleTypeDef hi2c3;     /* BQ25188: PA6 SCL / PA7 SDA */
extern ADC_HandleTypeDef hadc4;     /* VBAT_SENSE on ADC4_IN10 (PB9) + VREFINT */
extern IWDG_HandleTypeDef hiwdg;
extern RNG_HandleTypeDef hrng;

/* ------------------------------------------------------------------ GPIO (fixed by the schematic) */
#define EN48_PORT   GPIOB
#define EN48_PIN    GPIO_PIN_7     /* MCU_48V_EN -> R402 1k -> FLY_EN (R401 4.7k pull-down holds it off) */
#define PGOOD_PORT  GPIOA
#define PGOOD_PIN   GPIO_PIN_12    /* FLY_PGOOD (100k pull-up R302) */
#define READY_PORT  GPIOB
#define READY_PIN   GPIO_PIN_15    /* PMD_READY_M via Q701 shifter: LOW = ready */
#define FAULT_PORT  GPIOB
#define FAULT_PIN   GPIO_PIN_4     /* PMD_FAULT_M via Q702 shifter: HIGH = fault */
#define LED_PORT    GPIOB
#define LED_PIN     GPIO_PIN_2

uint32_t port_ms(void) { return HAL_GetTick(); }

void port_set_48v_enable(bool on) { HAL_GPIO_WritePin(EN48_PORT, EN48_PIN, on ? GPIO_PIN_SET : GPIO_PIN_RESET); }
bool port_fly_pgood(void) { return HAL_GPIO_ReadPin(PGOOD_PORT, PGOOD_PIN) == GPIO_PIN_SET; }
bool port_pmd_ready(void) { return HAL_GPIO_ReadPin(READY_PORT, READY_PIN) == GPIO_PIN_RESET; }
bool port_pmd_fault(void) { return HAL_GPIO_ReadPin(FAULT_PORT, FAULT_PIN) == GPIO_PIN_SET; }
void port_led(bool on) { HAL_GPIO_WritePin(LED_PORT, LED_PIN, on ? GPIO_PIN_SET : GPIO_PIN_RESET); }

/* ------------------------------------------------------------------ PMD401 SPI */
/* The SPI3 pins (PA0 SCK, PB8 MOSI, PA5 NSS) are switched between their CubeMX alternate function and
 * analog mode by rewriting only their MODER bits, so no alternate-function number is hard-coded here. */
static uint32_t moder_a_af, moder_b_af;
#define MASK_A ((3u << (0u * 2u)) | (3u << (5u * 2u)))   /* PA0, PA5 */
#define MASK_B (3u << (8u * 2u))                         /* PB8 */

void port_pmd_spi_enable(bool enable)
{
    if (enable) {
        GPIOA->MODER = (GPIOA->MODER & ~MASK_A) | moder_a_af;
        GPIOB->MODER = (GPIOB->MODER & ~MASK_B) | moder_b_af;
    } else {
        GPIOA->MODER |= MASK_A;     /* 11 = analog: no drive into an unpowered PMD401 (ECO2) */
        GPIOB->MODER |= MASK_B;
    }
}

void port_pmd_spi_write(int16_t rate_word)
{
    uint16_t w = (uint16_t)rate_word;
    (void)HAL_SPI_Transmit(&hspi3, (uint8_t *)&w, 1u, 2u);   /* one 16-bit frame, ~32 us at 500 kbit/s */
}

/* ------------------------------------------------------------------ encoder */
uint32_t port_enc_raw(void) { return __HAL_TIM_GET_COUNTER(&htim2); }
unsigned port_enc_bits(void) { return IS_TIM_32B_COUNTER_INSTANCE(htim2.Instance) ? 32u : 16u; }

/* ------------------------------------------------------------------ UART helpers */
typedef struct { volatile uint8_t b[256]; volatile uint16_t h, t; } ring_t;
static void ring_put(ring_t *r, uint8_t v) { uint16_t n = (uint16_t)((r->h + 1u) & 0xFFu); if (n != r->t) { r->b[r->h] = v; r->h = n; } }
static bool ring_get(ring_t *r, uint8_t *v) { if (r->t == r->h) { return false; } *v = r->b[r->t]; r->t = (uint16_t)((r->t + 1u) & 0xFFu); return true; }

static ring_t link_rx, rs485_rx;
static uint8_t link_byte, rs485_byte;
static uint8_t link_tx[32], rs485_tx[48];

void HAL_UART_RxCpltCallback(UART_HandleTypeDef *h)
{
    if (h == &hlpuart1) { ring_put(&link_rx, link_byte); (void)HAL_UART_Receive_IT(&hlpuart1, &link_byte, 1u); }
    else if (h == &huart2) { ring_put(&rs485_rx, rs485_byte); (void)HAL_UART_Receive_IT(&huart2, &rs485_byte, 1u); }
}

void HAL_UART_ErrorCallback(UART_HandleTypeDef *h)
{
    /* framing/noise/overrun: drop the byte and re-arm reception */
    if (h == &hlpuart1) { (void)HAL_UART_Receive_IT(&hlpuart1, &link_byte, 1u); }
    else if (h == &huart2) { (void)HAL_UART_Receive_IT(&huart2, &rs485_byte, 1u); }
}

void port_link_send(const uint8_t *p, size_t n)
{
    if (n > sizeof link_tx || hlpuart1.gState != HAL_UART_STATE_READY) { return; }   /* drop: next frame in 20 ms */
    memcpy(link_tx, p, n);
    (void)HAL_UART_Transmit_IT(&hlpuart1, link_tx, (uint16_t)n);
}

size_t port_link_recv(uint8_t *p, size_t max)
{
    size_t n = 0u;
    while (n < max && ring_get(&link_rx, &p[n])) { n++; }
    return n;
}

void port_rs485_send(const char *line)
{
    size_t n = strlen(line);
    if (n > sizeof rs485_tx || huart2.gState != HAL_UART_STATE_READY) { return; }
    memcpy(rs485_tx, line, n);
    (void)HAL_UART_Transmit_IT(&huart2, rs485_tx, (uint16_t)n);   /* DE driven by the USART (RS-485 mode) */
}

bool port_rs485_get_line(char *buf, size_t n)
{
    static char acc[64];
    static size_t len;
    uint8_t c;
    while (ring_get(&rs485_rx, &c)) {
        if (c == '\r' || c == '\n') {
            if (len == 0u) { continue; }
            size_t k = (len < n - 1u) ? len : n - 1u;
            memcpy(buf, acc, k); buf[k] = '\0'; len = 0u;
            return true;
        }
        if (len < sizeof acc - 1u) { acc[len++] = (char)c; }
    }
    return false;
}

void port_log(const char *s) { (void)HAL_UART_Transmit(&huart1, (const uint8_t *)s, (uint16_t)strlen(s), 5u); }

/* ------------------------------------------------------------------ ADC: VBAT = 2 x VBAT_SENSE */
static uint32_t adc_read(uint32_t channel)
{
    ADC_ChannelConfTypeDef c = { 0 };
    c.Channel = channel;
    c.Rank = ADC_REGULAR_RANK_1;
    c.SamplingTime = ADC_SAMPLINGTIME_COMMON_1;   /* set COMMON_1 >= 39.5 cycles in CubeMX: 100 k source + C104 */
    if (HAL_ADC_ConfigChannel(&hadc4, &c) != HAL_OK) { return 0u; }
    if (HAL_ADC_Start(&hadc4) != HAL_OK) { return 0u; }
    uint32_t v = (HAL_ADC_PollForConversion(&hadc4, 2u) == HAL_OK) ? HAL_ADC_GetValue(&hadc4) : 0u;
    (void)HAL_ADC_Stop(&hadc4);
    return v;
}

uint16_t port_vbat_mv(void)
{
    uint32_t vref = adc_read(ADC_CHANNEL_VREFINT);
    uint32_t raw = adc_read(ADC_CHANNEL_10);
    if (vref == 0u) { return 0u; }                 /* reads as "battery low": fails safe */
    uint32_t vdda = __LL_ADC_CALC_VREFANALOG_VOLTAGE(vref, LL_ADC_RESOLUTION_12B);
    uint32_t mv = __LL_ADC_CALC_DATA_TO_VOLTAGE(vdda, raw, LL_ADC_RESOLUTION_12B) * 2u;
    return (uint16_t)(mv > 65535u ? 65535u : mv);
}

/* ------------------------------------------------------------------ I2C, watchdog, RNG */
bool port_i2c_write(uint8_t a, uint8_t reg, uint8_t val)
{
    return HAL_I2C_Mem_Write(&hi2c3, (uint16_t)(a << 1), reg, I2C_MEMADD_SIZE_8BIT, &val, 1u, 5u) == HAL_OK;
}

bool port_i2c_read(uint8_t a, uint8_t reg, uint8_t *val)
{
    return HAL_I2C_Mem_Read(&hi2c3, (uint16_t)(a << 1), reg, I2C_MEMADD_SIZE_8BIT, val, 1u, 5u) == HAL_OK;
}

void port_wdg_kick(void) { (void)HAL_IWDG_Refresh(&hiwdg); }

uint32_t port_random(void)
{
    uint32_t r = 0u;
    if (HAL_RNG_GenerateRandomNumber(&hrng, &r) != HAL_OK) { r = HAL_GetTick() * 2654435761u; }
    return r;
}

/* ------------------------------------------------------------------ BLE glue */
/* The CubeWBA BLE application (STM32_WPAN) calls these: pump_ble_set_secure() from the pairing and
 * encryption-change events, pump_ble_set_notify() once at start-up with a function that sends a
 * notification on the status characteristic, and pump_app_ble_rx() from the GATT write handler. */
static volatile bool ble_secure;
static void (*ble_notify_fn)(const uint8_t *, size_t);

void pump_ble_set_secure(bool secure) { ble_secure = secure; }
void pump_ble_set_notify(void (*fn)(const uint8_t *, size_t)) { ble_notify_fn = fn; }
bool port_ble_link_secure(void) { return ble_secure; }
void port_ble_notify(const uint8_t *p, size_t n) { if (ble_notify_fn != NULL) { ble_notify_fn(p, n); } }

/* ------------------------------------------------------------------ entry points for main.c */
/* Call pump_main_init() in USER CODE BEGIN 2 (after all MX_*_Init calls) and pump_main_poll() inside the
 * while(1) loop next to the BLE sequencer (MX_APPE_Process / UTIL_SEQ_Run). */
void pump_main_init(void)
{
    moder_a_af = GPIOA->MODER & MASK_A;            /* CubeMX left the SPI pins in AF mode */
    moder_b_af = GPIOB->MODER & MASK_B;
    port_pmd_spi_enable(false);
    port_set_48v_enable(false);
    (void)HAL_TIM_Encoder_Start(&htim2, TIM_CHANNEL_ALL);
    (void)HAL_UART_Receive_IT(&hlpuart1, &link_byte, 1u);
    (void)HAL_UART_Receive_IT(&huart2, &rs485_byte, 1u);
    pump_app_init();
}

void pump_main_poll(void)
{
    static uint32_t last;
    uint32_t now = HAL_GetTick();
    if (now != last) {
        last = now;
        pump_app_tick();
    }
}
