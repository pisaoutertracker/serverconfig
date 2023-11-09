from switchbotmeter import DevScanner

for current_devices in DevScanner():
    for device in current_devices:
      if device.temp : 
        print(device)
        print(f'{device.humidity}  {device.temp} {device.device.addr}')

