/**
  ******************************************************************************
  * @file    uart_fusion_stream.c
  * @brief   Optional UART stream for PERSEUS DAQ board.
  ******************************************************************************
  */

#include "uart_fusion_stream.h"

#ifdef ALLMEMS1_ENABLE_UART_FUSION_STREAM

UART_HandleTypeDef hUartFusionStream;

#define UART_FUSION_FRAME_HEADER_LEN 6U
#define UART_FUSION_FRAME_CRC_LEN    2U
#define UART_FUSION_FRAME_TOTAL_LEN  (UART_FUSION_FRAME_HEADER_LEN + \
                                      UART_FUSION_FRAME_PAYLOAD_LEN + \
                                      UART_FUSION_FRAME_CRC_LEN)

static uint16_t crc16_ccitt(const uint8_t *data, uint16_t length)
{
  uint16_t crc = 0xFFFFU;

  while (length-- > 0U) {
    crc ^= (uint16_t)(*data++) << 8;
    for (uint8_t bit = 0; bit < 8U; bit++) {
      if ((crc & 0x8000U) != 0U) {
        crc = (uint16_t)((crc << 1) ^ 0x1021U);
      } else {
        crc <<= 1;
      }
    }
  }

  return crc;
}

static void put_u16_le(uint8_t *dst, uint16_t value)
{
  dst[0] = (uint8_t)(value & 0xFFU);
  dst[1] = (uint8_t)((value >> 8) & 0xFFU);
}

static void put_i16_le(uint8_t *dst, int16_t value)
{
  put_u16_le(dst, (uint16_t)value);
}

static void put_u32_le(uint8_t *dst, uint32_t value)
{
  dst[0] = (uint8_t)(value & 0xFFU);
  dst[1] = (uint8_t)((value >> 8) & 0xFFU);
  dst[2] = (uint8_t)((value >> 16) & 0xFFU);
  dst[3] = (uint8_t)((value >> 24) & 0xFFU);
}

static void put_i32_le(uint8_t *dst, int32_t value)
{
  put_u32_le(dst, (uint32_t)value);
}

void UART_FusionStream_Init(void)
{
  /* Enable UART clock */
  UART_FUSION_STREAM_UART_CLK_ENABLE();

  /* De-initialize PA11 and PA12 to prevent any USB CDC conflicts on these pins */
  __HAL_RCC_GPIOA_CLK_ENABLE();
  HAL_GPIO_DeInit(GPIOA, GPIO_PIN_11 | GPIO_PIN_12);

  /* Initialize UART pins */
  GPIO_InitTypeDef GPIO_InitStruct = {0};

  GPIO_InitStruct.Pin = UART_FUSION_STREAM_TX_PIN;
  GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
  GPIO_InitStruct.Alternate = UART_FUSION_STREAM_TX_GPIO_AF;
  UART_FUSION_STREAM_TX_GPIO_CLK_ENABLE();
  HAL_GPIO_Init(UART_FUSION_STREAM_TX_GPIO_PORT, &GPIO_InitStruct);

  GPIO_InitStruct.Pin = UART_FUSION_STREAM_RX_PIN;
  GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
  GPIO_InitStruct.Alternate = UART_FUSION_STREAM_RX_GPIO_AF;
  UART_FUSION_STREAM_RX_GPIO_CLK_ENABLE();
  HAL_GPIO_Init(UART_FUSION_STREAM_RX_GPIO_PORT, &GPIO_InitStruct);

  /* Initialize UART */
  hUartFusionStream.Instance = UART_FUSION_STREAM_UART_INSTANCE;
  hUartFusionStream.Init.BaudRate = UART_FUSION_STREAM_UART_BAUDRATE;
  hUartFusionStream.Init.WordLength = UART_WORDLENGTH_8B;
  hUartFusionStream.Init.StopBits = UART_STOPBITS_1;
  hUartFusionStream.Init.Parity = UART_PARITY_NONE;
  hUartFusionStream.Init.Mode = UART_MODE_TX_RX;
  hUartFusionStream.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  hUartFusionStream.Init.OverSampling = UART_OVERSAMPLING_16;
  hUartFusionStream.AdvancedInit.AdvFeatureInit = UART_ADVFEATURE_SWAP_INIT;
  hUartFusionStream.AdvancedInit.Swap = UART_ADVFEATURE_SWAP_ENABLE;

  (void)HAL_UART_Init(&hUartFusionStream);
}

void UART_FusionStream_SendFrame(uint32_t frame_id,
                                 uint32_t t_ms,
                                 uint32_t dt_ms,
                                 int32_t q0, int32_t q1,
                                 int32_t q2, int32_t q3,
                                 int32_t ax, int32_t ay, int32_t az,
                                 int32_t gx, int32_t gy, int32_t gz,
                                 int32_t mx, int32_t my, int32_t mz,
                                 int16_t temp_c_x10,
                                 int32_t pressure_hpa_x100,
                                 uint8_t calib_status,
                                 uint8_t status_flags)
{
  static uint8_t frame[UART_FUSION_FRAME_TOTAL_LEN];
  uint16_t pos = 0U;
  uint16_t crc;

  if (hUartFusionStream.gState != HAL_UART_STATE_READY) {
    return;
  }

  frame[pos++] = UART_FUSION_FRAME_SYNC0;
  frame[pos++] = UART_FUSION_FRAME_SYNC1;
  frame[pos++] = UART_FUSION_FRAME_VERSION;
  frame[pos++] = UART_FUSION_FRAME_TYPE_TELEMETRY;
  put_u16_le(&frame[pos], UART_FUSION_FRAME_PAYLOAD_LEN);
  pos += 2U;

  put_u32_le(&frame[pos], frame_id); pos += 4U;
  put_u32_le(&frame[pos], t_ms); pos += 4U;
  put_u32_le(&frame[pos], dt_ms); pos += 4U;
  put_i32_le(&frame[pos], q0); pos += 4U;
  put_i32_le(&frame[pos], q1); pos += 4U;
  put_i32_le(&frame[pos], q2); pos += 4U;
  put_i32_le(&frame[pos], q3); pos += 4U;
  put_i32_le(&frame[pos], ax); pos += 4U;
  put_i32_le(&frame[pos], ay); pos += 4U;
  put_i32_le(&frame[pos], az); pos += 4U;
  put_i32_le(&frame[pos], gx); pos += 4U;
  put_i32_le(&frame[pos], gy); pos += 4U;
  put_i32_le(&frame[pos], gz); pos += 4U;
  put_i32_le(&frame[pos], mx); pos += 4U;
  put_i32_le(&frame[pos], my); pos += 4U;
  put_i32_le(&frame[pos], mz); pos += 4U;
  put_i16_le(&frame[pos], temp_c_x10); pos += 2U;
  put_i32_le(&frame[pos], pressure_hpa_x100); pos += 4U;
  frame[pos++] = calib_status;
  frame[pos++] = status_flags;

  crc = crc16_ccitt(&frame[2], (uint16_t)(pos - 2U));
  put_u16_le(&frame[pos], crc);
  pos += 2U;

  (void)HAL_UART_Transmit_IT(&hUartFusionStream, frame, pos);
}

void UART5_IRQHandler(void)
{
  HAL_UART_IRQHandler(&hUartFusionStream);
}

#endif /* ALLMEMS1_ENABLE_UART_FUSION_STREAM */
