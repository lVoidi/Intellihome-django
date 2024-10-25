# main.py
import network
import socket
import time
from machine import Pin

# WiFi credentials
SSID = 'Senora de lo Angeles'
PASSWORD = '44556677'

def connect_to_wifi(ssid, password):
    debug_pin = Pin(20, Pin.OUT)
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect(SSID, PASSWORD)
        while not sta_if.isconnected():
            pass
    debug_pin.value(1)
    print('network config:', sta_if.ifconfig())

def main():
    wlan = connect_to_wifi(SSID, PASSWORD)
    print('WiFi connected')
    
    addr = socket.getaddrinfo('0.0.0.0', 8080)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(100)
    print(f"[DEBUG] Escuchando al puerto 8080, en {addr}")
    while True:
        cl, addr = s.accept()
        cl_file = cl.makefile('rwb', 0)
        while True:
            line = cl_file.readline()
            print(line)
            if not line or line == b'\r\n':
                break
        print(f"[DEBUG] Cliente conectado desde: {addr} ")
        request = cl.recv(1024).decode()
        print(f"[DEBUG] Request recibido: {request}")


main()