# emulator

SNES emulation setup for this project.

## Option 1 — macOS (OpenEmu)

**OpenEmu** is the recommended emulator on macOS.

```bash
brew install --cask openemu
xattr -dr com.apple.quarantine /Applications/OpenEmu.app
open -a OpenEmu
```

Drag a ROM from `roms/` into the OpenEmu library window, then double-click to play.

---

## Option 2 — Linux VM (UTM + RetroArch)

For a more reliable setup, run a Linux VM using UTM with RetroArch inside it.

### Prerequisites

```bash
brew install --cask utm
```

### 1. Download Ubuntu 24.04 ARM64 Desktop ISO

```bash
curl -L --progress-bar \
  -o emulator/vm/ubuntu-24.04-desktop-arm64.iso \
  "https://cdimage.ubuntu.com/releases/24.04/release/ubuntu-24.04.4-desktop-arm64.iso"
```

### 2. Generate the autoinstall seed ISO

The `autoinstall.yaml` file automates the Ubuntu installer — no manual clicking required.

```bash
mkdir -p emulator/vm/seed
cp emulator/vm/autoinstall.yaml emulator/vm/seed/user-data
touch emulator/vm/seed/meta-data
hdiutil makehybrid -o emulator/vm/seed.iso -hfs -iso -joliet emulator/vm/seed/ -ov
```

The `autoinstall.yaml` installs:
- Ubuntu Desktop (GNOME)
- RetroArch + cores
- Python 3, git, venv
- SSH server

Default credentials: username `skorn`, password `samuel`

To change credentials, edit `autoinstall.yaml` and regenerate the password hash:
```bash
openssl passwd -6 "yournewpassword"
```
Then re-run the seed ISO generation step above.

### 3. Create the VM in UTM

1. Open UTM → **Create a New Virtual Machine**
2. Select **Virtualize** → **Linux**
3. Boot ISO: select `emulator/vm/ubuntu-24.04-desktop-arm64.iso`
4. Hardware: **4096 MB RAM**, **4 CPU cores**
5. Storage: **30 GB**
6. Name: `snes-retro` → **Save**
7. Before booting, go to VM settings → **Drives** → **Add Drive** → **Import**
   and select `emulator/vm/seed.iso` (set type to CD/DVD)

### 4. Boot and auto-install

Click **Play** in UTM. The installer will run fully automatically (~10 minutes).
When it reboots, log in with username `skorn` / password `samuel`.

### 5. Pass USB controller through to VM

In UTM VM settings → **Devices** → **USB** → add the USB Gamepad (VID: 0x0079).
The controller will appear as a joystick inside Linux.

### 6. Install a SNES core in RetroArch

Inside the VM:

```
RetroArch → Load Core → Download a Core → Nintendo - SNES / SFC → Snes9x
```

### 7. Copy ROMs into the VM

From the host Mac, SCP the ROMs to the VM:

```bash
scp emulator/roms/*.SMC skorn@<vm-ip>:~/roms/
```

Or use UTM's shared folder feature to mount `emulator/roms/` directly.

---

## ROMs

Place `.sfc` or `.smc` ROM files in the `roms/` folder.

> ROMs are excluded from version control via `.gitignore`.

---

## Controller button layout

| SNES Button | HID location  |
|-------------|---------------|
| B           | byte 5 bit 6  |
| A           | byte 5 bit 5  |
| X           | byte 5 bit 4  |
| Y           | byte 5 bit 7  |
| L           | byte 6 bit 0  |
| R           | byte 6 bit 1  |
| Select      | byte 6 bit 4  |
| Start       | byte 6 bit 5  |
| D-Pad       | bytes 3 & 4   |
