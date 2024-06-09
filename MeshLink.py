# dont change unless you are making a fork
update_check_url = "https://raw.githubusercontent.com/Murturtle/MeshLink/main/rev"
update_url = "https://github.com/Murturtle/MeshLink"
rev = 2
import yaml
import xml.dom.minidom# dont change unless you are making a fork
update_check_url = "https://raw.githubusercontent.com/Murturtle/MeshLink/main/rev"
update_url = "https://github.com/Murturtle/MeshLink"
rev = 4
import yaml
import xml.dom.minidom
import os
from pubsub import pub
import discord
from meshtastic.tcp_interface import TCPInterface
from meshtastic.serial_interface import SerialInterface
import asyncio
import time
import requests

with open("./config.yml",'r') as file:
    config = yaml.safe_load(file)

config_options = [
    "max_message_length",
    "channel_ids",
    "message_channel_ids",
    "info_channel_ids",
    "token",
    "prefix",
    "discord_prefix",
    "use_serial",
    "radio_ip",
    "send_channel_index",
    "ignore_self",
    "send_packets",
    "verbose_packets",
    "weather_lat",
    "weather_long",
    "max_weather_hours",
    "ping_on_messages",
    "message_role",
]

for i in config_options:
    if i not in config:
        print("Config option "+i+" missing in config.yml (check github for example)")
        exit()

for i in config:
    if i not in config_options:
        print("Config option "+i+" is not needed anymore")

oversion = requests.get(update_check_url)
if(oversion.ok):
    if(rev < int(oversion.text)):
        for i in range(10):
            print("New MeshLink update ready "+update_url)

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

def send_msg(message):
    global config
    print(message)
    if (client._ready):
        for i in config["message_channel_ids"]:
            asyncio.run_coroutine_threadsafe(client.get_channel(i).send(message),client.loop)
        for i in config["info_channel_ids"]:
            asyncio.run_coroutine_threadsafe(client.get_channel(i).send(message),client.loop)

def send_info(message):
    global config
    print(message)
    if (client._ready):
        for i in config["info_channel_ids"]:
            asyncio.run_coroutine_threadsafe(client.get_channel(i).send(message),client.loop)

def asdf(a):
    print("ACK")
    print(a)

def onConnection(interface, topic=pub.AUTO_TOPIC):
    print("Node ready")
    interface.sendText("ready",channelIndex = config["send_channel_index"])
    #a = interface.sendText("hola!")
    #print(a.id)
    #interface._addResponseHandler(a.id,asdf)

    #print(a)

def genUserName(interface, packet):
    if(packet["fromId"] in interface.nodes):
        if(interface.nodes[packet["fromId"]]["user"]):
            ret = str("`"+str(interface.nodes[packet["fromId"]]["user"]["shortName"]))+" "+packet["fromId"]+"` "+str(interface.nodes[packet["fromId"]]["user"]["longName"])
        else:
            ret = str(packet["fromId"])
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
        return "`"+str(packet["fromId"])+"`"


def onReceive(packet, interface):
    if(config["verbose_packets"]):
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
            
            if(config["ping_on_messages"]):
                final_message += "\n||"+config["message_role"]+"||"

            if(text.startswith(config["prefix"])):
                noprefix = text[len(config["prefix"]):]

                if(noprefix.startswith("ping")):
                    interface.sendText("pong",channelIndex=config["send_channel_index"])
                
                elif (noprefix.startswith("help")):
                    interface.sendText("ping\n"
                                       +"time\n"
                                       +"weather\n"
                                       +"hf"
                                       ,channelIndex=config["send_channel_index"])
                
                elif (noprefix.startswith("time")):
                    interface.sendText(str(time.localtime()),channelIndex=config["send_channel_index"])
                
                elif (noprefix.startswith("weather")):
                    weather_data_res = requests.get("https://api.open-meteo.com/v1/forecast?latitude="+config["weather_lat"]+"&longitude="+config["weather_long"]+"&hourly=temperature_2m,precipitation_probability&temperature_unit=fahrenheit&wind_speed_unit=mph&precipitation_unit=inch&timeformat=unixtime")
                    weather_data = weather_data_res.json()
                    final_weather = ""
                    if (weather_data_res.ok):
                        for j in range(config["max_weather_hours"]):
                                i = j+int(time.strftime('%H'))
                                final_weather += str(int(i)%24)+" "
                                final_weather += str(round(weather_data["hourly"]["temperature_2m"][i]))+"F "+str(weather_data["hourly"]["precipitation_probability"][i])+"%🌧️\n"
                        final_weather = final_weather[:-1]
                    else:
                        final_weather += "error fetching"
                    print(final_weather)
                    interface.sendText(final_weather,channelIndex=config["send_channel_index"])
                
                elif (noprefix.startswith("hf")):
                    final_hf = ""
                    solar = requests.get("https://www.hamqsl.com/solarxml.php")
                    if(solar.ok):
                        solarxml = xml.dom.minidom.parseString(solar.text)
                        for i in solarxml.getElementsByTagName("band"):
                            final_hf += i.getAttribute("time")[0]+i.getAttribute("name") +" "+str(i.childNodes[0].data)+"\n"
                        final_hf = final_hf[:-1]
                    else:
                        final_hf += "error fetching"
                    print(final_hf)
                    interface.sendText(final_hf,channelIndex=config["send_channel_index"])
            send_msg(final_message)
        else:
            if(config["send_packets"]):
                if((packet["fromId"] == interface.getMyNodeInfo()["user"]["id"]) & config["ignore_self"]):
                    print("Ignoring self")
                else:
                    final_message+=genUserName(interface,packet)+"> "+str(packet["decoded"]["portnum"])
            send_info(final_message)
    else:
        final_message+=genUserName(interface,packet)+"> encrypted/failed"
        send_info(final_message)
        print("failed or encrypted")




pub.subscribe(onConnection, "meshtastic.connection.established")
pub.subscribe(onReceive, "meshtastic.receive")

if (config["use_serial"]):
    interface = SerialInterface()
else:
    interface = TCPInterface(hostname=config["radio_ip"], connectNow=True)
@client.event
async def on_ready():   
    print('Logged in as {0.user}'.format(client))
    #send_msg("ready")



@client.event
async def on_message(message):
    global interface
    if message.author == client.user:
        return
    if message.content.startswith(config["discord_prefix"]+'send'):
        if (message.channel.id in config["message_channel_ids"]):
            await message.channel.typing()
            trunk_message = message.content[len(config["discord_prefix"]+"send"):]
            final_message = message.author.name+">"+ trunk_message
            
            if(len(final_message) < config["max_message_length"] - 1):
                await message.reply(final_message)
                interface.sendText(final_message,channelIndex = config["send_channel_index"])
                print(final_message)
            else:
                await message.reply("(trunked) "+final_message[:config["max_message_length"]])
                interface.sendText(final_message,channelIndex = config["send_channel_index"])
                print(final_message[:config["max_message_length"]])
            
        else:
            return

try:
    client.run(config["token"])
except discord.HTTPException as e:
    if e.status == 429:
        print("too many requests")
    else:
        raise e
    