# This file is executed on every boot (including wake-boot from deepsleep)
import esp
esp.osdebug(None)
#import uos
#uos.dupterm(None, 1) # disable REPL on UART(0)
import gc
import webrepl
webrepl.start()
gc.collect()
import sys
#not needed 2023-06-23
#del sys.path[0]
#sys.path.append('')

