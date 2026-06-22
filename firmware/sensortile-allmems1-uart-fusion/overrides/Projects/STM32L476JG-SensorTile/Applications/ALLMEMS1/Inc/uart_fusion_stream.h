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

#define UART_FUSION_STREAM_UART_INSTANCE       UART5
#define UART_FUSION_STREAM_UART_BAUDRATE       115200U

#define UART_FUSION_STREAM_TX_GPIO_PORT        GPIOC
#define UART_FUSION_STREAM_TX_GPIO_CLK_ENABLE() __HAL_RCC_GPIOC_CLK_ENABLE()
#define UART_FUSION_STREAM_TX_PIN              GPIO_PIN_12
#define UART_FUSION_STREAM_TX_GPIO_AF          GPIO_AF8_UART5

#define UART_FUSION_STREAM_RX_GPIO_PORT        GPIOD
#define UART_FUSION_STREAM_RX_GPIO_CLK_ENABLE() __HAL_RCC_GPIOD_CLK_ENABLE()
#define UART_FUSION_STREAM_RX_PIN              GPIO_PIN_2
#define UART_FUSION_STREAM_RX_GPIO_AF          GPIO_AF8_UART5

#define UART_FUSION_STREAM_UART_CLK_ENABLE()   __HAL_RCC_UART5_CLK_ENABLE()
#define UART_FUSION_STREAM_UART_CLK_DISABLE()  __HAL_RCC_UART5_CLK_DISABLE()

#define UART_FUSION_STREAM_PERIOD_MS           100U

#define UART_FUSION_FRAME_SYNC0                0xA5U
#define UART_FUSION_FRAME_SYNC1                0x5AU
#define UART_FUSION_FRAME_VERSION              0x01U
#define UART_FUSION_FRAME_TYPE_TELEMETRY       0x01U
#define UART_FUSION_FRAME_PAYLOAD_LEN          72U

#define UART_FUSION_STATUS_QUAT_VALID          0x01U
#define UART_FUSION_STATUS_MOTION_VALID        0x02U
#define UART_FUSION_STATUS_TEMP_VALID          0x04U
#define UART_FUSION_STATUS_PRESSURE_VALID      0x08U
#define UART_FUSION_STATUS_MAG_CALIBRATED      0x10U

extern UART_HandleTypeDef hUartFusionStream;

void UART_FusionStream_MspInit(UART_HandleTypeDef *huart);
void UART_FusionStream_MspDeInit(UART_HandleTypeDef *huart);
void UART_FusionStream_Init(void);
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
                                 uint8_t status_flags);

#endif /* ALLMEMS1_ENABLE_UART_FUSION_STREAM */

#endif /* UART_FUSION_STREAM_H */
