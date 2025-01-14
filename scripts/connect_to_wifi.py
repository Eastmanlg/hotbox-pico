import network

def do_connect(ssid, pw):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect(ssid, pw)
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())


ssid = 'Wu-Tang LAN'
ssidPw = "Ain'tNothingToFunkWith!"


do_connect(ssid, ssidPw)