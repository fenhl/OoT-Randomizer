#ifndef EVERDRIVE_H
#define EVERDRIVE_H

bool everdrive_detect();
bool everdrive_read(uint8_t *buf);
bool everdrive_write(uint8_t *buf);

#endif
