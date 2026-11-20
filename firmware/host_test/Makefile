# Host build of both firmwares + plant model. Usage: make -C firmware/host_test   (run tests)
CC      ?= gcc
CFLAGS  ?= -std=c11 -O2 -g -Wall -Wextra -Werror -Wshadow -Wconversion -Wno-sign-conversion -DPUMP_TEST
APP      = ../main_wba55/app
SUP      = ../supervisor_c031/app
SRC      = ../common/link_proto.c \
           $(APP)/dose_limits.c $(APP)/load_est.c $(APP)/pmd401.c $(APP)/charger.c $(APP)/ble_cmd.c \
           $(APP)/dose_ctrl.c $(APP)/pump_app.c \
           $(SUP)/sup_logic.c \
           sim_plant.c sim_ports.c test_main.c

all: run

pump_host_test: $(SRC) $(wildcard $(APP)/*.h $(SUP)/*.h ../common/*.h *.h)
	$(CC) $(CFLAGS) -o $@ $(SRC) -lm

run: pump_host_test
	./pump_host_test

clean:
	rm -f pump_host_test

.PHONY: all run clean
