# Olly's heartbeat, once a second (cheap: a few selector scans).
# Any dog (vanilla wolf or Doggy Talents dog) named "Olly" becomes Olly.
execute as @e[type=#olly:good_boys,name="Olly",tag=!olly.blessed] at @s run function olly:bless
execute as @e[type=#olly:good_boys,name="olly",tag=!olly.blessed] at @s run function olly:bless

# He fights cows: when a cow is close, Olly gets fired up.
execute as @e[type=#olly:good_boys,tag=olly.blessed] at @s if entity @e[type=minecraft:cow,distance=..10] run function olly:cow_spotted

# Renamed away from Olly? Then he's just a regular good boy again.
execute as @e[type=#olly:good_boys,tag=olly.blessed] unless entity @s[name="Olly"] unless entity @s[name="olly"] run function olly:unbless

schedule function olly:pulse 1s
