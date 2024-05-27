max_message_length = 170 #max discord -> mesh message length
channel_id = 1234567890123456789 # discord channel id
token = "DISCORD BOT TOKEN" # discord bot token - DO NOT SHARE
prefix = "?" #mesh command prefix
discord_prefix = "$" #discord prefix
use_serial = True
radio_ip="192.168.1.123"
send_channel_index = 0
ignore_self = True #dont show your own node in the mesh
send_packets = True #show all data not just messages
verbose_packets = False #should the full packet data be shown in the console
weather_lat = "45.5"
weather_long = "-122.7"
max_weather_hours = 4 # how many hours ahead to send weather info for

# dont change 
update_check_url = "https://raw.githubusercontent.com/Murturtle/MeshLink/main/rev"
update_url = "https://github.com/Murturtle/MeshLink"
rev = 0
import os
from pubsub import pub
import discord
from meshtastic.tcp_interface import TCPInterface
from meshtastic.serial_interface import SerialInterface
import asyncio
import time
import requests

oversion = requests.get(update_check_url)
if(oversion.ok):
    if(rev < int(oversion.text)):
        for i in range(10):
            print("New MeshLink update ready "+update_url)

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

def send_msg(message):
    global channel_id
    print(message)
    if (client._ready):
        asyncio.run_coroutine_threadsafe(client.get_channel(channel_id).send(message),client.loop)

def onConnection(interface, topic=pub.AUTO_TOPIC):
        interface.sendText("ready",channelIndex = send_channel_index)

def genUserName(interface, packet):
    if(packet["fromId"] in interface.nodes):
        ret = str("**`"+str(interface.nodes[packet["fromId"]]["user"]["shortName"])) +"`** *"+str(interface.nodes[packet["fromId"]]["user"]["longName"]+"*")
        if("position" in interface.nodes[packet["fromId"]]):
            if("latitude" in interface.nodes[packet["fromId"]]["position"] and "longitude" in interface.nodes[packet["fromId"]]["position"]):
                ret +=" [map](<https://www.google.com/maps/search/?api=1&query="+str(interface.nodes[packet["fromId"]]["position"]["latitude"])+"%2C"+str(interface.nodes[packet["fromId"]]["position"]["longitude"])+">)"
        
        
        if("hopLimit" in packet):
            if("hopStart" in packet):
                ret+=" `"+str(packet["hopStart"]-packet["hopLimit"])+"`/`"+str(packet["hopStart"])+"`"
            else:
                ret+=" `"+str(packet["hopLimit"])+"`"
        
        return ret
    else:
        return str(packet["fromId"])


def onReceive(packet, interface):
    if(verbose_packets):
        print("############################################")
        print(packet)
        print("--------------------------------------------")
    final_message = ""
    if("decoded" in packet):
        
        print("decoded")
        if(packet["decoded"]["portnum"] == "TEXT_MESSAGE_APP"):
            final_message += genUserName(interface,packet)

            text = packet["decoded"]["text"]
            final_message += "> "+text
            if(text.startswith(prefix)):
                noprefix = text[len(prefix):]

                if(noprefix.startswith("ping")):
                    interface.sendText("pong",channelIndex=send_channel_index)
                
                elif (noprefix.startswith("help")):
                    interface.sendText("ping\n"
                                       +"time\n"
                                       +"weather\n"
                                       ,channelIndex=send_channel_index)
                
                elif (noprefix.startswith("time")):
                    interface.sendText(str(time.localtime()),channelIndex=send_channel_index)
                
                elif (noprefix.startswith("weather")):
                    response = requests.get("https://api.open-meteo.com/v1/forecast?latitude="+weather_lat+"&longitude="+weather_long+"&hourly=temperature_2m,precipitation_probability&temperature_unit=fahrenheit&wind_speed_unit=mph&precipitation_unit=inch&timeformat=unixtime")
                    weather_data = response.json()
                    final_weather = ""
                    if (response.ok):
                        for i in range(max_weather_hours):
                            final_weather += str(round(weather_data["hourly"]["temperature_2m"][i]))+"t "+str(weather_data["hourly"]["precipitation_probability"][i])+"p\n"
                    else:
                        final_weather += "error fetching"
                    print(final_weather)
                    interface.sendText(final_weather,channelIndex=send_channel_index)

        else:
            if(send_packets):
                if((packet["fromId"] == interface.getMyNodeInfo()["user"]["id"]) & ignore_self):
                    print("Ignoring self")
                else:
                    final_message+=genUserName(interface,packet)+"> "+str(packet["decoded"]["portnum"])
        send_msg(final_message)
    else:
        final_message+=genUserName(interface,packet)+"> encrypted"
        send_msg(final_message)
        print("failed or encrypted")


pub.subscribe(onConnection, "meshtastic.connection.established")
pub.subscribe(onReceive, "meshtastic.receive")
if (use_serial):
    interface = SerialInterface()
else:
    interface = TCPInterface(hostname=radio_ip, connectNow=True)
@client.event
async def on_ready():   
    print('Logged in as {0.user}'.format(client))
    await client.get_channel(channel_id).send("ready")


@client.event
async def on_message(message):
    global interface
    if message.author == client.user:
        return
    if message.content.startswith(discord_prefix+'send'):
        if (message.channel.id == channel_id):
            await message.channel.typing()
            trunk_message = message.content[len(discord_prefix+"send"):]
            final_message = message.author.name+">"+ trunk_message
            
            if(len(final_message) < max_message_length - 1):
                await message.reply(final_message)
                interface.sendText(final_message,channelIndex = send_channel_index)
                print(final_message)
            else:
                await message.reply("(trunked) "+final_message[:max_message_length])
                interface.sendText(final_message,channelIndex = send_channel_index) 
                print(final_message[:max_message_length])
            
        else:
            return

try:
    client.run(token)
except discord.HTTPException as e:
    if e.status == 429:
        print("too many requests")
    else:
        raise e
    
