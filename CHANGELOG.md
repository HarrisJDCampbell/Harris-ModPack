# Changelog

## 1.1.0

- **Confetti creepers.** Creepers explode into confetti instead of blowing up. Toggle in
  `config/harris-common.toml` or Mods > Harris > Config.
- **Mum's Shepherd's Pie**, with its own pixel art, recipe and advancement.
- **Olly is Olly-sized**: a bit smaller than a wolf. Existing Ollys shrink automatically.
- New Harris Java mod (`mod/`), text-file pixel art (`make art`) and an image-to-texture tool
  (`make pixelize`).
- **Removed Distant Horizons.** Its bundled native SQLite library corrupted memory on macOS and crashed
  the game shortly after joining a world, on both Homebrew's and Mojang's Java. Default render distance
  goes from 12 to 16 chunks to make up for it.
- Smoke test now also checks confetti creepers, Olly's size and the pie.

## 1.0.0

First release.

- Minecraft 1.21.1 on NeoForge 21.1.264, 85 mods.
- Create plus Crafts & Additions, Enchantment Industry, Big Cannons, Copycats+, Deco, Connected,
  Slice & Dice and Central Kitchen.
- Terralith 2.6.2 + Tectonic terrain, all YUNG's structure mods, Dungeons & Taverns, Towns & Towers,
  Distant Horizons.
- The Aether, Mowzie's Mobs, L_Ender's Cataclysm, Naturalist, Artifacts, Better Combat, Combat Roll.
- Olly mod: name a dog Olly for buffs, cow rivalry and trophy drops; Harris advancement tab;
  Harris Field Guide and starter kit on first join; custom splash texts.
- Default options with keybind conflicts fixed (dodge roll vs shader reload, backpack vs waypoint).
- Complementary Reimagined and BSL shaders included, off by default (`K` to toggle).
- One-command macOS install into Prism Launcher, `.mrpack` export, dedicated server setup,
  and an in-game smoke test.
