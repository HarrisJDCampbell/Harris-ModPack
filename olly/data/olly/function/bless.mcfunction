# Turns the executing dog into Olly. Runs once per dog (tag-guarded).
tag @s add olly.blessed
attribute @s minecraft:generic.max_health modifier add olly:good_boy_health 20 add_value
attribute @s minecraft:generic.attack_damage modifier add olly:good_boy_bite 4 add_value
attribute @s minecraft:generic.movement_speed modifier add olly:good_boy_zoomies 0.15 add_multiplied_base
attribute @s minecraft:generic.scale modifier add olly:good_boy_size 0.15 add_multiplied_base
effect give @s minecraft:instant_health 1 4 true
particle minecraft:heart ~ ~1 ~ 0.6 0.5 0.6 0 12
playsound minecraft:entity.player.levelup neutral @a[distance=..16] ~ ~ ~ 0.6 1.6
execute on owner run function olly:owner_greeting
