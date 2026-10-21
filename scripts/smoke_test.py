#!/usr/bin/env python3
"""Boot the real modded client into a throwaway world and check the pack works.

What it does:
  1. Syncs the client pack into .test/client (same code path as `make install`).
  2. Writes a fresh creative test world (level.dat built by hand, see write_level_dat)
     plus a tiny test datapack that exercises the Olly mod.
  3. Launches NeoForge offline with portablemc and quick-plays straight into the world.
  4. Watches the log for PASS/FAIL lines, mod errors and crashes, then quits the game.

Run it with `make test`. Needs portablemc (installed into .test/venv automatically)
and Java 21. A Minecraft window opens for ~1-2 minutes; leave it alone.
"""

from __future__ import annotations

import gzip
import io
import re
import shutil
import struct
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import modpack  # noqa: E402

ROOT = modpack.ROOT
TEST = ROOT / ".test"
GAME = TEST / "client"
WORLD_NAME = "SmokeTest"
TIMEOUT_S = 420

# Checks the test datapack reports. Each must print "SMOKE PASS <name>".
EXPECTED = ["olly_blessed", "olly_buffed", "olly_sized", "olly_trophy", "guide_book", "advancements",
            "creeper_confetti", "surprise_party", "shepherds_pie"]

# Log lines that mean something in our own content is broken.
FATAL_PATTERNS = [
    r"Failed to load function olly:",
    r"Couldn't parse element .*olly:",
    r"Couldn't load advancement olly:",
    r"Parsing error loading .*olly",
    r"Couldn't parse data file olly:",
    r"Failed to load book olly:",
    r"\[olly\].*(ERROR|Exception)",
    r"Failed to load function harris:",
    r"Couldn't parse element .*harris:",
    r"Couldn't load advancement harris:",
    r"Parsing error loading recipe harris:",
]


# --------------------------------------------------------------------------- #
# Minimal NBT writer: just enough to build a level.dat
# --------------------------------------------------------------------------- #

class Byte(int): pass
class Int(int): pass
class Long(int): pass


def _nbt_payload(v) -> tuple[int, bytes]:
    if isinstance(v, Byte):
        return 1, struct.pack(">b", v)
    if isinstance(v, Long):
        return 4, struct.pack(">q", v)
    if isinstance(v, (Int, int)) and not isinstance(v, bool):
        return 3, struct.pack(">i", v)
    if isinstance(v, str):
        b = v.encode()
        return 8, struct.pack(">H", len(b)) + b
    if isinstance(v, list):
        if not v:
            return 9, struct.pack(">bi", 8, 0)
        tags = [_nbt_payload(x) for x in v]
        return 9, struct.pack(">bi", tags[0][0], len(v)) + b"".join(p for _, p in tags)
    if isinstance(v, dict):
        out = io.BytesIO()
        for k, x in v.items():
            tid, payload = _nbt_payload(x)
            kb = k.encode()
            out.write(struct.pack(">bH", tid, len(kb)) + kb + payload)
        out.write(b"\x00")
        return 10, out.getvalue()
    raise TypeError(type(v))


def write_level_dat(world: Path) -> None:
    """A brand-new 1.21.1 world: the game generates terrain on first load, using
    whatever worldgen mods are installed (Terralith/Tectonic included)."""
    noise = lambda settings, source: {"type": "minecraft:noise", "settings": settings, "biome_source": source}
    data = {
        "DataVersion": Int(3955),
        "version": Int(19133),
        "LevelName": WORLD_NAME,
        "GameType": Int(1),
        "Difficulty": Byte(1),
        "allowCommands": Byte(1),
        "hardcore": Byte(0),
        "initialized": Byte(0),
        # Modded worldgen can count as "experimental"; skip the warning screen that
        # would otherwise sit there waiting for a click.
        "confirmedExperimentalSettings": Byte(1),
        "Version": {"Id": Int(3955), "Name": "1.21.1", "Series": "main", "Snapshot": Byte(0)},
        "DataPacks": {"Enabled": ["vanilla"], "Disabled": []},
        "WorldGenSettings": {
            "seed": Long(8675309),
            "generate_features": Byte(1),
            "bonus_chest": Byte(0),
            "dimensions": {
                "minecraft:overworld": {"type": "minecraft:overworld", "generator": noise(
                    "minecraft:overworld", {"type": "minecraft:multi_noise", "preset": "minecraft:overworld"})},
                "minecraft:the_nether": {"type": "minecraft:the_nether", "generator": noise(
                    "minecraft:nether", {"type": "minecraft:multi_noise", "preset": "minecraft:nether"})},
                "minecraft:the_end": {"type": "minecraft:the_end", "generator": noise(
                    "minecraft:end", {"type": "minecraft:the_end"})},
            },
        },
    }
    tid, payload = _nbt_payload({"Data": data})
    raw = struct.pack(">bH", tid, 0) + payload
    world.mkdir(parents=True, exist_ok=True)
    (world / "level.dat").write_bytes(gzip.compress(raw))


