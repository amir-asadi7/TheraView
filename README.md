# TheraView
TheraView is a portable two angle capture system for physical therapy and occupational therapy. The goal is to build a simple and affordable kit that records sessions at high quality, offers a live preview, supports synchronized dual camera use, and later adds pose analysis and activity tools. TheraView is part of the RITA Project.

## Roadmap

### Stage 1: Single Camera Unit *(Current Stage)*
- Install Raspberry Pi OS Lite ✅
- Verify 1080p at 30 FPS capture with MJPG ✅
- Add GStreamer preview output to an HTML page ✅
- Confirm recording stability 
- Test power bank duration 
- Add the first enclosure design
- Use the Bluetooth button on the tripod mount to trigger camera recording
- Add an RTC module for reliable time tracking

### Stage 2: Dual Camera System
- Add a second camera setup
- Add synchronized start across both units
- Build a page that displays the two live previews
- Improve local network coordination
- Add a auto file transfer system when connected to an external HDD

### Stage 3: Synchronized Recording and Playback
- Align timelines between both units
- Create a playback layout with two camera angles
- Add session metadata
- Improve storage flow and file handling

### Stage 4: Pose Detection
- Apply pose models to recorded sessions
- Produce structured data for therapist review
- Add export and visualization tools
- Add a privacy layer that captures only pose and activity data instead of raw video when desired

### Stage 5: Activity and Game Layer
- Train models for specific therapy tasks
- Add workflow logic for guided activities
- Add simple games that respond to pose output

### Stage 6: External Processing Unit
- Add an external processor for real time analysis
- Offload compute tasks from Raspberry Pi units
- Improve overall performance of the streaming and analysis pipeline


---


## Hardware

- **Raspberry Pi 4B**
- **Microsoft LifeCam Studio**  
  Any USB webcam that supports 1080p MJPG at 30 FPS can be used.
- **Power bank** 10,000 mAh, 22.5 W output (Anker)  
  *Operation duration: [to be tested]*
- **MicroSD card** 64 GB
- **Cooling fan for Raspberry Pi**
- **3D printed enclosure:** [to be added]
- **Tripod mount**  
  This model (link TBA ) was used and the enclosure design follows this choice.
  It also includes a Bluetooth button used to trigger camera control.
- **Optional future processing unit**

---

## Software

- **Raspberry Pi OS Lite (Bookworm)**  
  - Version: [placeholder]  
  - Release date: [placeholder]
- **GStreamer**  
  - Version: [to be added]
- To be completed

---

## Setup Guide


Use [Raspberry Pi Imager](https://www.raspberrypi.com/software/) with advanced settings before writing the SD cards.

**Hostnames**  
TVA (unit one)  
TVB (unit two)
It is important to set these correctly because the setup process depends on them.

**Username**  
pi

**Password**  
ritaengs

**SSH**  
Enabled

You'll need internet access during setup and first test run.  Set the wifi info in RPi imager to an external Wi Fi network. A mobile hotspot is fine. If you use an iPhone hotspot, rename your Phone. Names like `John's iPhone` contain an apostrophe and the Raspberry Pi will not accept them. Use a simple name such as `John iPhone`.

Allow a few minutes on the first boot.  
On a computer connected to the same network, connected to the RPi using:

```bash
ssh pi@TVA.local
#or 
ssh pi@TVB.local
```
If hostname lookup fails, find the device IP with a network scanner and connect to that IP instead of using TVA.local.

---


After getting connected

```
sudo apt install git
git clone [https://github.com/NeuroRehack/TheraView](https://github.com/NeuroRehack/TheraView)
cd TheraView
chmod +x scripts/setup.sh
./scripts/setup.sh
```

## Usage

**[ instructions to be added]**

---



---

*TheraView — A RITA Project initiative.*
