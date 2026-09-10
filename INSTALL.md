# Installing MPN (Medical Publishing to Network)

**One file per system.** Download the file for the system in use from
[Releases](https://github.com/Tox-pub/Medical_Publishing_to_Network-MPN/releases).
The others are not needed.

| System | File | What to do |
| :--- | :--- | :--- |
| **Windows** | `MPN-3.2.10-win64.msi` | Double-click it. |
| **Windows, without installing** | `MPN-3.2.10-win64-portable.zip` | Extract, then double-click `MPN.bat`. |
| **Linux** | `MPN-3.2.10-linux-x86_64.tar.gz` | Extract, then run `./"MPN"`. It adds itself to the applications menu. |
| **macOS** | `MPN-3.2.10-macos-arm64.tar.gz` | Extract, then run `./"MPN"` from Terminal. |

**Every build carries its own Python.** Nothing needs installing first: no
system Python, no `python3-tk`, no administrator rights, and nothing is written
outside the user's own profile.

- [Windows](#windows)
- [Linux](#linux)
- [macOS](#macos)
- [If a download is blocked](#if-a-download-is-blocked)
- [Where things are kept](#where-things-are-kept)
- [Updating](#updating)
- [Removing it](#removing-it)

---

## Windows

### Installer

Double-click `MPN-3.2.10-win64.msi`. It asks where to install, offers desktop
and Start-menu shortcuts, and adds an entry to Add/Remove Programs.

The installer carries its own Python and is executed by `msiexec.exe`, which is
part of Windows and signed by Microsoft. On a managed machine this matters: a
newly built `.exe` installer has no signature and no reputation, and Defender
Exploit Guard can refuse it outright with `0x80070005`. An MSI introduces no new
binary.

To install silently, for deployment to several machines:

```
msiexec /i "MPN-3.2.10-win64.msi" /qn
```

### Portable zip

Extract `MPN-3.2.10-win64-portable.zip` to any writable folder, open the
extracted `MPN` folder and double-click `MPN.bat`. Nothing is installed.

| File | Purpose |
| :--- | :--- |
| `MPN.bat` | Starts the application. |
| `MPN (Troubleshooting).bat` | Starts the same application with a console attached, so error messages stay on screen. |
| `Create desktop shortcut.bat` | Adds a desktop icon that points at this folder. |
| `Install.bat` | Copies the program into the user profile, with a Start-menu entry and an Add/Remove Programs entry. |
| `mpn-pipeline.bat` | Runs the pipeline from a shell. See [COMMAND-LINE.md](COMMAND-LINE.md). |
| `Uninstall.bat` | Removes the program's data outside the folder. |

---

## Linux

Download `MPN-3.2.10-linux-x86_64.tar.gz`, then:

```
tar -xzf MPN-3.2.10-linux-x86_64.tar.gz
cd MPN-3.2.10-linux-x86_64
./"MPN"
```

The folder carries its own Python, its own Tk and every library, already
compiled. **No system Python and no `python3-tk` are required.** The first run
unpacks the libraries from `wheels/`, takes about a minute, and needs no
network.

**MPN appears in the applications menu after the first launch.** A `.desktop`
entry must name an absolute path, which is not known until the folder is
unpacked, so the launcher writes the entry on first run, to
`~/.local/share/applications/mpn.desktop`. This needs no root and writes nothing
outside the home directory, and the entry is rewritten if the folder moves.
`./mpn-uninstall` removes it. If the desktop does not show the entry
immediately, log out and back in.

To run without a desktop:

```
./mpn-pipeline --step all
```

---

## macOS

**MPN runs on a Mac without an Apple Developer account or any payment.**

Download `MPN-3.2.10-macos-arm64.tar.gz` (Apple silicon) and extract it. Open
**Terminal**, change to the extracted folder and run:

```
./"MPN"
```

### Why Terminal, and not a double-click

macOS tags every file downloaded through a browser with a
`com.apple.quarantine` attribute, and Gatekeeper refuses to run unsigned
programs that carry it. MPN is unsigned, because signing requires a paid Apple
Developer ID, so the attribute must be cleared once.

Clearing it needs **no password, no Apple account and no payment**. The launcher
clears it: the launcher is a shell script, read by macOS's own signed `/bin/sh`,
so it is not blocked itself and can clear the attribute from everything else in
the folder. It reports this on the first run.

Start the first run from Terminal, not Finder. Finder either opens the script in
a text editor or refuses it. After the first run, either works.

### Clearing the attribute by hand

To clear the attribute without the launcher:

```
xattr -dr com.apple.quarantine "/path/to/MPN-3.2.10-macos-arm64"
```

This removes one extended attribute from the files in that folder and changes
nothing else. `xattr` is part of macOS.

### If macOS still refuses

On macOS Sequoia and later, open **System Settings → Privacy & Security**,
scroll to the bottom, and press **Open Anyway** next to the blocked item. The
button appears only after the first refusal.

### Intel Macs

The published build is for Apple silicon. An Intel build is produced with
`python packaging/build_unix_bundle.py --target macos-intel` and can be added to
a release on request.

---

## If a download is blocked

Two different things can stop a downloaded file from running.

**A warning that can be dismissed.** *"Windows protected your PC"* means
SmartScreen has not seen the file before. Click **More info → Run anyway**. This
is expected for any installer without a purchased code-signing certificate.

**A refusal that cannot be dismissed.** *"Blocked an operation that is not
allowed by your IT administrator"*, or error `0x80070005`, means a security
policy, usually Defender Exploit Guard, has refused the file because it is a
newly compiled, unsigned executable. There is nothing to click through.

Use the `.msi` in that case. It is executed by `msiexec.exe`, which is part of
Windows and signed by Microsoft, so no unsigned binary is introduced. Where the
MSI is refused as well, use the portable zip: the only program it runs is
`python.exe`, signed by the Python Software Foundation.

**A file copied over the network** may also be flagged. Right-click it →
**Properties** → tick **Unblock** → **OK**. This is the most common reason a
copied download appears to do nothing.

---

## Where things are kept

An installed copy keeps each user's settings and results separate. A portable
copy keeps everything inside its own folder.

| | Installed (Windows) | Portable (Windows) |
| --- | --- | --- |
| Program | `%LOCALAPPDATA%\Programs\MPN` | the extracted folder |
| Settings | `%LOCALAPPDATA%\MPN\mesh_config.json` | `mesh_config.json` in that folder |
| Results | `Documents\MPN` | `results` in that folder |
| Downloaded data | `%LOCALAPPDATA%\MPN\data`, or the folder set on the Folders tab | `data` in that folder |

On Linux, settings and downloaded data default to `~/.local/share/MPN`, and on
macOS to `~/Library/Application Support/MPN`. Results default to
`~/Documents/MPN` on both.

A portable copy is self-contained because it carries a file named
`portable.marker`. Deleting that file makes it behave as an installed copy.

**The downloaded data is the large part:** about 50 GB for the PubMed archive and
10 GB for the database built from it. Set the data folder on the **Folders** tab
before starting a download, on a drive with room.

---

## Updating

**Installer:** install the new `.msi` over the old version. It replaces the
program in place and keeps settings and results.

**Portable zip:** extract the new zip to a new folder, move `mesh_config.json`,
`data` and `results` across from the old folder, then delete the old folder.

**Linux and macOS:** extract the new tarball. Settings, data and results live
outside the program folder, so the new copy finds them; delete the old folder.

---

## Removing it

**Installed (Windows):** Settings → Apps → MPN → Uninstall.

This keeps the downloaded PubMed data by default, because it is large and slow
to fetch again, and always clears the temporary working copy that the database
build leaves in the Windows temp folder. To remove the downloaded data as well:

```
msiexec /x "MPN-3.2.10-win64.msi" REMOVEDATA=1
```

**Windows portable zip:** run `Uninstall.bat`, then delete the folder.

**Linux and macOS:** run the uninstaller from the extracted folder, then delete
the folder.

```
cd MPN-3.2.10-linux-x86_64
```

```
./mpn-uninstall
```

The uninstaller removes what the program put **outside** its own folder:
settings and downloaded data under `~/.local/share/MPN`
(`~/Library/Application Support/MPN` on macOS), the applications-menu entry
and, when requested, the results. It lists everything with sizes and asks before
removing anything.

Then delete the folder, which is the program itself:

```
rm -rf MPN-3.2.10-linux-x86_64
```

**A downloaded build has nothing to `pip uninstall`.** The bundle carries its own
Python and puts the application on that interpreter's path without installing
it.

**Installed from source with pip:** run `mpn-uninstall` to clear the data, then
`python -m pip uninstall mpn` with the same interpreter the package was
installed into.

Results are never removed without an explicit request.

To list what is on disk before deciding, without changing anything:

```
mpn-uninstall --list
```

The list covers every file the program downloaded, built or installed, with
sizes, including the files outside the program folder that would otherwise be
left behind.
