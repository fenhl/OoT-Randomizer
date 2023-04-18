#include <mips.h>
#include <n64.h>

#include "everdrive.h"
#include "z64.h"

#define REG_EDID 0x0005
#define REG_KEY 0x2001

#define REG_BASE 0xBF800000
#define REGS_PTR ((volatile uint32_t *)REG_BASE)

static int      cart_irqf;
static uint32_t cart_lat;
static uint32_t cart_pwd;
static uint16_t spi_cfg;

#define ED64_DETECTION_UNKNOWN 0
#define ED64_DETECTION_PRESENT 1
#define ED64_DETECTION_NOT_PRESENT 2
uint8_t everdrive_detection_state = ED64_DETECTION_UNKNOWN;

static inline void __pi_wait(void) {
    while (pi_regs.status & (PI_STATUS_DMA_BUSY | PI_STATUS_IO_BUSY)) {
        // busy loop
    }
}

static inline uint32_t __pi_read_raw(uint32_t dev_addr) {
    __pi_wait();
    return *(volatile uint32_t *)dev_addr;
}

static inline void __pi_write_raw(uint32_t dev_addr, uint32_t value) {
    __pi_wait();
    *(volatile uint32_t *)dev_addr = value;
}

static inline uint32_t reg_rd(int reg) {
    return __pi_read_raw((uint32_t)&REGS_PTR[reg]);
}


static inline void reg_wr(int reg, uint32_t dat) {
    return __pi_write_raw((uint32_t)&REGS_PTR[reg], dat);
}

// set irq bit and return previous value
static inline int set_irqf(int irqf) {
  uint32_t sr;

  __asm__ ("mfc0    %[sr], $12;" : [sr] "=r"(sr));
  int old_irqf = sr & MIPS_STATUS_IE;

  sr = (sr & ~MIPS_STATUS_IE) | (irqf & MIPS_STATUS_IE);
  __asm__ ("mtc0    %[sr], $12;" :: [sr] "r"(sr));

  return old_irqf;
}

void cart_lock_safe() {
    z64_osPiGetAccess();
    cart_irqf = set_irqf(0);
    cart_lat = pi_regs.dom1_lat;
    cart_pwd = pi_regs.dom1_pwd;
}

void cart_unlock() {
    pi_regs.dom1_lat = cart_lat;
    pi_regs.dom1_pwd = cart_pwd;
    z64_osPiRelAccess();
    set_irqf(cart_irqf);
}

bool everdrive_detect() {
    if (everdrive_detection_state == ED64_DETECTION_UNKNOWN) {
        cart_lock_safe();
        reg_wr(REG_KEY, 0xAA55);
        if ((reg_rd(REG_EDID) >> 16) == 0xED64) {
            cart_unlock();
            everdrive_detection_state = ED64_DETECTION_PRESENT;
        } else {
            reg_wr(REG_KEY, 0);
            cart_unlock();
            everdrive_detection_state = ED64_DETECTION_NOT_PRESENT;
        }
    }
    return everdrive_detection_state == ED64_DETECTION_PRESENT;
}
