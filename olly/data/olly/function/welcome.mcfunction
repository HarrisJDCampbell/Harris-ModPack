# First join: starter kit + field guide. Reward of olly:root, so it runs once per player.
give @s patchouli:guide_book[patchouli:book="olly:field_guide"]
give @s minecraft:name_tag[minecraft:custom_name='"Olly"',minecraft:lore=['{"text":"Use on a dog. Trust me.","color":"gray","italic":true}']]
give @s doggytalents:training_treat 3
give @s minecraft:bone 6
give @s minecraft:bread 8
tellraw @s ["",{"text":"\n  Welcome to ","color":"gray"},{"text":"Harris ModPack","color":"gold","bold":true},{"text":"!\n","color":"gray"},{"text":"  Read the ","color":"gray"},{"text":"Harris Field Guide","color":"aqua"},{"text":" in your inventory. Tame a wolf, name it ","color":"gray"},{"text":"Olly","color":"gold"},{"text":", and see what happens.\n","color":"gray"}]
