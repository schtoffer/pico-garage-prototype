"""
    Project: GurgleApps Webserver
    File: main.py
    Author: GurgleApps.com
    Date: 2021-04-01
    Description: Demonstrates how to use the GurgleApps Webserver
"""
from gurgleapps_webserver import GurgleAppsWebserver
import config
import utime as time
import uasyncio as asyncio
from machine import Pin
import ujson as json
from hcsr04 import HCSR04

led = Pin("LED", Pin.OUT) # circuit board LED
switch_restart = Pin(20, Pin.OUT)
garage_signal = Pin(16, Pin.OUT)
magnet = Pin(17, mode=Pin.IN, pull=Pin.PULL_DOWN)
sensor = HCSR04(trigger_pin=19, echo_pin=18, echo_timeout_us=10000)

led_r = Pin(15, Pin.OUT)
led_y = Pin(14, Pin.OUT)
led_g = Pin(13, Pin.OUT)

led.off()

blink_off_time = 0.5
blink_on_time = 0.5

status = True
shutdown = False

def red():
    led_g.off()
    led_y.off()
    led_r.on()
    
def yellow():
    led_g.off()
    led_y.on()
    led_r.off()

def green():
    led_g.on()
    led_y.off()
    led_r.off()
    
def leds_off():
    led_g.off()
    led_y.off()
    led_r.off()

async def example_func(request, response, param1, param2):
    print("example_func")
    print("param1: " + param1)
    print("param2: " + param2)
    response_string = json.dumps({ "param1": param1, "param2": param2, "post_data": request.post_data})
    await response.send_json(response_string, 200)

async def say_hello(request, response, name):
    await response.send_html("Hello " + name + " hope you are well")

async def send_status(request, response):
    # send boolean status and number frequency
    response_string = json.dumps({"door-state": magnet.value()})
    await response.send_json(response_string, 200)

async def set_blink_pattern(request, response, on, off):
    print("on: " + on)
    print("off: " + off)
    global blink_off_time, blink_on_time
    blink_off_time = float(off)
    blink_on_time = float(on)
    await send_status(request, response)

async def set_delay(request, response, new_delay):
    print("new delay: " + new_delay)
    global blink_off_time, blink_on_time
    blink_off_time = float(new_delay)
    blink_on_time = float(new_delay) 
    await send_status(request, response)

async def stop_flashing(request, response):
    global status
    status = False
    await send_status(request, response)

async def start_flashing(request, response):
    global status
    status = True
    await send_status(request, response)

async def stop_server(request, response):
    global shutdown
    await response.send_html("Server stopping")
    await server.stop_server()
    shutdown = True

async def control_garage_door(request, response, operation):
    if operation == "close":
        if magnet.value() == 1:
            pass
        else:
            garage_signal.on()
            await asyncio.sleep(1)
            garage_signal.off()
    elif operation == "open":
        if magnet.value() == 0:
            pass
        else:
            garage_signal.on()
            await asyncio.sleep(1)
            garage_signal.off()
    await send_status(request, response)

async def main():
    global shutdown
    
    while not shutdown:
        await asyncio.sleep(0.2)
        distance = sensor.distance_cm()
        print(distance)
        
        if distance < 20:
            while True:
                distance = sensor.distance_cm()
                red()
                time.sleep(.1)
                leds_off()
                time.sleep(.1)
                print(distance)
                if distance > 5:
                    break
        elif distance > 0 and distance < 30:
            red()
        elif distance >= 30 and distance < 80:
            green()
        else:
            leds_off()
        await asyncio.sleep(.1)
        
        ###

        if magnet.value() == 1:
            await asyncio.sleep(1)
            #switch_restart.on()
        
        if server.wlan.isconnected() == False:       
            await asyncio.sleep(1)
            switch_restart.on()
        else:
            led.on()
            #print(server.wlan.isconnected())
            
server = GurgleAppsWebserver(config.WIFI_SSID, config.WIFI_PASSWORD, port=80, timeout=20, doc_root="/www", log_level=2)
server.add_function_route("/set-delay/<delay>", set_delay)
server.add_function_route(
    "/set-blink-pattern/<on_time>/<off_time>",
    set_blink_pattern
)
server.add_function_route("/stop", stop_flashing)
server.add_function_route("/start", start_flashing)
server.add_function_route("/status", send_status)
server.add_function_route("/example/func/<param1>/<param2>", example_func)
server.add_function_route("/hello/<name>", say_hello)
server.add_function_route("/stop-server", stop_server)
server.add_function_route("/garage-door/<operation>", control_garage_door)

asyncio.run(server.start_server_with_background_task(main))
print('DONE')
