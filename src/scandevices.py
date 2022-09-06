import decawave_ble
import logging
import json
import time
import tenacity

myformat = "%(asctime)s.%(msecs)03d %(levelname)s:\t%(message)s"
logging.basicConfig(format=myformat,
                    level=logging.INFO,
                    datefmt="%H:%M:%S")
logging.getLogger().setLevel(logging.INFO)


logging.info('Scanning for Decawave devices')
devices = decawave_ble.scan_for_decawave_devices()
logging.info('Found {} Decawave devices'.format(len(devices)))
device_names = list(devices.keys())
for key, value in devices.items():
    '''
    print(key, value.__dict__)
    decawave_peripheral = decawave_ble.get_decawave_peripheral(value)
    print(decawave_peripheral)

    network_id = decawave_ble.get_network_id_from_peripheral(decawave_peripheral)
    print(network_id)

    decawave_peripheral.disconnect()

    device_info_data = decawave_ble.get_operation_mode_data(value)
    logging.info('Device Info Data')
    print(device_info_data)

    data_total = decawave_ble.get_data(value)
    logging.info('All data of device')
    print(data_total)

    network_node_service = decawave_ble.get_decawave_network_node_service_from_peripheral(decawave_peripheral)
    logging.info('Network Node Service')
    print(network_node_service)
'''

    if key == "DW5293":
        decawave_peripheral = decawave_ble.get_decawave_peripheral(value)
        break

while True:
    try:
        location_data = decawave_ble.get_location_data_from_peripheral(decawave_peripheral)
        json_dump = json.dumps(location_data["position_data"], indent=2)
        print(json_dump)
    except tenacity.RetryError as retry_err:
        print("Disconnected: Fetch Peripheral")
        decawave_peripheral = decawave_ble.get_decawave_peripheral(value)
    except Exception as e:
        print("Other Exception: ", e)
