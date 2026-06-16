/**
  ******************************************************************************
  * @file    uart_fusion_stream.c
  * @brief   Optional UART stream for PERSEUS DAQ board.
  ******************************************************************************
  */

#include "uart_fusion_stream.h"

#ifdef ALLMEMS1_ENABLE_UART_FUSION_STREAM

#include <stdio.h>
#include <string.h>

UART_HandleTypeDef hUartFusionStream;

static void append_float(char **cursor, size_t *remaining, float value, uint8_t precision)
{
  int32_t scale = 1;
  int32_t whole;
  int32_t frac;
  int32_t scaled;
  int written;

  while (precision-- > 0U) {
    scale *= 10;
  }

  scaled = (int32_t)(value * (float)scale);
  if (scaled < 0) {
    scaled = -scaled;
    written = snprintf(*cursor, *remaining, "-");
    if ((written > 0) && ((size_t)written < *remaining)) {
      *cursor += written;
      *remaining -= (size_t)written;
    }
  }

  whole = scaled / scale;
  frac = scaled % scale;
  written = snprintf(*cursor, *remaining, "%ld.%0*ld",
                     (long)whole,
                     (int)(scale == 1000000 ? 6 : 3),
                     (long)frac);
  if ((written > 0) && ((size_t)written < *remaining)) {
    *cursor += written;
    *remaining -= (size_t)written;
  }
}

void UART_FusionStream_Init(void)
{
  hUartFusionStream.Instance = UART_FUSION_STREAM_UART_INSTANCE;
  hUartFusionStream.Init.BaudRate = UART_FUSION_STREAM_UART_BAUDRATE;
  hUartFusionStream.Init.WordLength = UART_WORDLENGTH_8B;
  hUartFusionStream.Init.StopBits = UART_STOPBITS_1;
  hUartFusionStream.Init.Parity = UART_PARITY_NONE;
  hUartFusionStream.Init.Mode = UART_MODE_TX_RX;
  hUartFusionStream.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  hUartFusionStream.Init.OverSampling = UART_OVERSAMPLING_16;
  hUartFusionStream.Init.OneBitSampling = UART_ONE_BIT_SAMPLE_DISABLE;
  hUartFusionStream.AdvancedInit.AdvFeatureInit = UART_ADVFEATURE_NO_INIT;

  if (HAL_UART_Init(&hUartFusionStream) == HAL_OK) {
    static const char header[] =
      "BOOT,ALLMEMS1_UART_FUSION_STREAM\r\n"
      "FUS,frame_id,t_ms,dt_ms,ax,ay,az,gx,gy,gz,mx,my,mz,q0,q1,q2,q3,calib\r\n";

    (void)HAL_UART_Transmit(&hUartFusionStream,
                            (uint8_t *)header,
                            (uint16_t)(sizeof(header) - 1U),
                            200U);
  }
}

void UART_FusionStream_SendFrame(uint32_t frame_id,
                                 uint32_t t_ms,
                                 uint32_t dt_ms,
                                 int32_t ax, int32_t ay, int32_t az,
                                 int32_t gx, int32_t gy, int32_t gz,
                                 int32_t mx, int32_t my, int32_t mz,
                                 float q0, float q1, float q2, float q3,
                                 uint8_t calib_status)
{
  char buffer[240];
  char *cursor = buffer;
  size_t remaining = sizeof(buffer);
  int written;

  if (hUartFusionStream.gState != HAL_UART_STATE_READY) {
    return;
  }

  written = snprintf(cursor, remaining,
                     "FUS,%lu,%lu,%lu,%ld,%ld,%ld,%ld,%ld,%ld,%ld,%ld,%ld,",
                     (unsigned long)frame_id,
                     (unsigned long)t_ms,
                     (unsigned long)dt_ms,
                     (long)ax, (long)ay, (long)az,
                     (long)gx, (long)gy, (long)gz,
                     (long)mx, (long)my, (long)mz);
  if ((written <= 0) || ((size_t)written >= remaining)) {
    return;
  }
  cursor += written;
  remaining -= (size_t)written;

  append_float(&cursor, &remaining, q0, 6U);
  written = snprintf(cursor, remaining, ",");
  if ((written <= 0) || ((size_t)written >= remaining)) { return; }
  cursor += written; remaining -= (size_t)written;
  append_float(&cursor, &remaining, q1, 6U);
  written = snprintf(cursor, remaining, ",");
  if ((written <= 0) || ((size_t)written >= remaining)) { return; }
  cursor += written; remaining -= (size_t)written;
  append_float(&cursor, &remaining, q2, 6U);
  written = snprintf(cursor, remaining, ",");
  if ((written <= 0) || ((size_t)written >= remaining)) { return; }
  cursor += written; remaining -= (size_t)written;
  append_float(&cursor, &remaining, q3, 6U);

  written = snprintf(cursor, remaining, ",%u\r\n", calib_status);
  if ((written <= 0) || ((size_t)written >= remaining)) {
    return;
  }
  cursor += written;

  (void)HAL_UART_Transmit(&hUartFusionStream,
                          (uint8_t *)buffer,
                          (uint16_t)(cursor - buffer),
                          50U);
}

#endif /* ALLMEMS1_ENABLE_UART_FUSION_STREAM */
