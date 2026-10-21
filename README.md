<p align="center"><img src="assets/icon.png" width="96" alt="Olly"></p>

<h1 align="center">Harris ModPack</h1>

<p align="center">
Minecraft taught me everything I know about engineering (and XP farm ethics).<br>
This modpack started as a winter break project to keep my brain from turning to mush.<br>
My dog Olly made it in. He fights cows.
</p>

<p align="center"><b>Minecraft 1.21.1 · NeoForge 21.1 · 85 mods · one-command install</b></p>

---

## What's in it

**Engineering.** [Create](https://modrinth.com/mod/create) with the good add-ons: electricity (Crafts & Additions),
liquid XP (Enchantment Industry), actual cannons (Big Cannons), extra building blocks (Copycats+, Deco, Connected),
and kitchen automation (Slice & Dice, Central Kitchen with Farmer's Delight).

**A bigger world.** Terralith biomes on Tectonic terrain, all of YUNG's structure overhauls, Dungeons & Taverns,
Towns & Towers, and Distant Horizons so you can actually see the mountains.

**Adventure.** The Aether, Mowzie's Mobs and L_Ender's Cataclysm bosses, Naturalist wildlife, Artifacts,
Better Combat with dodge rolls, Waystones, backpacks, gravestones.

**Olly.** The custom part. Name any tamed dog **Olly** and he becomes Olly: bigger, tougher, faster, and he
fights cows. Cows he takes down drop *Olly's Trophy*. Doggy Talents Next lets him level up and learn talents.

**Polish.** A built-in field guide on first join, a custom advancement tab, splash texts, keybind conflicts
already sorted, Complementary shaders one key away (`K`), and a performance stack (Sodium, Lithium, FerriteCore,
ModernFix, Entity Culling, ImmediatelyFast) so it all runs well.

## Install (macOS)

You need [Homebrew](https://brew.sh) and a Minecraft account.

```sh
git clone https://github.com/HarrisJDCampbell/Harris-ModPack.git
cd Harris-ModPack
./install.sh
```

That installs Python, Java 21 and [Prism Launcher](https://prismlauncher.org) if you don't have them, builds a
Prism instance called **Harris ModPack** (8 GB RAM, every mod downloaded and hash-checked), and opens
Prism. First time only: sign in with your Microsoft account in Prism. Then select the pack and hit **Launch**.

**Updating:** `git pull && ./install.sh`. Only changed files are downloaded, and mods that were removed from the
pack are removed from your instance. Your worlds, settings and screenshots are never touched.

**Not on a Mac / using another launcher?** `make export` builds `dist/Harris-ModPack-1.0.0.mrpack`, which imports
straight into Prism, the Modrinth App or ATLauncher on any OS.

## Playing with friends

```sh
make server DIR=~/harris-server
```

Sets up a dedicated NeoForge server with only the server-side mods. Read the
[Minecraft EULA](https://aka.ms/MinecraftEULA), set `eula=true` in `eula.txt`, then `./run.sh nogui`.
Friends join with the same pack version (send them the `.mrpack`).

## Controls worth knowing

| Key | Does |
| --- | --- |
| `R` | Dodge roll |
| `B` | Open backpack |
| `M` / `N` / `U` | World map / new waypoint / waypoint list |
| `K` / `O` | Shaders on/off / pick shader pack |
| `G` / `H` / `I` | Trinket slots (Curios / Accessories / Aether) |
| `W` over a Create item | Ponder (animated tutorial) |
| `R` / `U` over any item | Recipes / uses |

All of it is in the **Harris Field Guide** you spawn with.

## Working on the pack

The pack is plain text managed with [packwiz](https://packwiz.infra.link): every mod is a small `.pw.toml`
file in `pack/mods/` with a download URL and a hash, so git tracks exactly what changed.

```text
pack/            packwiz source of truth (mods, shaders, default configs)
olly/            the Olly mod: functions, advancements, loot, field guide, splashes
scripts/
  modpack.py     install / sync / server / export / check
  smoke_test.py  boots the real game into a test world and checks Olly works
install.sh       one-command macOS install
Makefile         shortcuts (run `make`)
```

| Command | What it does |
| --- | --- |
| `make tools` | Install packwiz (needed to add or update mods) |
| `cd pack && packwiz mr add <slug>` | Add a mod from Modrinth |
| `make outdated` / `make update` | See / apply mod updates |
| `make olly` | Rebuild the Olly jar after editing `olly/` |
| `make check` | Fast checks: hashes, sides, Olly jar up to date |
| `make test` | Launch the game, load a test world, run the Olly checks, quit |
| `make install` | Apply your changes to the Prism instance |

### How Olly works

`olly/` is a NeoForge "lowcode" mod: no Java, just data and assets, packed into a jar so it applies to every
world automatically (no datapack to copy around). A one-second heartbeat function finds tamed wolves or Doggy
Talents dogs named Olly, tags them, and applies permanent attribute modifiers. The cow trophy is a NeoForge
global loot modifier that adds a loot table only when the cow's killer has Olly's tag. The jar is zipped with
fixed timestamps and no compression, so the same source always produces the same bytes and the same hash.

### How the smoke test works

`scripts/smoke_test.py` writes a fresh world's `level.dat` by hand (a tiny NBT writer), drops in a test datapack,
and launches the real client straight into it. The datapack summons a wolf named Olly, checks he got buffed,
kills a cow with him, and confirms the trophy dropped and the field guide was handed out. Each check prints
`SMOKE PASS/FAIL` to the log, which the script watches. It also fails on any load error from the Olly mod or on
a crash.

## Credits

Every mod belongs to its authors. Huge thanks to all of them, see each project's Modrinth page. Built by
Harris Campbell. Olly is a real dog and he is doing great.

The scripts and the Olly mod in this repo are MIT licensed (see `LICENSE`).
