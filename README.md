# LEGO-ALMA

## Position measurements utilizing Ultra-Wideband (UWB)

In the following project we describe a PoC with Decawave DWB1001-Development boards for 
[Lego-ALMA](
https://astro.uni-bonn.de/en/research/mm-submm-astronomy/projects-1/alma/lego-alma) (in German) 
at AIfA, University Bonn. The underlying idea is to measure the location of mobile antennas
to demonstrate the functionality of an astronomical Radio-Interferometer for varying baselines.

Inspired by an article [Precise Realtime Indoor Localization With Raspberry Pi And Ultra-Wideband Technology](
https://medium.com/@newforestberlin/precise-realtime-indoor-localization-with-raspberry-pi-and-ultra-wideband-technology-decawave-191e4e2daa8c)
we developed a similar setup. The difference being, that the readout of the Decawave boards 
is realized via BLE, though. As a client we use a raspberry PI 4 or the board computer of the Lego-ALMA with 
a BLE USB dongle.

### Set up the UWB Sensors

#### Download the Decawave Software Package

This package includes documentation and the necessary software for the DWM1001 development board.
This package is found here: https://www.segger.com/downloads/jlink/ 

#### Flash the UWB Sensors with J-Flash Light

After installing the application, follow the next steps and flash all sensors (anchors and tags):

* Connect the sensor with a micro USB data cable to your computer.
* Flash the image DWM1001 module
  * Open J-Flash Lite
  * Choose nrf52832_XXAA as device and SWD as interface, use default speed 1000. Click “OK”
* Click “Erase Chip” to do a full chip erase.
* In Data File, click and browse the downloaded Decawave Software Package [DWM1001_PANS_R2.0.hex](
https://github.com/AIfA-Radio/lego-alma/blob/main/Factory_Firmware_Image/DWM1001_PANS_R2.0.hex) to flash, 
click “Program Device”.

#### Define anchors and tags via Decawave Android App

The entire UWB network will be configured utilizing the [Android SDK](
https://github.com/AIfA-Radio/lego-alma/blob/main/app/DRTLS_Manager_R2.apk) for anchors and tags. 
If you have successfully installed the application, you can now power each sensor via the micro-USB connector. 
If the LEDs of the sensors flash green and red, the connection can be established via BLE. 
You can seek the sensors with the Decawave App (Networks & Devices), if there are unassigned devices. Others may
already be identified in our network "lego-alma". Unidentified sensors need to be assigned to the same network.

In most cases the lego-alma network - comprising 4 anchors and between 1 and 8 tags - is already entirely defined. 
However, in case of any pecularities (e.g. after a device reset) we may have to redefine anchors or tags and 
assign it to the lego-alma network. 

Network Overview             |  Anchor Settings | Tag Settings  
:-------------------------:|:-------------------------:|:------------------
![](./images/Screenshot_network.jpg) | ![](./images/Screenshot_anchor.jpg) | ![](./images/Screenshot_tag.jpg)

If you are in jeopardy having to configure the UWB boards, please configure them as shown above for anchors and tags. 
Caveat: only one anchor (mandatory) can serve as an initiator. If no action was required, as described above, 
we will have to auto-locate 
the anchors (for best quality measurements) all 4 boards need to be in the same plane! After auto-location 
the anchors MUST NOT - NEVER EVER - be relocated. 

tbc.

we invoke

    sudo -E python3 ./src/DW_read_tags.py

Caveat: sudo rights are required, as scanning of BLE devices requires root on your client.

#### Contact

Ralf Antonius Timmermann, email: rtimmermann@astro.uni-bonn.de &
Toma Badescu, email: toma@astro.uni-bonn.de,
Argelander Institute for Astronomy (AIfA), University Bonn, Germany.