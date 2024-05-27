# MeshLink
## Features

 - Send messages to and from discord
 
 ### Mesh only
 - Weather forecast
 - Ping

### WIP
- SOS

## Commands
**prefix + command**
### Discord
send (message)

### Mesh
ping
weather

## Setup 

 1. Download the python script from Github
 2. Install the Meshtastic python CLI https://meshtastic.org/docs/software/python/cli/installation/
 3. Install discord py https://discordpy.readthedocs.io/en/latest/intro.html
 4. Create a discord bot https://discord.com/developers
 5. Give it admin permission in your server and give it read messages intent (google it if you don't know what to do)
 6. Invite it to a server
 7. Get the discord channel id (this is where the messages will go) (again google a tutorial if don't know how to get the channel id)
 8. Get the discord bot token
 9. Edit the python file to configure the settings
 10. Put in the discord bot token and channel id
 11. If you are using serial set `use_serial` to `True` otherwise get your nodes ip and put it into the `radio_ip` setting
 12. Run the script

## Suggestions/Feature Requests
Put them in issues.
