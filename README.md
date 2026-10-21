<p align="center"><img src="assets/icon.png" width="96" alt="Olly"></p>

<h1 align="center">Harris ModPack</h1>

<p align="center">
Minecraft taught me everything I know about engineering (and XP farm ethics).<br>
This modpack started as a winter break project to keep my brain from turning to mush.<br>
My dog Olly made it in. He fights cows.
</p>

<p align="center"><b>Minecraft 1.21.1 · NeoForge 21.1 · 84 mods + 2 of our own · one-command install</b></p>

---

## Get it running

**Mac** (needs [Homebrew](https://brew.sh) and a Minecraft account):

```sh
git clone https://github.com/HarrisJDCampbell/Harris-ModPack.git
cd Harris-ModPack
./install.sh
```

1. The script installs whatever's missing (Java 21, [Prism Launcher](https://prismlauncher.org)), downloads
   and hash-checks every mod, and builds a Prism instance called **Harris ModPack** with 8 GB of RAM.
2. Prism opens. First time only: finish its setup screens, then **Accounts → Add Microsoft** and sign in.
3. Select **Harris ModPack** → **Launch**.

**Update:** `git pull && ./install.sh`. Only changed mods download; your worlds and settings are left alone.

**Windows / Linux:** install [Prism Launcher](https://prismlauncher.org) and Python 3.11+, clone the repo, then
run `python3 scripts/modpack.py install`. Prism offers to download Java on first launch.

**Other launchers (Modrinth App, ATLauncher):** `make export` (needs `make tools` once) builds
`dist/Harris-ModPack-<version>.mrpack`; import that file.

## What's in it

**Engineering.** [Create](https://modrinth.com/mod/create) with the good add-ons: electricity (Crafts & Additions),
liquid XP (Enchantment Industry), actual cannons (Big Cannons), extra building blocks (Copycats+, Deco, Connected),
and kitchen automation (Slice & Dice, Central Kitchen with Farmer's Delight).

**A bigger world.** Terralith biomes on Tectonic terrain, all of YUNG's structure overhauls, Dungeons & Taverns,
and Towns & Towers.

**Adventure.** The Aether, Mowzie's Mobs and L_Ender's Cataclysm bosses, Naturalist wildlife, Artifacts,
Better Combat with dodge rolls, Waystones, backpacks, gravestones.

**Olly.** The custom part. Name any tamed dog **Olly** and he becomes Olly: Olly-sized (a bit smaller than a
wolf, like the real one), tougher, faster, and he fights cows. Cows he takes down drop *Olly's Trophy*. Doggy
Talents Next lets him level up and learn talents.

**The funny stuff.** Creepers still sneak up and hiss, then explode into **confetti**: no crater, no damage,
just a party (toggle in `config/harris-common.toml`). **Mum's Shepherd's Pie** is its own food item with its own
pixel art, and it's the best food in the game.

**Polish.** A built-in field guide on first join, a custom advancement tab, splash texts, keybind conflicts
already sorted, Complementary shaders one key away (`K`), and a performance stack (Sodium, Lithium, FerriteCore,
ModernFix, Entity Culling, ImmediatelyFast) so it all runs well.

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
mod/             the Harris Java mod (NeoForge, Gradle): confetti creepers, Mum's Shepherd's Pie
art/             pixel art as text files, rendered into textures by `make art`
scripts/
  modpack.py     install / sync / server / export / check
  smoke_test.py  boots the real game into a test world and checks everything works
  pixelart.py    art/*.txt -> PNG textures
  pixelize.py    any image (drawings, photos) -> clean 16x16 texture
install.sh       one-command macOS install
Makefile         shortcuts (run `make`)
```

| Command | What it does |
| --- | --- |
| `make tools` | Install packwiz (needed to add or update mods) |
| `cd pack && packwiz mr add <slug>` | Add a mod from Modrinth |
| `make outdated` / `make update` | See / apply mod updates |
| `make olly` | Rebuild the Olly jar after editing `olly/` |
| `make mod` | Build the Harris Java mod into the pack (needs Java 21) |
| `make art` | Render `art/*.txt` into textures |
| `make pixelize IN=pic.png NAME=item` | Turn any image into a 16x16 item texture |
| `make check` | Fast checks: hashes, sides, Olly jar up to date |
| `make test` | Launch the game, load a test world, run the Olly checks, quit |
| `make install` | Apply your changes to the Prism instance |

### How Olly works

`olly/` is a NeoForge "lowcode" mod: no Java, just data and assets, packed into a jar so it applies to every
world automatically (no datapack to copy around). A one-second heartbeat function finds tamed wolves or Doggy
Talents dogs named Olly, tags them, and applies permanent attribute modifiers. The cow trophy is a NeoForge
global loot modifier that adds a loot table only when the cow's killer has Olly's tag. The jar is zipped with
fixed timestamps and no compression, so the same source always produces the same bytes and the same hash.

### Making art

Two ways to get a texture in:

- **Draw it as text.** `art/mums_shepherds_pie.txt` is a palette plus a 16x16 grid of letters. `make art`
  renders every file in `art/` to its PNG. Easy to tweak one pixel and see the diff in git.
- **Bring a picture.** Draw it anywhere, or grab any picture, then
  `make pixelize IN=~/Downloads/thing.png NAME=thing`. Big "pixel art" images are usually ~1024px with a wobbly grid
  and hundreds of colours, so a plain resize looks like mush. The script removes the background, cuts the image
  to a small palette, then picks each output pixel by majority vote of the block it covers, which keeps edges
  crisp. A 16x preview lands in `.test/art/`.

### How the Harris mod works

`mod/` is a normal NeoForge 1.21.1 mod. Confetti creepers listen for `ExplosionEvent.Start`, which fires before
any block or entity is touched; if the exploder is a creeper, the event is cancelled and the server sends one
packet telling clients to spawn a burst of confetti particles (white sprites tinted a random party colour on the
client). The pie is a regular food item with effects, a recipe and a tooltip. The jar is built with fixed
timestamps so rebuilding unchanged code gives the same hash.

### How the smoke test works

`scripts/smoke_test.py` writes a fresh world's `level.dat` by hand (a tiny NBT writer), drops in a test datapack,
and launches the real client straight into it. The datapack summons a wolf named Olly, checks he got buffed,
kills a cow with him, and confirms the trophy dropped and the field guide was handed out. It also lights a real
creeper next to a glass block and passes only if the glass survives. Each check prints
`SMOKE PASS/FAIL` to the log, which the script watches. It also fails on any load error from the Olly mod or on
a crash.

## Credits

Every mod belongs to its authors. Huge thanks to all of them, see each project's Modrinth page. Built by
Harris Campbell. Olly is a real dog and he is doing great.

The scripts and the Olly mod in this repo are MIT licensed (see `LICENSE`).
