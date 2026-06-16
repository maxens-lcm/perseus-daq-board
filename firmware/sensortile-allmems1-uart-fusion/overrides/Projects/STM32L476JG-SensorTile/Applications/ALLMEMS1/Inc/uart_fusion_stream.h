/**
  ******************************************************************************
  * @file    uart_fusion_stream.h
  * @brief   Optional UART stream for PERSEUS DAQ board.
  ******************************************************************************
  */

#ifndef UART_FUSION_STREAM_H
#define UART_FUSION_STREAM_H

#include "ALLMEMS1_config.h"

#ifdef ALLMEMS1_ENABLE_UART_FUSION_STREAM

#include "stm32l4xx_hal.h"
#include <stdint.h>

#define UART_FUSION_STREAM_UART_INSTANCE       USART1
#define UART_FUSION_STREAM_UART_BAUDRATE       115200U

#define UART_FUSION_STREAM_TX_GPIO_PORT        GPIOA
#define UART_FUSION_STREAM_TX_GPIO_CLK_ENABLE() __HAL_RCC_GPIOA_CLK_ENABLE()
#define UART_FUSION_STREAM_TX_PIN              GPIO_PIN_9
#define UART_FUSION_STREAM_TX_GPIO_AF          GPIO_AF7_USART1

#define UART_FUSION_STREAM_RX_GPIO_PORT        GPIOA
#define UART_FUSION_STREAM_RX_GPIO_CLK_ENABLE() __HAL_RCC_GPIOA_CLK_ENABLE()
#define UART_FUSION_STREAM_RX_PIN              GPIO_PIN_10
#define UART_FUSION_STREAM_RX_GPIO_AF          GPIO_AF7_USART1

#define UART_FUSION_STREAM_UART_CLK_ENABLE()   __HAL_RCC_USART1_CLK_ENABLE()
#define UART_FUSION_STREAM_UART_CLK_DISABLE()  __HAL_RCC_USART1_CLK_DISABLE()

#define UART_FUSION_STREAM_PERIOD_MS           1000U

extern UART_HandleTypeDef hUartFusionStream;

void UART_FusionStream_MspInit(UART_HandleTypeDef *huart);
void UART_FusionStream_MspDeInit(UART_HandleTypeDef *huart);
void UART_FusionStream_Init(void);
void UART_FusionStream_SendFrame(uint32_t frame_id,
                                 uint32_t t_ms,
                                 uint32_t dt_ms,
                                 int32_t ax, int32_t ay, int32_t az,
                                 int32_t gx, int32_t gy, int32_t gz,
                                 int32_t mx, int32_t my, int32_t mz,
                                 float q0, float q1, float q2, float q3,
                                 uint8_t calib_status);

#endif /* ALLMEMS1_ENABLE_UART_FUSION_STREAM */

#endif /* UART_FUSION_STREAM_H */
