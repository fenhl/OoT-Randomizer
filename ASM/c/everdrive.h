#ifndef EVERDRIVE_H
#define EVERDRIVE_H

bool everdrive_detect();
bool everdrive_read(void *buf);
bool everdrive_write(void *buf);

#endif
