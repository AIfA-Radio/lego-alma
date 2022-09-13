# LEGO-ALMA

## Position measurements utilizing Ultra-Wideband (UWB)

In the following project we describe a PoC with Decawave DWB1001-development boards for 
Lego-ALMA at AIfA, University Bonn. The underlying idea is to measure the location of mobile antennas
to demonstrate the functionality of an astronomical [Radio-Interferometer](
https://astro.uni-bonn.de/en/research/mm-submm-astronomy/projects-1/alma/lego-alma).

Inspired by an article [Precise Realtime Indoor Localization With Raspberry Pi And Ultra-Wideband Technology](
https://medium.com/@newforestberlin/precise-realtime-indoor-localization-with-raspberry-pi-and-ultra-wideband-technology-decawave-191e4e2daa8c)
we developed a similar setup. The difference being that the readout of the Decawave boards 
is realized via BLE, though. We use either a raspberry PI 4 or the board computer of the Lego-ALMA with 
a BLE USB dongle.

After the entire UWB network will be configured utilizing the [Android SDK](
https://github.com/AIfA-Radio/lego-alma/blob/main/app/DRTLS_Manager_R2.apk) for anchors and tags, 
we invoke

    python3 ./DW_read_tags.py

Caveat: sudo rights are required, as scanning of BLE devices requires root rights on your host.

#### Contact

Ralf Antonius Timmermann, Email: rtimmermann@astro.uni-bonn.de,
Toma Badescu, Email: toma@astro.uni-bonn.de,

Argelander Institute for Astronomy (AIfA), University Bonn, Germany.