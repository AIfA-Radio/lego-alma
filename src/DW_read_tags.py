import decawave_ble
import logging
import time
import tenacity

myformat = "%(asctime)s.%(msecs)03d %(levelname)s:\t%(message)s"
logging.basicConfig(format=myformat,
                    level=logging.INFO,
                    datefmt="%H:%M:%S")
logging.getLogger().setLevel(logging.INFO)


def check_total_number_devices(devices):
    number_devices = len(devices)
    logging.info(
        'Found No Decawave devices: Exiting ... nothing to track' if number_devices == 0 else
        'Found {0} Decawave device{1}'.format(number_devices, 's' if number_devices != 1 else '')
    )
    if len(devices) == 0:
        exit(1)


def check_total_number_anchors(devices_anchor):
    number_anchors = len(devices_anchor)
    logging.info(
        'Found less than 3 Anchors: Exiting ...' if number_anchors < 3 else
        'Found {0} Decawave Anchor{1}'.format(number_anchors, 's' if number_anchors != 1 else '')
    )
    if number_anchors < 3:
        exit(1)


def check_total_number_tags(devices_tag):
    number_tags = len(devices_tag)
    logging.info(
        'Found No Decawave Tag: Exiting ... nothing to track' if number_tags == 0 else
        'Found {0} Decawave Tag{1}'.format(number_tags, 's' if number_tags != 1 else '')
    )
    if number_tags == 0:
        exit(1)


def main():
    logging.info('Scanning for Decawave devices')
    devices = decawave_ble.scan_for_decawave_devices()
    check_total_number_devices(devices=devices)

    # splitting the devices into anchors and tags
    # peripherals_xxx comprise {<deviceID>: <current peripheral>} that needs to be updated after a connection was lost
    devices_anchor = dict()
    devices_tag = dict()
    peripherals_anchor = dict()
    peripherals_tag = dict()

    for key, value in devices.items():
        decawave_peripheral = decawave_ble.get_decawave_peripheral(value)
        operation_mode_data = decawave_ble.get_operation_mode_data_from_peripheral(decawave_peripheral)
        network_id = decawave_ble.get_network_id_from_peripheral(decawave_peripheral)
        # ToDo: having a fixed network ID in the code is not a good idea!
        if network_id == 0x66ce:
            if operation_mode_data['device_type_name'] == 'Tag':
                devices_tag[key] = value
                peripherals_tag[key] = decawave_peripheral
            elif operation_mode_data['device_type_name'] == 'Anchor':
                devices_anchor[key] = value
                peripherals_anchor[key] = decawave_peripheral
        else:
            logging.warning("Decawave devices found from network ID: {}, hence, being disregarded".format(network_id))

    # anchors
    check_total_number_anchors(devices_anchor=devices_anchor)
    # and print their positions
    for key, decawave_peripheral in peripherals_anchor.items():
        location_data = decawave_ble.get_location_data_from_peripheral(decawave_peripheral)
        print({key: location_data["position_data"]})
    # tags
    check_total_number_tags(devices_tag=devices_tag)

    # loop over all tags
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
                print("Other Exception: {}".format(e))

        time.sleep(.2)


if __name__ == "__main__":
    main()