# --------------------------------------------------------------------------- #
# Test datapack
# --------------------------------------------------------------------------- #

TEST_FUNCTIONS = {
    # Give the world a few seconds to settle, then run the checks.
    "load": "schedule function smoke:start 100t\n",
    "start": """\
say SMOKE START
forceload add ~ ~
tp @a ~ ~1 ~
summon minecraft:wolf ~2 ~ ~ {CustomName:'"Olly"',Tags:["smoke.dog"],PersistenceRequired:1b}
# Give him an owner so the owner greeting + advancement path runs too.
data modify entity @e[type=minecraft:wolf,tag=smoke.dog,limit=1] Owner set from entity @p UUID
schedule function smoke:check_bless 60t
""",
    "check_bless": """\
execute if entity @e[type=minecraft:wolf,tag=smoke.dog,tag=olly.blessed] run say SMOKE PASS olly_blessed
execute unless entity @e[type=minecraft:wolf,tag=smoke.dog,tag=olly.blessed] run say SMOKE FAIL olly_blessed
execute as @e[type=minecraft:wolf,tag=smoke.dog] if data entity @s attributes[{id:"minecraft:generic.max_health"}].modifiers[{id:"olly:good_boy_health"}] run say SMOKE PASS olly_buffed
execute as @e[type=minecraft:wolf,tag=smoke.dog] unless data entity @s attributes[{id:"minecraft:generic.max_health"}].modifiers[{id:"olly:good_boy_health"}] run say SMOKE FAIL olly_buffed
execute as @e[type=minecraft:wolf,tag=smoke.dog] if data entity @s attributes[{id:"minecraft:generic.scale"}].modifiers[{id:"olly:olly_sized"}] run say SMOKE PASS olly_sized
execute as @e[type=minecraft:wolf,tag=smoke.dog] unless data entity @s attributes[{id:"minecraft:generic.scale"}].modifiers[{id:"olly:olly_sized"}] run say SMOKE FAIL olly_sized
summon minecraft:cow ~4 ~ ~ {Tags:["smoke.cow"],NoAI:1b}
execute as @e[type=minecraft:cow,tag=smoke.cow] run damage @s 1000 minecraft:mob_attack by @e[type=minecraft:wolf,tag=smoke.dog,limit=1]
schedule function smoke:check_trophy 20t
""",
    "check_trophy": """\
execute if entity @e[type=minecraft:item,nbt={Item:{components:{"minecraft:custom_data":{olly_trophy:1b}}}}] run say SMOKE PASS olly_trophy
execute unless entity @e[type=minecraft:item,nbt={Item:{components:{"minecraft:custom_data":{olly_trophy:1b}}}}] run say SMOKE FAIL olly_trophy
execute if entity @a[nbt={Inventory:[{id:"patchouli:guide_book"}]}] run say SMOKE PASS guide_book
execute unless entity @a[nbt={Inventory:[{id:"patchouli:guide_book"}]}] run say SMOKE FAIL guide_book
execute if entity @a[advancements={olly:root=true,olly:good_boy=true}] run say SMOKE PASS advancements
execute unless entity @a[advancements={olly:root=true,olly:good_boy=true}] run say SMOKE FAIL advancements
schedule function smoke:creeper 10t
""",
    # A lit creeper right next to a glass block: a real explosion would break the
    # glass; a confetti creeper leaves it standing and just disappears.
    "creeper": """\
setblock ~8 ~ ~1 minecraft:glass
summon minecraft:creeper ~8 ~ ~ {Tags:["smoke.creeper"],Fuse:5s,ignited:1b,NoAI:1b}
give @a harris:mums_shepherds_pie
schedule function smoke:check_creeper 40t
""",
    "check_creeper": """\
execute unless entity @e[tag=smoke.creeper] if block ~8 ~ ~1 minecraft:glass run say SMOKE PASS creeper_confetti
execute unless block ~8 ~ ~1 minecraft:glass run say SMOKE FAIL creeper_confetti
execute if entity @e[tag=smoke.creeper] run say SMOKE FAIL creeper_confetti
execute if entity @a[advancements={harris:surprise_party=true}] run say SMOKE PASS surprise_party
execute unless entity @a[advancements={harris:surprise_party=true}] run say SMOKE FAIL surprise_party
execute if entity @a[nbt={Inventory:[{id:"harris:mums_shepherds_pie"}]}] run say SMOKE PASS shepherds_pie
execute unless entity @a[nbt={Inventory:[{id:"harris:mums_shepherds_pie"}]}] run say SMOKE FAIL shepherds_pie
say SMOKE DONE
""",
}


