#!/usr/bin/python3
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
    if operation_mode_data['device_type_name'] == 'Tag':
        devices_tag[key] = value
        peripherals_tag[key] = decawave_peripheral
    elif operation_mode_data['device_type_name'] == 'Anchor':
        devices_anchor[key] = value
        peripherals_anchor[key] = decawave_peripheral

# anchors
check_total_number_anchors(devices_anchor=devices_anchor)
# and print their positions
for key, decawave_peripheral in peripherals_anchor.items():
    location_data = decawave_ble.get_location_data_from_peripheral(decawave_peripheral)
    print({key: location_data["position_data"]})
# tags
check_total_number_tags(devices_tag=devices_tag)

# loop over all tags
# set 

try:
    reference_tag = 'DW5293'
    ref_loc_data = decawave_ble.get_location_data_from_peripheral(peripherals_tag[reference_tag])
except tenacity.RetryError:
    reference_tag = 'DW5293'
    ref_peripheral = decawave_ble.get_decawave_peripheral(devices_tag[reference_tag])
    ref_loc_data = decawave_ble.get_location_data_from_peripheral(ref_peripheral)
except Exception as e:
    print(e)
    ref_loc_data = {'position_data':{'x_position':0,'y_position':0,'z_position':0}}
i=0
pos_list = []
N=1000
while i<N:
    for key, decawave_peripheral in peripherals_tag.items():
        try:
            location_data = decawave_ble.get_location_data_from_peripheral(decawave_peripheral)
            print({key: location_data["position_data"]})
            x,y,z,q = (location_data["position_data"]['x_position'] - ref_loc_data["position_data"]['x_position'],location_data["position_data"]['y_position'] - ref_loc_data["position_data"]['y_position'],location_data["position_data"]['z_position'] - ref_loc_data["position_data"]['z_position'],location_data['position_data']['quality'])
            print(key+' ref corrected positions:',x,y,z,q)
            #plt.scatter(location_data['x_position'],location_data['y_position'])
            pos_list.append((x,y,z,q))
            i+=1
        except tenacity.RetryError:
            print("Disconnected: fetch peripheral again")
            decawave_peripheral = decawave_ble.get_decawave_peripheral(devices_tag[key])
            peripherals_tag[key] = decawave_peripheral
        except Exception as e:
            print("Other Exception: ", e)
#    time.sleep(.1)
import numpy as np
pos_list = np.asarray(pos_list).T
print(np.mean(pos_list,axis=1))
print(np.std(pos_list,axis=1))
print(np.average(pos_list[0:3],axis=1,weights=[pos_list[3],pos_list[3],pos_list[3]]))

import matplotlib.pyplot as plt
bins = int(max(max(pos_list[0]) - min(pos_list[0]),max(pos_list[1]) - min(pos_list[1]))/4)
plt.hist2d(pos_list[0],pos_list[1],bins)
plt.xlabel("X offset [cm]")
plt.ylabel("Y offset [cm]")

plt.colorbar(label='N')
plt.title("N="+"{:n}".format(N)+" samples")
plt.savefig("test1.pdf")
plt.show()


