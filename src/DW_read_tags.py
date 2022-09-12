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


def main():
    logging.info('Scanning for Decawave devices')
    devices = decawave_ble.scan_for_decawave_devices()
    number_devices = len(devices)
    logging.info(
        'Found No Decawave devices: Exiting ... nothing to track' if number_devices == 0 else
        'Found {0} Decawave device{1}'.format(number_devices, 's' if number_devices != 1 else '')
    )
    if len(devices) == 0:
        exit(1)

    devices_anchor = dict()
    peripherals_anchor = dict()
    devices_tag = dict()
    peripherals_tag = dict()

    for key, value in devices.items():
        decawave_peripheral = decawave_ble.get_decawave_peripheral(value)
        operation_mode_data = decawave_ble.get_operation_mode_data_from_peripheral(decawave_peripheral)
        if operation_mode_data['device_type_name'] == 'Tag':
            devices_tag[key] = value
            peripherals_tag[key] = decawave_peripheral
        elif operation_mode_data['device_type_name'] == 'Anchor':
            devices_anchor[key] = value
            peripherals_anchor[key] = decawave_peripheral

    number_anchors = len(devices_anchor)
    logging.info(
        'Found less than 3 Anchors: Exiting ...' if number_anchors < 3 else
        'Found {0} Decawave Anchor{1}'.format(number_anchors, 's' if number_anchors != 1 else '')
    )
    if number_anchors < 3:
        exit(1)

    for key, decawave_peripheral in peripherals_anchor.items():
        location_data = decawave_ble.get_location_data_from_peripheral(decawave_peripheral)
        print({key: location_data["position_data"]})

    number_tags = len(devices_tag)
    logging.info(
        'Found No Decawave Tag: Exiting ... nothing to track' if number_tags == 0 else
        'Found {0} Decawave Tag{1}'.format(number_tags, 's' if number_tags != 1 else '')
    )
    if number_tags == 0:
        exit(1)

    while True:
        for key, decawave_peripheral in peripherals_tag.items():
            try:
                location_data = decawave_ble.get_location_data_from_peripheral(decawave_peripheral)
                print({key: location_data["position_data"]})
            except tenacity.RetryError:
                print("Disconnected: fetch peripheral again")
                decawave_peripheral = decawave_ble.get_decawave_peripheral(devices_tag[key])
                peripherals_tag[key] = decawave_peripheral
            except Exception as e:
                print("Other Exception: ", e)

        time.sleep(.1)


if __name__ == "__main__":
    main()