def write_test_datapack(world: Path) -> None:
    dp = world / "datapacks" / "smoke"
    shutil.rmtree(dp, ignore_errors=True)
    (dp / "data" / "smoke" / "function").mkdir(parents=True)
    (dp / "data" / "minecraft" / "tags" / "function").mkdir(parents=True)
    (dp / "pack.mcmeta").write_text('{"pack":{"pack_format":48,"description":"smoke test"}}\n')
    (dp / "data" / "minecraft" / "tags" / "function" / "load.json").write_text('{"values":["smoke:load"]}\n')
    for name, body in TEST_FUNCTIONS.items():
        (dp / "data" / "smoke" / "function" / f"{name}.mcfunction").write_text(body)


# --------------------------------------------------------------------------- #
# Launch + watch
# --------------------------------------------------------------------------- #

def portablemc() -> Path:
    venv = TEST / "venv"
    exe = venv / "bin" / "portablemc"
    if not exe.exists():
        modpack.say("Setting up portablemc in .test/venv")
        subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
        subprocess.run([str(venv / "bin" / "pip"), "install", "-q", "portablemc"], check=True)
    return exe


def main() -> int:
    java = modpack.find_java21() or modpack.die("Java 21 not found (brew install openjdk@21)")
    pack = modpack.sync(GAME, "client")

    world = GAME / "saves" / WORLD_NAME
    shutil.rmtree(world, ignore_errors=True)
    write_level_dat(world)
    write_test_datapack(world)

    log = GAME / "logs" / "latest.log"
    log.unlink(missing_ok=True)
    shutil.rmtree(GAME / "crash-reports", ignore_errors=True)

    nf = pack["versions"]["neoforge"]
    cmd = [str(portablemc()), "--main-dir", str(TEST / "mc"), "start", f"neoforge::{nf}",
           "--mc-dir", str(GAME), "--jvm", java, "--jvm-arg=" + ",".join(["-Xmx8G", "-Xms2G", *modpack.GC_ARGS]),
           "-u", "SmokeTester", "--join-world", WORLD_NAME]
    modpack.say(f"Launching {pack['name']} {pack['version']} (a game window will open)")
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    results: dict[str, str] = {}
    fatal: list[str] = []
    start = time.time()
    seen = 0
    try:
        while time.time() - start < TIMEOUT_S:
            time.sleep(2)
            if (GAME / "crash-reports").exists() and any((GAME / "crash-reports").iterdir()):
                fatal.append("game crashed (see .test/client/crash-reports)")
                break
            if proc.poll() is not None:
                fatal.append(f"game exited early with code {proc.returncode}")
                break
            if not log.exists():
                continue
            lines = log.read_text(errors="replace").splitlines()
            for line in lines[seen:]:
                m = re.search(r"SMOKE (PASS|FAIL) (\w+)", line)
                if m and "[CHAT]" not in line:
                    results[m.group(2)] = m.group(1)
                for pat in FATAL_PATTERNS:
                    if re.search(pat, line):
                        fatal.append(line.strip())
            seen = len(lines)
            if "SMOKE DONE" in "\n".join(lines):
                break
        else:
            fatal.append(f"timed out after {TIMEOUT_S}s")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=20)
        except subprocess.TimeoutExpired:
            proc.kill()
        subprocess.run(["pkill", "-f", "SmokeTester"], check=False)

    print()
    for name in EXPECTED:
        status = results.get(name, "MISSING")
        mark = "\033[32mPASS\033[0m" if status == "PASS" else f"\033[31m{status}\033[0m"
        print(f"  {mark}  {name}")
    for line in dict.fromkeys(fatal):
        print(f"  \033[31mERROR\033[0m {line}")
    ok = not fatal and all(results.get(n) == "PASS" for n in EXPECTED)
    print()
    modpack.say("Smoke test passed" if ok else "Smoke test FAILED (full log: .test/client/logs/latest.log)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
