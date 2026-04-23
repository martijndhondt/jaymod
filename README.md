# Jaymod

![Downloads](https://img.shields.io/github/downloads/martijndhondt/jaymod/total)
![Build Linux](https://github.com/martijndhondt/jaymod/actions/workflows/build-linux.yml/badge.svg)
![Build Windows](https://github.com/martijndhondt/jaymod/actions/workflows/build-windows.yml/badge.svg)

This is the source for the last release of Jaymod, which is version 2.0.0.

## Releases

| Version | Tag | Notes |
|---|---|---|
| [2.2.3](https://github.com/martijndhondt/jaymod/releases/tag/v2.2.3) | `v2.2.3` | configurable announce HP display position |
| [2.2.2 (ET Legacy)](https://github.com/martijndhondt/jaymod/releases/tag/v2.2.2-etlegacy) | `v2.2.2-etlegacy` | dynamite countdown timer built-in |
| [2.2.1 (ET Legacy)](https://github.com/martijndhondt/jaymod/releases/tag/v2.2.1-etlegacy) | `v2.2.1-etlegacy` | announcehp built-in, CI full package builds |
| [2.2.0 (ET Legacy)](https://github.com/martijndhondt/jaymod/releases/tag/v2.2.0-etlegacy) | `v2.2.0-etlegacy` | OmniBot ABI fix, GCC/MinGW support, GitHub Actions CI |

# Dynamite Timer

Jaymod 2.2.2 adds a built-in dynamite countdown timer implemented directly in the game code (`src/game/g_dynamitetimer.cpp`), without requiring a Lua script.

When dynamite is planted and armed, players receive a center-print message each second showing the time remaining until detonation:

```
Dynamite: 30 seconds!
...
Dynamite: ^310 seconds!   (yellow)
...
Dynamite: ^15 seconds!    (red)
```

**Who sees the timer:**

| Player | When |
|---|---|
| Planting team | Full countdown from the moment it is armed |
| Defending team | Last 10 seconds only |
| Spectators | Never |

**Cvar:** `g_dynamiteTimer` (default `1`)

| Value | Behaviour |
|---|---|
| `1` | Enabled (default) |
| `0` | Disabled |

# Announce HP

Jaymod 2.2.1 implements the popular `announcehp` feature directly in the game code (`src/game/g_combat.cpp`), without requiring a separate Lua script or server-side plugin.

When a player is killed by an enemy, the victim receives a message showing the killer's name and their remaining HP:

```
PlayerName had 3 HP left
```

The message only appears for enemy kills — not for teamkills or self-damage.

**Cvar:** `g_announceHP` — controls both enablement and display position (default `1`)

| Value | Behaviour |
|---|---|
| `0` | Disabled |
| `1` | Center-print — large text, upper-center of screen **(default)** |
| `2` | Popup message — stacks in the left-side kill-message area |
| `3` | Banner print — small text at top of screen |
| `4` | Console notification — top-left overlay |

# ET Legacy + GCC Compatibility (OmniBot ABI fix)

The original Jaymod release shipped a `qagame_mp_x86.dll` built with MSVC. When the DLL is recompiled with GCC (MinGW), bots crash immediately on connect because of a calling-convention mismatch between MSVC and GCC for C++ virtual functions that return a non-trivial class by value.

**Root cause:** MSVC and GCC disagree on where `this` and the hidden return-value pointer go in the thiscall convention:

- MSVC: `ECX = this`, `[EBP+8] = hidden_ptr`
- GCC: `ECX = hidden_ptr`, `[EBP+8] = this`

Since OmniBot is an MSVC-compiled DLL that calls into the GCC-compiled game module through a C++ vtable, five `GameEntity`-returning virtual functions
(`GetLocalGameEntity`, `EntityFromID`, `EntityByName`, `GetEntityOwner`, `FindEntityInSphere`)
were crashing as GCC treated the MSVC-supplied hidden pointer (passed in ECX) as `this` and attempted vtable dispatch through it.

**Fix:** The five affected virtual functions are replaced with `__attribute__((naked))` assembly thunks that explicitly implement MSVC's calling convention — reading ECX as `this`, reading `[EBP+8]` as the hidden return pointer, delegating to plain `extern "C"` cdecl helper functions for the actual logic, writing the result into `*hidden_ptr`, returning `hidden_ptr` in EAX, and cleaning up the stack with the correct `ret $N` for each signature.

Additional fixes included:
- Portable `#pragma pack(push, 4)` form (replacing MSVC-only two-step syntax) in the OmniBot message headers
- Null guard in `UpdateBotInput` to prevent a crash when the client pointer is not yet valid
- Internal calls to `GetEntityOwner` within the game module now call the helper directly instead of going through the vtable

With these changes, bots successfully connect and play on an ET Legacy dedicated server using the GCC-compiled `qagame_mp_x86.dll`.

# Compiling

The mod uses a GNU make-based build system originally designed (2006) to cross-compile for Linux, Windows (MinGW), and OSX.

> **Note:** The [original build system document](notes/BuildSystem.txt) is largely historical. Many things it describes no longer apply: the project moved from SVN to Git, Windows builds now use MinGW64 (MSYS2) instead of MSVC + Cygwin, PowerPC/OSX targets are long gone, and the multi-machine "hub host" release process is not needed. The sections on make targets (`make`, `make clean`, `make debug`, `make release`), the `PLATFORM` / `VARIANT` / `GCC/=` variables, and the `build/` output directory separation are still accurate.

## Windows (MinGW64 / MSYS2) — recommended

Install [MSYS2](https://www.msys2.org/) and the MinGW32 toolchain:

```bash
pacman -S mingw-w64-i686-toolchain
```

Then build from the MSYS2 shell:

```bash
mingw32-make.exe PLATFORM=mingw "GCC/=/path/to/mingw32/"
# Example using the default MSYS2 install path:
mingw32-make.exe PLATFORM=mingw "GCC/=/c/msys64/mingw32/"
```

The output DLL is placed at `build.mingw/game/qagame_mp_x86.dll`. No external runtime DLLs are needed — `libwinpthread` is linked statically.

## Linux

```bash
make
```

Requires GCC and the standard GNU toolchain. Produces `build/game/qagame_mp_x86.so`.

## Make targets

| Target | Description |
|---|---|
| `make` / `make all` | Compile and link everything |
| `make clean` | Remove all build output (run after changing headers) |
| `make debug` | Build with debug symbols (`VARIANT=debug`) |
| `make release` | Optimised release build (`VARIANT=release`) |
| `make pkg` | Build + create distributable archive |

# License

This source is bound to the original terms from **id Software**. On top of that, I am releasing this source under the Apache 2.0 license. Feel free to use this codebase
as you please, as long as both licenses are bundled and proper credit is given.

# Credits

Jaymod was originally created and maintained by **budjb** and the Jaymod development team. Many thanks to all contributors who worked on the mod over the years — without their effort this codebase would not exist.

The OmniBot integration was originally written by the **OmniBot team** (Omni-Bot project). Their bot framework made it possible to have AI-controlled bots in Enemy Territory.
