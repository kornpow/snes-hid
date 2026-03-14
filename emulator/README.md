# emulator

SNES emulation setup for this project.

## Emulator

**Snes9x** — installed via Homebrew at `/Applications/Snes9x.app`

To reinstall:
```bash
brew install --cask snes9x
```

## ROMs

Place `.sfc` or `.smc` ROM files in the `roms/` folder, then open them with:

```bash
open -a Snes9x emulator/roms/your-game.sfc
```

Or launch Snes9x and use File → Open to browse to `emulator/roms/`.

> ROMs are excluded from version control via `.gitignore`.

## Controller setup

Snes9x will automatically detect the USB gamepad (VID: 0x0079, PID: 0x0011)
as a joystick input. To configure button mapping inside Snes9x:

1. Open Snes9x
2. Go to **Input → Joystick Commands**
3. Select **Joypad 1** and map each button

The physical button layout for this controller is:

| SNES Button | Maps to     |
|-------------|-------------|
| B           | byte 5 bit 6 |
| A           | byte 5 bit 5 |
| X           | byte 5 bit 4 |
| Y           | byte 5 bit 7 |
| L           | byte 6 bit 0 |
| R           | byte 6 bit 1 |
| Select      | byte 6 bit 4 |
| Start       | byte 6 bit 5 |
| D-Pad       | bytes 3 & 4  |
