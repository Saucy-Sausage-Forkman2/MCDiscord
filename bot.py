from mcstatus import JavaServer
from mcstatus import BedrockServer
import math
import discord
import os
import asyncio
import json
import datetime
from dotenv import load_dotenv

address="192.168.254.11"
publicAddress="beangod.duckdns.org"
javaPort="26003"
bedrockPort="19132"
load_dotenv()
#loads environment variables from the .env file to hide them from public code
#FILE MUST BE NAMED ".env"
prefix = '.'
   
#end of variable declaration
#------------------------------------------------------------------------
#------------------------------------------------------------------------
#------------------------------------------------------------------------
#functions moved up for my own convenience:


async def formatResponse(java, bedrock):
    zeroServerColor = discord.Colour.red()
    oneServerColor = discord.Colour.yellow()
    twoServerColor = discord.Colour.green()

    bothOnlineTitle = "Minecraft Server is Online"
    onlyJavaTitle = "Java is Online"
    onlyBedrockTitle = "Bedrock is Online"
    bothOfflineTitle = "Server is Offline"

    current_time = datetime.datetime.now()
    hour = current_time.hour
    minute = current_time.minute
    pm = 'AM'
    if hour >= 12:
        pm = "PM"
    if hour > 13:
        hour -= 12


    embed = 0# if embed is not defined outside of the else if chain, it cannot be accessed by anything outside of the chain.
    #So I define it here.
    #both java and bedrock
    if java != 0 and bedrock != 0:
        embed = discord.Embed(
            title=bothOnlineTitle,
            color=twoServerColor,
        )
    #---------------------------------
    #only java, no bedrock
    elif java != 0 and bedrock == 0:
        embed = discord.Embed(
            title=onlyJavaTitle,
            color=oneServerColor,
        )
    #---------------------------------

    #only bedrock, no java
    elif java == 0 and bedrock != 0:
        embed = discord.Embed(
            title=onlyBedrockTitle,
            color=oneServerColor,
        )
        embed.add_field(name="Java", value="",inline=False)
    #---------------------------------
    
     #neither bedrock or java
    elif java == 0 and bedrock == 0:
        embed = discord.Embed(
            title=bothOfflineTitle,
            color=zeroServerColor,
        )

    
        embed.set_footer(text=f"{hour}" + ":"+ f"{minute}" + f"{pm}"+ " PST")

        #We can take a shortcut here since there is no other data to add
        embed.add_field(name="Java", value="Offline")
        embed.add_field(name="",value=publicAddress+":"+javaPort,inline=False)

        embed.add_field(name="",value="",inline=False) # a new line to separate the player fields so it looks nice

        embed.add_field(name="Bedrock", value="Offline")
        embed.add_field(name="",value=publicAddress+":"+bedrockPort,inline=False)

        return embed
            

    #---------------------------------
    
    embed.set_footer(text=f"{hour}" + ":"+ f"{minute}" + f"{pm}"+ " PST")

    #if java is online
    if java != 0:
        #if the server is alive
        ping = math.trunc(java.latency)
        version = java.version.name
        players = java.players.online
        maxPlayers=java.players.max
        javaPlayerList = java.players.sample
        #only java servers provide a list of active players

        embed.add_field(name="Players", value=f"{players}" + "/" + f"{maxPlayers}")
        if javaPlayerList != None:
            #go through the array of usernames and compile them into a list for beauty
            formattedUsernames = ""
            for i in javaPlayerList:
                formattedUsernames += " " + i.name + "\n"
            embed.add_field(name="", value=formattedUsernames,inline=False)
        else: embed.add_field(name="",value="",inline=False) # a new line to separate the player fields so it looks nice
        
        #I placed the player count before the Java server header as it applies to both java and bedrock, and it feels wrong to have the
        #player count only under one or under both. And it has to be exist.
        embed.add_field(name="Java", value="")
        #Putting the game version first as it's the most important for new players, and is important in general
        embed.add_field(name="", value=f"{version}")
        #embed.add_field(name="Ping", value=f"{ping}" + "ms")
        #The java server has more details since both servers run hand in hand, so having all information about both is simply redundant.
        embed.add_field(name="",value=publicAddress+":"+javaPort,inline=False)
    else:
        embed.add_field(name="",value="Server Offline")
        embed.add_field(name="",value=publicAddress+":"+javaPort,inline=False)
    
    embed.add_field(name="",value="",inline=False) # a new line to separate the player fields so it looks nice

    #if bedrock is online
    if bedrock != 0:
        embed.add_field(name="Bedrock", value="")
        ping = math.trunc(bedrock.latency)
        version = bedrock.version.name
        embed.add_field(name="  ", value=f"{version}")
        #embed.add_field(name="Ping", value=f"{ping}" + "ms")
        embed.add_field(name="",value=publicAddress+":"+bedrockPort,inline=False)
    else:
        embed.add_field(name="Bedrock",value="Server Offline")
        embed.add_field(name="",value=publicAddress+":"+bedrockPort,inline=False)
    return embed

