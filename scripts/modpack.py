#!/usr/bin/env python3
"""Harris ModPack tool.

One script that turns the packwiz source in pack/ into something playable:

  modpack.py install            build + install/update the Prism Launcher instance
  modpack.py sync DIR --side S  sync pack files into any game directory (client|server)
  modpack.py server DIR         set up a dedicated NeoForge server in DIR
  modpack.py build-olly         rebuild the Olly mod jar from olly/ (deterministic)
  modpack.py export             write dist/Harris-ModPack-<version>.mrpack (needs packwiz)
  modpack.py check              sanity-check the pack (hashes, sides, Olly jar up to date)

Only needs Python 3.11+ (for tomllib). Mods are downloaded from the URLs in the
.pw.toml metafiles, checked against their hashes, and cached so updates are fast.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
import tomllib
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACK = ROOT / "pack"
OLLY_SRC = ROOT / "olly"
ASSETS = ROOT / "assets"
USER_AGENT = "HarrisJDCampbell/Harris-ModPack (github.com/HarrisJDCampbell/Harris-ModPack)"
MANIFEST_NAME = ".harris-modpack.json"
INSTANCE_ID = "HarrisModPack"
ICON_KEY = "harris_modpack"
JAVA21_CANDIDATES = [
    "/opt/homebrew/opt/openjdk@21/bin/java",
    "/usr/local/opt/openjdk@21/bin/java",
]


# --------------------------------------------------------------------------- #
# Output helpers
# --------------------------------------------------------------------------- #

def say(msg: str) -> None:
    print(f"\033[1;36m==>\033[0m {msg}", flush=True)


def warn(msg: str) -> None:
    print(f"\033[1;33m!!\033[0m  {msg}", flush=True)


def die(msg: str) -> "NoReturn":  # type: ignore[name-defined]
    print(f"\033[1;31mxx\033[0m  {msg}", file=sys.stderr, flush=True)
    sys.exit(1)


# --------------------------------------------------------------------------- #
# Pack model
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class PackFile:
    path: str            # destination path relative to the game dir (e.g. mods/create.jar)
    side: str            # both | client | server
    preserve: bool       # don't overwrite if the user already has the file
    url: str | None      # remote files only
    hash_format: str
    hash: str
    source: Path | None  # local files only


def load_pack() -> tuple[dict, list[PackFile]]:
    pack = tomllib.loads((PACK / "pack.toml").read_text())
    index = tomllib.loads((PACK / pack["index"]["file"]).read_text())
    default_fmt = index.get("hash-format", "sha256")
    files: list[PackFile] = []
    for entry in index.get("files", []):
        rel = entry["file"]
        if entry.get("metafile"):
            meta = tomllib.loads((PACK / rel).read_text())
            dl = meta["download"]
            dest = str(Path(rel).parent / meta["filename"])
            files.append(PackFile(dest, meta.get("side", "both"), bool(entry.get("preserve")),
                                  dl["url"], dl["hash-format"], dl["hash"], None))
        else:
            files.append(PackFile(rel, "both", bool(entry.get("preserve")), None,
                                  entry.get("hash-format", default_fmt), entry["hash"], PACK / rel))
    return pack, files


def file_hash(path: Path, fmt: str) -> str:
    h = hashlib.new(fmt)
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def cache_dir() -> Path:
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Caches"
    elif os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home()))
    else:
        base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    d = base / "HarrisModPack" / "downloads"
    d.mkdir(parents=True, exist_ok=True)
    return d


def fetch(pf: PackFile) -> Path:
    """Download a remote file into the content-addressed cache and verify it."""
    assert pf.url
    cached = cache_dir() / f"{pf.hash_format}-{pf.hash}"
    if cached.exists() and file_hash(cached, pf.hash_format) == pf.hash:
        return cached
    tmp = cached.with_suffix(".part")
    last_err: Exception | None = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(pf.url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=60) as r, tmp.open("wb") as out:
                shutil.copyfileobj(r, out)
            got = file_hash(tmp, pf.hash_format)
            if got != pf.hash:
                raise ValueError(f"hash mismatch for {pf.path}: expected {pf.hash[:12]}…, got {got[:12]}…")
            tmp.replace(cached)
            return cached
        except Exception as e:  # network hiccups are common; retry with backoff
            last_err = e
            time.sleep(1.5 * (attempt + 1))
    tmp.unlink(missing_ok=True)
    raise RuntimeError(f"failed to download {pf.path}: {last_err}")


# --------------------------------------------------------------------------- #
# Syncing files into a game directory
# --------------------------------------------------------------------------- #

def sync(game_dir: Path, side: str, *, quiet: bool = False) -> dict:
    """Make game_dir match the pack for the given side. Returns the pack.toml dict."""
    build_olly(quiet=True)
    pack, files = load_pack()
    wanted = [f for f in files if f.side in ("both", side)]
    game_dir.mkdir(parents=True, exist_ok=True)

    remote = [f for f in wanted if f.url]
    if not quiet:
        say(f"Checking {len(remote)} downloads (cached in {cache_dir()})")
    sources: dict[str, Path] = {}
    with cf.ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(fetch, f): f for f in remote}
        for i, fut in enumerate(cf.as_completed(futures), 1):
            pf = futures[fut]
            sources[pf.path] = fut.result()
            if not quiet:
                print(f"\r    {i}/{len(remote)}", end="", flush=True)
    if not quiet and remote:
        print()

    installed: list[str] = []
    changed = 0
    for pf in wanted:
        dest = game_dir / pf.path
        src = sources.get(pf.path) or pf.source
        assert src is not None
        if pf.source is not None and file_hash(src, pf.hash_format) != pf.hash:
            die(f"{pf.path} doesn't match index.toml. Run `make refresh` (packwiz refresh) first.")
        if pf.preserve and dest.exists():
            continue
        if dest.exists() and file_hash(dest, pf.hash_format) == pf.hash:
            installed.append(pf.path)
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
        installed.append(pf.path)
        changed += 1

    # Remove files a previous version of the pack installed but this one doesn't.
    manifest_path = game_dir / MANIFEST_NAME
    removed = 0
    if manifest_path.exists():
        old = json.loads(manifest_path.read_text()).get("files", [])
        keep = {f.path for f in wanted}
        for rel in old:
            if rel not in keep and (game_dir / rel).is_file():
                (game_dir / rel).unlink()
                removed += 1
    manifest_path.write_text(json.dumps({
        "pack": pack["name"], "version": pack["version"], "side": side,
        "files": sorted(installed),
    }, indent=2) + "\n")

    if not quiet:
        say(f"{len(installed)} files in place ({changed} updated, {removed} removed)")
    return pack


# --------------------------------------------------------------------------- #
# Olly mod (code-free NeoForge mod built from olly/)
# --------------------------------------------------------------------------- #

def olly_version() -> str:
    toml = tomllib.loads((OLLY_SRC / "META-INF" / "neoforge.mods.toml").read_text())
    return toml["mods"][0]["version"]


def olly_jar_bytes() -> bytes:
    """Zip olly/ with fixed timestamps and no compression so the bytes (and the
    hash packwiz records) are identical on every machine and Python version."""
    import io
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_STORED) as z:
        for p in sorted(OLLY_SRC.rglob("*")):
            if p.is_dir() or p.name == ".DS_Store":
                continue
            info = zipfile.ZipInfo(p.relative_to(OLLY_SRC).as_posix(), date_time=(1980, 1, 1, 0, 0, 0))
            info.external_attr = 0o644 << 16
            z.writestr(info, p.read_bytes())
    return buf.getvalue()


def build_olly(*, quiet: bool = False) -> Path:
    jar = PACK / "mods" / f"olly-{olly_version()}.jar"
    data = olly_jar_bytes()
    stale = [p for p in (PACK / "mods").glob("olly-*.jar") if p != jar]
    if jar.exists() and jar.read_bytes() == data and not stale:
        if not quiet:
            say(f"{jar.name} is up to date")
        return jar
    for p in stale:
        p.unlink()
    jar.write_bytes(data)
    say(f"Built {jar.relative_to(ROOT)}")
    refresh()
    return jar


def refresh() -> None:
    if shutil.which("packwiz") is None:
        die("packwiz is needed to refresh pack/index.toml. Install it with `make tools`.")
    subprocess.run(["packwiz", "refresh"], cwd=PACK, check=True, stdout=subprocess.DEVNULL)


# --------------------------------------------------------------------------- #
# Prism Launcher instance
# --------------------------------------------------------------------------- #

def prism_dir() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "PrismLauncher"
    if os.name == "nt":
        return Path(os.environ["APPDATA"]) / "PrismLauncher"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "PrismLauncher"


def find_java21() -> str | None:
    for c in JAVA21_CANDIDATES:
        if Path(c).exists():
            return c
    return None


def write_instance(inst: Path, pack: dict, memory_mb: int) -> None:
    versions = pack["versions"]
    java = find_java21()
    cfg = {
        "ConfigVersion": "1.2",
        "InstanceType": "OneSix",
        "name": pack["name"],
        "iconKey": ICON_KEY,
        "notes": "Managed by Harris ModPack. Update with `make install` in the repo.",
        "OverrideMemory": "true",
        "MinMemAlloc": "2048",
        "MaxMemAlloc": str(memory_mb),
        "OverrideJavaArgs": "true",
        # Generational ZGC: short GC pauses = fewer stutters with a big modded heap.
        "JvmArgs": "-XX:+UseZGC -XX:+ZGenerational",
        "OverrideWindow": "true",
        "LaunchMaximized": "false",
        "MinecraftWinWidth": "1600",
        "MinecraftWinHeight": "960",
    }
    if java:
        cfg |= {"OverrideJavaLocation": "true", "JavaPath": java, "IgnoreJavaCompatibility": "false"}
    existing = {}
    cfg_path = inst / "instance.cfg"
    if cfg_path.exists():
        # Keep anything Prism (or the player) added, like play time and last launch.
        for line in cfg_path.read_text().splitlines():
            if "=" in line and not line.startswith("["):
                k, v = line.split("=", 1)
                existing[k] = v
    merged = existing | cfg
    cfg_path.write_text("[General]\n" + "".join(f"{k}={v}\n" for k, v in merged.items()))

    mmc_pack = {
        "components": [
            {"important": True, "uid": "net.minecraft", "version": versions["minecraft"]},
            {"uid": "net.neoforged", "version": versions["neoforge"]},
        ],
        "formatVersion": 1,
    }
    (inst / "mmc-pack.json").write_text(json.dumps(mmc_pack, indent=2) + "\n")


def cmd_install(args: argparse.Namespace) -> None:
    prism = Path(args.prism_dir) if args.prism_dir else prism_dir()
    inst = prism / "instances" / INSTANCE_ID
    say(f"Installing into Prism instance: {inst}")
    if subprocess.run(["pgrep", "-qx", "prismlauncher"]).returncode == 0:
        warn("Prism Launcher is running. That's fine, but restart it if the instance doesn't refresh.")
    inst.mkdir(parents=True, exist_ok=True)
    pack = sync(inst / "minecraft", "client")
    write_instance(inst, pack, args.memory)
    icon = ASSETS / "icon.png"
    if icon.exists():
        (prism / "icons").mkdir(parents=True, exist_ok=True)
        shutil.copyfile(icon, prism / "icons" / f"{ICON_KEY}.png")
    if not find_java21():
        warn("Java 21 not found at the Homebrew path; Prism will ask to download one on first launch.")
    say(f"{pack['name']} {pack['version']} is ready. Open Prism Launcher and hit Launch.")


# --------------------------------------------------------------------------- #
# Dedicated server
# --------------------------------------------------------------------------- #

def cmd_server(args: argparse.Namespace) -> None:
    server = Path(args.dir).resolve()
    pack = sync(server, "server")
    nf = pack["versions"]["neoforge"]
    if not (server / "run.sh").exists() or args.reinstall:
        java = find_java21() or shutil.which("java") or die("Java 21 is required (brew install openjdk@21)")
        url = f"https://maven.neoforged.net/releases/net/neoforged/neoforge/{nf}/neoforge-{nf}-installer.jar"
        installer = cache_dir() / f"neoforge-{nf}-installer.jar"
        if not installer.exists():
            say(f"Downloading NeoForge {nf} installer")
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=120) as r, installer.open("wb") as out:
                shutil.copyfileobj(r, out)
        say("Running NeoForge server installer")
        subprocess.run([java, "-jar", str(installer), "--install-server", str(server)],
                       cwd=server, check=True, stdout=subprocess.DEVNULL)
        java_args = server / "user_jvm_args.txt"
        java_args.write_text(f"-Xms2G\n-Xmx{args.memory}M\n-XX:+UseZGC\n-XX:+ZGenerational\n")
    if not (server / "eula.txt").exists() or "eula=true" not in (server / "eula.txt").read_text():
        warn("Before the first start, read https://aka.ms/MinecraftEULA and set eula=true in eula.txt")
    say(f"Server ready in {server}. Start it with: cd '{server}' && ./run.sh nogui")


# --------------------------------------------------------------------------- #
# Export + checks
# --------------------------------------------------------------------------- #

def cmd_export(args: argparse.Namespace) -> None:
    build_olly()
    refresh()
    pack, _ = load_pack()
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    out = dist / f"Harris-ModPack-{pack['version']}.mrpack"
    subprocess.run(["packwiz", "modrinth", "export", "-o", str(out)], cwd=PACK, check=True)
    say(f"Wrote {out.relative_to(ROOT)} (import it in Prism, the Modrinth App, or ATLauncher)")


def cmd_check(args: argparse.Namespace) -> None:
    problems = 0
    jar = PACK / "mods" / f"olly-{olly_version()}.jar"
    if not jar.exists() or jar.read_bytes() != olly_jar_bytes():
        warn(f"{jar.name} is out of date with olly/ (run `make olly`)")
        problems += 1
    pack, files = load_pack()
    for pf in files:
        if pf.source is not None:
            if not pf.source.exists():
                warn(f"missing local file {pf.path}")
                problems += 1
            elif file_hash(pf.source, pf.hash_format) != pf.hash:
                warn(f"stale hash in index.toml for {pf.path} (run `make refresh`)")
                problems += 1
        if pf.side not in ("both", "client", "server"):
            warn(f"bad side '{pf.side}' on {pf.path}")
            problems += 1
    seen: dict[str, str] = {}
    for pf in files:
        if pf.path in seen:
            warn(f"duplicate destination {pf.path}")
            problems += 1
        seen[pf.path] = pf.path
    mods = sum(1 for f in files if f.path.startswith("mods/"))
    say(f"{pack['name']} {pack['version']}: {mods} mods, {len(files)} files, {problems} problem(s)")
    sys.exit(1 if problems else 0)


def main() -> None:
    if sys.version_info < (3, 11):
        die("Python 3.11+ is required (brew install python)")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("install", help="install/update the Prism Launcher instance")
    p.add_argument("--memory", type=int, default=8192, help="max RAM in MB (default 8192)")
    p.add_argument("--prism-dir", help="Prism data dir (auto-detected by default)")
    p.set_defaults(func=cmd_install)

    p = sub.add_parser("sync", help="sync pack files into a game directory")
    p.add_argument("dir")
    p.add_argument("--side", choices=["client", "server"], default="client")
    p.set_defaults(func=lambda a: sync(Path(a.dir).resolve(), a.side))

    p = sub.add_parser("server", help="set up a dedicated server")
    p.add_argument("dir")
    p.add_argument("--memory", type=int, default=6144)
    p.add_argument("--reinstall", action="store_true", help="re-run the NeoForge installer")
    p.set_defaults(func=cmd_server)

    sub.add_parser("build-olly", help="rebuild the Olly mod jar").set_defaults(func=lambda a: build_olly())
    sub.add_parser("export", help="export a .mrpack").set_defaults(func=cmd_export)
    sub.add_parser("check", help="sanity-check the pack").set_defaults(func=cmd_check)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
