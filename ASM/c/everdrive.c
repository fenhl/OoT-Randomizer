#include <stdbool.h>
#include <mips.h>
#include <n64.h>

#include "everdrive.h"
#include "z64.h"

#define REG_USB_CFG 0x0001
#define REG_EDID    0x0005
#define REG_USB_DAT 0x0100
#define REG_SYS_CFG 0x2000
#define REG_KEY     0x2001

#define REG_BASE 0xBF800000
#define REGS_PTR ((volatile uint32_t *)REG_BASE)

#define USB_LE_CFG 0x8000
#define USB_LE_CTR 0x4000

#define USB_CFG_RD  0x0400
#define USB_CFG_WR  0x0000
#define USB_CFG_ACT 0x0200

#define USB_STA_PWR 0x1000
#define USB_STA_RXF 0x0400
#define USB_STA_TXE 0x0800
#define USB_STA_ACT 0x0200

#define USB_CMD_RD      (USB_LE_CFG | USB_LE_CTR | USB_CFG_RD | USB_CFG_ACT)
#define USB_CMD_RD_NOP  (USB_LE_CFG | USB_LE_CTR | USB_CFG_RD)
#define USB_CMD_WR      (USB_LE_CFG | USB_LE_CTR | USB_CFG_WR | USB_CFG_ACT)
#define USB_CMD_WR_NOP  (USB_LE_CFG | USB_LE_CTR | USB_CFG_WR)

static int      cart_irqf;
static uint32_t cart_lat;
static uint32_t cart_pwd;
static uint16_t spi_cfg;

#define ED64_DETECTION_UNKNOWN 0
#define ED64_DETECTION_PRESENT 1
#define ED64_DETECTION_NOT_PRESENT 2
uint8_t everdrive_detection_state = ED64_DETECTION_UNKNOWN;

// set irq bit and return previous value
static inline int set_irqf(int irqf) {
  uint32_t sr;

  __asm__ ("mfc0    %[sr], $12;" : [sr] "=r"(sr));
  int old_irqf = sr & MIPS_STATUS_IE;

  sr = (sr & ~MIPS_STATUS_IE) | (irqf & MIPS_STATUS_IE);
  __asm__ ("mtc0    %[sr], $12;" :: [sr] "r"(sr));

  return old_irqf;
}

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

static void pio_read(uint32_t dev_addr, uint32_t ram_addr, size_t size) {
    if (size == 0) {
        return;
    }

    uint32_t dev_s = dev_addr & ~0x3;
    uint32_t dev_e = (dev_addr + size + 0x3) & ~0x3;
    uint32_t dev_p = dev_s;

    uint32_t ram_s = ram_addr;
    uint32_t ram_e = ram_s + size;
    uint32_t ram_p = ram_addr - (dev_addr - dev_s);

    while (dev_p < dev_e) {
        uint32_t w = __pi_read_raw(dev_p);
        for (int i = 0; i < 4; i++) {
            if (ram_p >= ram_s && ram_p < ram_e) {
                *(uint8_t *)ram_p = w >> 24;
            }
            w <<= 8;
            ram_p++;
        }
        dev_p += 4;
    }
}

static void pio_write(uint32_t dev_addr, uint32_t ram_addr, size_t size)
{
  if (size == 0)
    return;

  uint32_t dev_s = dev_addr & ~0x3;
  uint32_t dev_e = (dev_addr + size + 0x3) & ~0x3;
  uint32_t dev_p = dev_s;

  uint32_t ram_s = ram_addr;
  uint32_t ram_e = ram_s + size;
  uint32_t ram_p = ram_addr - (dev_addr - dev_s);

  while (dev_p < dev_e) {
    uint32_t w = __pi_read_raw(dev_p);
    for (int i = 0; i < 4; i++) {
      uint8_t b;
      if (ram_p >= ram_s && ram_p < ram_e)
        b = *(uint8_t *)ram_p;
      else
        b = w >> 24;
      w = (w << 8) | b;
      ram_p++;
    }
    __pi_write_raw(dev_p, w);
    dev_p += 4;
  }
}

