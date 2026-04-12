# Jaymod

This is the source for the last release of Jaymod, which is version 2.0.0.

# Credits

Jaymod was originally created and maintained by **budjb** and the Jaymod development team. Many thanks to all contributors who worked on the mod over the years — without their effort this codebase would not exist.

The OmniBot integration was originally written by the **OmniBot team** (Omni-Bot project). Their bot framework made it possible to have AI-controlled bots in Enemy Territory.

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

The mod has a very powerful make system that can cross-compile the mod for Linux, Windows (via mingw) and OSX. There are also specialty binaries for specific CPU
platforms for each of these platforms.

Information about the build system can be found in the [build system notes](https://raw.githubusercontent.com/budjb/jaymod/master/notes/BuildSystem.txt).

Some of the compilation and system libraries required to make a complete build have been lost to time. If anyone would like to minimalize the build system and provide
compilation instructions, it would be much appreciated.

To build the Windows DLL with MinGW:

```
mingw32-make.exe PLATFORM=mingw "GCC/=/path/to/mingw32/"
```

# License

This source is bound to the original terms from **id Software**. On top of that, I am releasing this source under the Apache 2.0 license. Feel free to use this codebase
as you please, as long as both licenses are bundled and proper credit is given.

