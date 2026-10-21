# Runs on world load and /reload. Kicks off Olly's heartbeat.
schedule clear olly:pulse
schedule function olly:pulse 1s