void pi_read_locked(uint32_t dev_addr, void *dst, size_t size) {
    pio_read(dev_addr, (uint32_t)dst, size);
}

void pi_write_locked(uint32_t dev_addr, void *dst, size_t size) {
    pio_write(dev_addr, (uint32_t)dst, size);
}

static inline uint32_t reg_rd(int reg) {
    return __pi_read_raw((uint32_t)&REGS_PTR[reg]);
}


static inline void reg_wr(int reg, uint32_t dat) {
    return __pi_write_raw((uint32_t)&REGS_PTR[reg], dat);
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
        switch (reg_rd(REG_EDID)) {
            case 0xED640008: // EverDrive 3.0
            case 0xED640013: // EverDrive X7
                // initialize USB
                reg_wr(REG_SYS_CFG, 0);
                cart_unlock();
                everdrive_detection_state = ED64_DETECTION_PRESENT;
                break;
            default: // EverDrive without USB support or no EverDrive
                reg_wr(REG_KEY, 0);
                cart_unlock();
                everdrive_detection_state = ED64_DETECTION_NOT_PRESENT;
                break;
        }
    }
    return everdrive_detection_state == ED64_DETECTION_PRESENT;
}

bool everdrive_read(void *buf) {
    cart_lock_safe();
    uint32_t len = 16; // for simplicity, the protocol is designed so each packet size is the EverDrive's minimum of 16 bytes
    uint32_t usb_cfg = reg_rd(REG_USB_CFG);
    if (!(usb_cfg & USB_STA_PWR)) {
        // cannot read or write (no USB device connected?)
        cart_unlock();
        return false;
    }
    if (usb_cfg & USB_STA_ACT) {
        // currently busy reading or writing
        cart_unlock();
        return false;
    }
    if (usb_cfg & USB_STA_RXF) {
        // no data waiting
        cart_unlock();
        return false;
    } else {
        // data waiting, start reading
        reg_wr(REG_USB_CFG, USB_CMD_RD | (512 - len));
        uint16_t timeout = 0;
        while (reg_rd(REG_USB_CFG) & USB_STA_ACT) {
            // still reading
            if (timeout++ == 8192) {
                // timed out
                return false; //TODO set buf to special error packet and return true?
            }
        }
        reg_wr(REG_USB_CFG, USB_CMD_RD_NOP);
        pi_read_locked((uint32_t)&REGS_PTR[REG_USB_DAT] + (512 - len), buf, len);
        cart_unlock();
        return true;
    }
}

bool everdrive_write(void *buf) {
    cart_lock_safe();
    uint32_t len = 16; // for simplicity, the protocol is designed so each packet size is the EverDrive's minimum of 16 bytes
    uint32_t usb_cfg = reg_rd(REG_USB_CFG);
    if (!(usb_cfg & USB_STA_PWR)) {
        // cannot read or write (no USB device connected?)
        cart_unlock();
        return false;
    }
    if (usb_cfg & USB_STA_ACT) {
        // currently busy reading or writing
        cart_unlock();
        return false;
    }
    if (usb_cfg & USB_STA_TXE) {
        // no data waiting
        cart_unlock();
        return false;
    } else {
        // data waiting, start writing
        reg_wr(REG_USB_CFG, USB_CMD_WR_NOP);
        pi_write_locked((uint32_t)&REGS_PTR[REG_USB_DAT] + (512 - len), buf, len);
        reg_wr(REG_USB_CFG, USB_CMD_WR | (512 - len));
        uint16_t timeout = 0;
        while (reg_rd(REG_USB_CFG) & USB_STA_ACT) {
            // still reading
            if (timeout++ == 8192) {
                // timed out
                return false; //TODO set buf to special error packet and return true?
            }
        }
        cart_unlock();
        return true;
    }
}
