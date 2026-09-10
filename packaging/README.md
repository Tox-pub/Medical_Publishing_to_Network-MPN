# Packaging

Build tooling for distributing **MPN**. Nothing here is imported by the
application or the pipeline; these scripts only assemble releases.

| File | Purpose |
| --- | --- |
| `build_location.py` | The single output location every build script resolves. |
| `build_portable_windows.py` | Assembles the Windows application tree and zips it. Run this first. |
| `build_msi_windows.py` | Wraps that tree in an `.msi`. |
| `windows_msi.wxs` | The WiX source it compiles. |
| `build_unix_bundle.py` | The self-contained Linux and macOS tarballs. |
| `verify_windows_bundle.py`, `verify_unix_bundle.py` | Check a build before it is published. |
| `launchers/` | The `.bat` files copied verbatim into the Windows tree. |
| `install.sh` | Installs a source checkout into a private virtual environment on Linux or macOS. |
| `make_icon.py` | Redraws the application icon into `src/mpn/assets/`. |
| `make_third_party_notices.py` | Regenerates `THIRD-PARTY-NOTICES.md` from a built bundle. |
| `sync_notebooks.py` | Regenerates `src/mesh_aop_notebooks/` from the modules. |
| `where_are_my_files.py` | Prints where a copy keeps its settings, data and results. |

## Output location

Every build writes to **`D:\mpn_build`**, resolved through `build_location.py`.
The location is outside the project because the working copy is cloud-synced and
a build tree is about 460 MB of reproducible output; `.gitignore` stops git, not
the sync client.

**If D: is not attached, the build stops** and writes nothing. To build
elsewhere deliberately, pass `--out <path>` for one run, or set `MESH_BUILD_OUT`
for a session. CI sets `MESH_BUILD_OUT`, because a runner has no D:.

Downloads reused between builds (the embeddable CPython for Windows, and the
python-build-standalone interpreters for Linux and macOS) are cached in `_cache`
inside the output location.

## Building a release

Build all four artefacts from the same commit, in this order:

```
python packaging/build_portable_windows.py
python packaging/build_msi_windows.py
python packaging/build_unix_bundle.py --target linux
python packaging/build_unix_bundle.py --target macos-arm
```

`build_msi_windows.py` wraps the most recent portable tree in the output location
and writes the `.msi` beside it; `--portable` and `--out` override both.

Verify every artefact before hashing or uploading it:

```
python packaging/verify_windows_bundle.py D:\mpn_build\MPN-<version>-win64-portable.zip D:\mpn_build\MPN-<version>-win64.msi
python packaging/verify_unix_bundle.py D:\mpn_build\MPN-<version>-linux-x86_64.tar.gz D:\mpn_build\MPN-<version>-macos-arm64.tar.gz
```

| Artefact | Size | For |
| --- | --- | --- |
| `MPN-<version>-win64.msi` | ~90 MB | Windows. `msiexec` performs the install, and it is signed by Microsoft. |
| `MPN-<version>-win64-portable.zip` | ~112 MB | Windows without installing, or where the installer is refused. Contains `Install.bat`. |
| `MPN-<version>-linux-x86_64.tar.gz` | ~211 MB | Linux, self-contained: its own CPython, Tk and wheels. |
| `MPN-<version>-macos-arm64.tar.gz` | ~162 MB | macOS on Apple silicon, the same shape. **Unvalidated:** assembled on Windows and not yet run on a Mac. |

Options for `build_portable_windows.py`: `--out` (output location), `--repo`
(project directory), `--venv` (environment to copy dependencies from; defaults
to the interpreter running the script), `--base-python` (full CPython install to
take the Tk runtime from), `--no-zip`.

Options for `build_unix_bundle.py`: `--target` (`linux`, `linux-arm`,
`macos-arm`, `macos-intel`), `--all`, `--out`, `--full-python` (unstripped
interpreter), `--repack` (re-archive an assembled staging folder without
downloading anything).

### The Windows tree

```
MPN/
  MPN.bat                             launcher
  MPN (Troubleshooting).bat           the same, with a console attached
  mpn-pipeline.bat                    the pipeline without the window
  Install.bat, Uninstall.bat, Create desktop shortcut.bat
  README - Install and First Run.txt
  portable.marker                     keeps settings, data and results in this folder
  python/                             embeddable CPython + Tk
  app/                                mpn, mesh_aop, reference data
```

### The installer

The MSI installs **the same tree the zip contains**, minus the `.bat` files,
`portable.marker` and the portable README, so the only program that executes is
still the PSF-signed `python.exe`. Shortcuts point at `pythonw.exe app\launch.py`,
so no console appears. It installs per user: there is no administrator prompt
and nothing for a managed machine to refuse.

Uninstalling through Windows removes what the installer wrote, then offers to
run the application's own uninstaller for the downloaded data and the
temp-folder workspace, which Windows would otherwise leave behind at tens of
gigabytes. Results are kept.