#----------------------------------------

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

#-------------------------------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------------------------------------

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    await supervisorLoop()

@client.event
async def on_message(message):
    if message.content.startswith(prefix) and message.author != client.user:
        arguments = message.content[1:].split(" ")
        command = arguments.pop(0)
        if len(arguments) > 0:
            argumentRaw = message.content[1:].split(" ", 1)[1]  

        match command:
            case "ping":
                pendingMessage = await message.channel.send("Pinging...")
                status = await minecraftPing()

                await pendingMessage.edit(content=None,embed=status) 
                #using local ip address since bot will be run from within the 
                #same network as the minecraft server itself
            case "create":
                match(arguments[0]):
                    case "supervisor":
                        with open("status_messages.json","r+") as json_file:
                            pendingMessage = await message.channel.send("Pinging...")
                            data = json.load(json_file)
                            try:
                                if data[f"{pendingMessage.channel.id}"] != pendingMessage.id: data["servers"][pendingMessage.channel.id] = message.id
                            except:
                                data[f"{pendingMessage.channel.id}"] = pendingMessage.id
                            finally:
                                json_file.seek(0)
                                json.dump(data, json_file, indent=4)
                            await pendingMessage.edit(content=None,embed=(await minecraftPing()))

                    case _:
                        await message.channel.send(embed=help())
            case "disable":
                match(arguments[0]):
                    case "supervisor":
                        with open("status_messages.json","r+") as json_file:
                            data = json.load(json_file)
                            try:
                                if data[f"{message.channel.id}"] != null: data["servers"][message.channel.id] = null
                            except:
                                pass
                        message.channel.send("Supervisor disabled.")
                    case _:
                        await message.channel.send(embed=help())
            case _:
                await message.channel.send(embed=help())
                

def help():
    embed = discord.Embed(
        title="Help",
        color=discord.Colour.dark_gray()
    )
    embed.add_field(name=".ping", value="Request the Server's Status")
    embed.add_field(name=".create supervisor", value="Sends the results of a ping, and will update that message periodically. Dhar Mann will only update one supervisor per server, and that is the most recently created one.")
    embed.add_field(name=".disable supervisor", value="Disables the bot from editing the message with the server's status")

    return embed

async def minecraftPing():
    javaStatus = ""
    bedrockStatus = ""

    #Java Status Request
    try:
        #ping the server ip
        javaStatus = await JavaServer.async_lookup(address+":"+javaPort)
        javaStatus = await javaStatus.async_status()
    except:
        #if there is any response other than OK, assume the server is down and request such an embed.
        javaStatus = 0

    #----

    #Bedrock Status Request
    try:
        bedrockStatus = BedrockServer.lookup(address+":"+bedrockPort)
        bedrockStatus = await bedrockStatus.async_status()
    except:
        bedrockStatus = 0
    #---

    return await formatResponse(javaStatus,bedrockStatus)
        
async def supervisorLoop():
    delayInSeconds = 60
    while True:
        with open("status_messages.json","r+") as json_file:
            data = json.load(json_file)
            for i in data:
                ping = await minecraftPing()
                dontcrash = await client.fetch_channel(f'{i}')
                #print(f'Updating supervisor in {dontcrash}')
                dontcrash = await dontcrash.fetch_message(data[f'{i}'])
                dontcrash = await dontcrash.edit(content=None, embed=ping)
            #try:
            #    if data[f"{message.channel.id}"] != null: data["servers"][message.channel.id] = null
            #except:
            #    pass
        await asyncio.sleep(delayInSeconds)

client.run(os.getenv('TOKEN'))