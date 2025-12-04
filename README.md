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


## Hardware used for development

- **Raspberry Pi 4B**
- **Microsoft LifeCam Studio**  
  Any USB webcam that supports 1080p MJPG at 30 FPS can be used.
- **Power bank** 10,000 mAh, 22.5 W output (Anker)  
  *Operation duration: [to be tested]*
- **MicroSD card** 64 GB
- **Cooling fan for Raspberry Pi**
- **3D printed enclosure:** [to be added]
- **Tripod mount**  
  This model was used and the enclosure design follows this choice.
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

**[Placeholder: Detailed setup instructions will be added here]**

---

## Usage

**[Placeholder: Usage instructions to be added]**

---



---

*TheraView — A RITA Project initiative.*