The MSI spends a while on "Computing space requirements". It carries one
component per file, nearly ten thousand of them; that is `CostFinalize` working,
not a hang.

Building the MSI requires WiX 5 and its two extensions at the same version:

```
dotnet tool install --global wix --version 5.0.2
wix extension add --global WixToolset.UI.wixext/5.0.2
wix extension add --global WixToolset.Util.wixext/5.0.2
```

WiX 6 and later require accepting a paid licence agreement.

## Repository or release

**The repository holds source only:** build scripts, launchers, the WiX source
and the icon generator. Everything needed to *produce* an artefact is here, and
none of the artefacts themselves.

**The release holds the artefacts.** GitHub rejects any file over 100 MB in a
repository, while release assets are capped at 2 GB each. A binary committed to
git history stays there permanently, and every clone pays for it.

## Publishing

1. **Confirm the version agrees everywhere it is declared.** After changing it,
   `git grep -n "<previous version>"` must return nothing outside history. It
   is declared in `pyproject.toml`, `CITATION.cff`, `src/mesh_aop/__init__.py`,
   `src/mesh_aop/citation.py`, `src/mpn/__init__.py`, `src/mpn/app.py`,
   `packaging/build_portable_windows.py`, `packaging/build_msi_windows.py`,
   `packaging/windows_msi.wxs`, `packaging/install.sh`,
   `packaging/launchers/Install.bat` and `INSTALL.md`; `build_unix_bundle.py`
   reads it from `pyproject.toml`. A mismatch produces an asset whose name
   disagrees with its tag, and a wrong `AppVersion` breaks in-place MSI
   upgrades.
2. **Build and verify** all four artefacts, as above.
3. **Hash them**, so a download can be verified:

   ```
   certutil -hashfile "D:\mpn_build\MPN-<version>-win64.msi" SHA256
   ```

4. **Tag the exact commit** the artefacts were built from, and push the tag:

   ```
   git tag -a v<version> -m "MPN <version>"
   git push origin v<version>
   ```

   A pushed tag runs the release workflow, which builds the MSI and both
   tarballs and tests each on a real Windows, Linux or macOS runner. It does not
   publish anything.

5. **Publish.** On GitHub: **Releases → Draft a new release**, choose the tag,
   attach the four files, paste the checksums into the notes, and publish. With
   the `gh` CLI:

   ```
   gh release create v<version> --title "MPN <version>" --notes-file notes.md *.msi *.zip *.tar.gz
   ```

   Running the release workflow by hand with `publish` ticked creates the
   release from the CI build instead. That release carries the MSI and the two
   tarballs, but not the portable zip.

## Why an interpreter rather than a frozen executable

The only program a user runs is `python.exe` from the official embeddable
distribution, **signed by the Python Software Foundation**. That side-steps the
whole trust problem: no code-signing certificate to buy, no SmartScreen
reputation to earn, and none of the antivirus false positives PyInstaller
bundles routinely attract. On a managed Windows device a newly built unsigned
binary can be refused outright, while a signed interpreter runs normally.

Dependencies are copied from a working virtual environment rather than installed
fresh, so a release ships the exact versions the published results were produced
with.

### Three things that break the Windows build if changed carelessly

1. **`Lib` must stay on the path in `python3xx._pth`.** The embeddable build
   serves the standard library from a zip and puts only `.` on `sys.path`, so
   anything added under `Lib/` (which is how tkinter arrives) is invisible
   without it.
2. **Do not prune directories that look like test suites.** `numpy.testing` is
   public API that scipy imports while loading; removing it breaks every
   scipy-dependent import.
3. **Keep `.dist-info`.** Several packages, plotly among them, read their own
   version through `importlib.metadata` and raise without it.

The embeddable package also ships **without tkinter**, so `add_tkinter()` copies
`Lib/tkinter`, `_tkinter.pyd`, the Tcl/Tk DLLs and the `tcl/` runtime from a full
CPython install of the same version.

## macOS and Linux

```
python packaging/build_unix_bundle.py --target linux
python packaging/build_unix_bundle.py --target macos-arm
```

Self-contained tarballs carrying their own CPython, Tk and every wheel, so the
first run installs offline (`--no-index`) and needs nothing from the machine.
The Linux bundle also adds a `.desktop` entry to the applications menu.

For anyone who already has Python, installing a source checkout with
`packaging/install.sh` or `pip install .` is the lighter route on either
platform.

**The macOS bundle is unvalidated.** It is assembled on Windows and has not been
run on a Mac. `verify_unix_bundle.py` checks what can be checked from the
outside (the executable bit NTFS cannot store, wheels built for the wrong Python
or architecture, a launcher written with CRLF), but that is not the same as
running it, and the documentation states as much until a Mac run confirms it.
