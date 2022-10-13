# LEGO-ALMA

## Position measurements utilizing Ultra-Wideband (UWB)

In the following project we describe a PoC with Decawave DWB1001-Development boards for 
[Lego-ALMA](
https://astro.uni-bonn.de/en/research/mm-submm-astronomy/projects-1/alma/lego-alma) (in German) 
at the Argelander Institute for Astronomy (AIfA), University Bonn. 
The underlying idea is to locate mobile antennas
to demonstrate the functionality of an astronomical Radio-Interferometer. 
When antennas are moved with respect to each other, baselines do change, thus, 
it reveals changes in the interferogram.

Inspired by an article 
[Precise Realtime Indoor Localization With Raspberry Pi And Ultra-Wideband Technology](
https://medium.com/@newforestberlin/precise-realtime-indoor-localization-with-raspberry-pi-and-ultra-wideband-technology-decawave-191e4e2daa8c)
we developed a similar setup. The difference being, though, the readout of the Decawave boards
is realized via BLE. We utilize a raspberry PI 4 or Lego-ALMA's board computer, with
a BLE USB dongle attached, as BLE clients.

### UWB Sensor Set-Up

#### Download the Decawave Software Package

This package includes documentation and the necessary software for the DWM1001-Development board which
is found here: https://www.segger.com/downloads/jlink/ 

#### Flash the UWB Sensors with J-Flash Light

After having installed the application, follow the next steps and flash all sensors (anchors & tags):

* Connect the sensor with a micro-USB data cable to your computer.
* Flash the image DWM1001 module
  * Open J-Flash Lite
  * Choose nrf52832_XXAA as device and SWD as interface, use default speed 1000. Click “OK”
* Click “Erase Chip” to do a full chip erase.
* In Data File, click and browse the downloaded Decawave Software Package [DWM1001_PANS_R2.0.hex](
https://github.com/AIfA-Radio/lego-alma/blob/main/Factory_Firmware_Image/DWM1001_PANS_R2.0.hex) to flash, 
click “Program Device”.

#### Define anchors and tags via Decawave Android App

The entire UWB network will be configured utilizing the [Android SDK](
https://github.com/AIfA-Radio/lego-alma/blob/main/app/DRTLS_Manager_R2.apk). 
If you have successfully installed the application on your Android Smartphone, 
you can now power up each sensor either via the micro-USB connector or batteries (switch). 
If the LEDs of the sensors flash green and red, the connection can be established via BLE. 
Seek the sensors with the Decawave App. Networks & Devices reaveals if there are unassigned devices. 
Others may already be identified and assigned to our network "lego-alma". 
Unidentified sensors need to be assigned to the same network now.

In most cases the lego-alma network - comprising 4 anchors and between 1 and 8 tags - is already 
entirely defined. 
However, in case of any pecularities (e.g. after a device reset) we may have to redefine the board and 
assign it to the lego-alma network. 

|           Network Details            |           Anchor Settings           |           Tag Settings           |
|:------------------------------------:|:-----------------------------------:|:--------------------------------:|
| ![](./images/Screenshot_network.jpg) | ![](./images/Screenshot_anchor.jpg) | ![](./images/Screenshot_tag.jpg) |

If you are in jeopardy having to configure the UWB boards, please configure them as shown above for 
anchors and tags. Caveat: only one anchor (mandatory) can serve as an initiator. 

#### Anchor Location & Auto Positioning

If no previous action was required, we will have to resume here in order to auto-position
the anchors. This action is mandatory after the anchors were relocated from a previous setup.
For best quality measurements, all 4 boards need to be in the same plane! After having performed
the auto-positioning the anchors MUST NOT - NEVER EVER - be relocated.
It is also desirable to place the tags into the plane of the
anchors, which is - in the nature of Lego-ALMA - not feasible. The tags may be lowered from that plane such,
that individuals of the auditorium may not be in LOS between tags and anchors.

To position the anchor points automatically proceed to Network Details and invoke "Auto positioning". Click
"Measure" and - if successful - "Save". We are done. On "Grid" you can verify the current UWB setup 
(in units of meter) of 
achors and tags. Before you call the application on Lego-ALMA you will have to leave the Android APP, 
since many clients cannot access the tag's BLE module simultaneously.

For the time being we invoke

    sudo -E python3 ./src/DW_read_tags.py

Caveat: sudo rights are required, as scanning of BLE devices requires root on your client.

#### Contact

Ralf Antonius Timmermann, email: rtimmermann@astro.uni-bonn.de &
Toma Badescu, email: toma@astro.uni-bonn.de,
Argelander Institute for Astronomy (AIfA), University Bonn, Germany.