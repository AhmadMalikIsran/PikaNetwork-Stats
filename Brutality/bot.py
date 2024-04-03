import discord
from discord.ext import commands
import json
from imgurpython import ImgurClient
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from datetime import datetime

# Imgur credentials
client_id = 'a01573b7bc5befa'
client_secret = 'fd972db08ae08dcff40c208d6198b9a433ec0865'
FONT_PATH = "path/to/font.ttf"



intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='$', intents=intents)

snipe_list = []

def get_minecraft_info(username):
    # Example URL to fetch Minecraft info
    url = f"https://api.example.com/minecraft/player/{username}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            # Extracting relevant information
            skin_url = data.get('skin_url')
            player_uuid = data.get('uuid')
            player_name = data.get('display_name')
            # Additional info you want to include in the embed
            player_level = data.get('level')
            player_health = data.get('health')
            player_location = data.get('location')

            return {
                'skin_url': skin_url,
                'uuid': player_uuid,
                'display_name': player_name,
                'level': player_level,
                'health': player_health,
                'location': player_location
            }
        else:
            return None
    except Exception as e:
        print(f"Error fetching Minecraft info: {e}")
        return None
    

@bot.command()
async def bw(ctx, playerIGN, interval, mode):
    # Bedwars API URL
    bw_api_url = f"https://stats.pika-network.net/api/profile/{playerIGN}/leaderboard?type=bedwars&interval={interval}&mode={mode}"
    
    # Fetch data from the Bedwars API
    response = requests.get(bw_api_url)
    if response.status_code == 200:
        bw_data = response.json()
        
        # Extract relevant stats
        stats = {
            "Kills": bw_data.get("Kills", {}).get("entries", [])[0].get("value", 0),
            "Final Kills": bw_data.get("Final kills", {}).get("entries", [])[0].get("value", 0) if bw_data.get("Final kills", {}).get("entries", []) else 0,
            "Wins": bw_data.get("Wins", {}).get("entries", [])[0].get("value", 0),
            "Losses": bw_data.get("Losses", {}).get("entries", [])[0].get("value", 0),
            "Deaths": bw_data.get("Deaths", {}).get("entries", [])[0].get("value", 0),
            "WinStreak": bw_data.get("Highest winstreak reached", {}).get("entries", [])[0].get("value", 0)
        }
        
        # Get player's skin
        skin_url = await get_skin(playerIGN)
        
        # Generate image with stats and player's info
        img = generate_bw_stats_image(stats, playerIGN, skin_url)
        
        # Send image as attachment
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        file = discord.File(fp=img_bytes, filename=f"{playerIGN}_stats.png")
        await ctx.send(file=file)
    elif response.status_code == 400:
        await ctx.send("The player is not registered in the PikaNetwork database.")
    else:
        await ctx.send("There was a mistake in the link.")


def generate_bw_stats_image(stats, playerIGN, skin_url):
    # Load font
    font = ImageFont.truetype("arial.ttf", size=20)
    
    # Load background image
    background = Image.open("background.png")
    
    # Create a blank image with white background
    img = Image.new("RGB", (600, 400), color=(255, 255, 255))
    
    # Paste the background image onto the blank image
    img.paste(background, (0, 0))
    
    draw = ImageDraw.Draw(img)
    
    # Add player's name
    draw.text((50, 10), f"Player: {playerIGN}", fill=(0, 0, 0), font=font)
    
    # Add player's image (skin)
    if skin_url:
        skin_response = requests.get(skin_url)
        if skin_response.status_code == 200:
            skin_img = Image.open(BytesIO(skin_response.content))
            skin_img = skin_img.resize((100, 200))  # Adjust the size of the skin image
            img.paste(skin_img, (50, 30))  # Position the skin image
    
    # Add stats with translucent soft background
    y = 50
    for stat, value in stats.items():
        color = get_stat_color(stat)
        translucent_color = (192, 192, 192, 150)  # Adjust opacity here (150 for example)
        draw.rectangle([(50, y), (300, y + 20)], fill=translucent_color)  # Translucent soft background
        draw.text((55, y), f"{stat}:", fill=(0, 0, 0), font=font)
        if stat == "Highest Win Streak":
            draw.text((200, y), f"{value}", fill=color, font=font)
        else:
            draw.text((200, y), f"{value}", fill=color, font=font)
        y += 30
    
    return img



def get_stat_color(stat):
    if stat == "Kills":
        return (255, 0, 0)  # Red
    elif stat == "Final Kills":
        return (255, 105, 180)  # Pink
    elif stat == "Wins":
        return (0, 255, 0)  # Green
    elif stat == "Losses":
        return (0, 0, 255)  # Blue
    elif stat == "Deaths":
        return (255, 255, 0)  # Yellow
    elif stat == "Highest Win Streak":
        return (128, 0, 128)  # Purple
    else:
        return (128, 0, 128)  # Default color

async def get_skin(username):
    response = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{username}")
    if response.status_code == 200:
        uuid = response.json()["id"]
        crafatar_url = f"https://crafatar.com/renders/body/{uuid}?overlay"
        
        # Upload ima


@bot.command()
async def commands(ctx):
    embed = discord.Embed(title="List of Commands", description="The list of commands available are:", color=0x00ff00)
    embed.add_field(name="#snipe list", value="Lists all usernames in the snipe list", inline=False)
    embed.add_field(name="#snipe set <username>", value="Adds a username to the snipe list", inline=False)
    embed.add_field(name="#user <username>", value="Shows Minecraft info for a specific username", inline=False)
    await ctx.send(embed=embed)
    embed.set_image(url="attachment://thumb.png")  # Add static image as thumbnail
    file = discord.File("thumb.png", filename="thumb.png")
    embed.set_footer(text="Thumbnail", icon_url="attachment://thumb.png")

@bot.command()
async def snipe(ctx, action=None, username=None):
    if action == 'list':
        if not snipe_list:
            await ctx.send("Snipe list is empty.")
        else:
            await ctx.send("Snipe list: {}".format(', '.join(snipe_list)))
    elif action == 'set' and username:
        snipe_list.append(username)
        await ctx.send("{} added to snipe list.".format(username))
    else:
        await ctx.send("Invalid syntax. Use #snipe list or #snipe set <username>.")

@bot.command()
async def user(ctx, username=None):
    if username:
        # Assuming you have a function to fetch Minecraft info and the player's skin
        minecraft_info = get_minecraft_info(username)
        if minecraft_info:
            skin_url = minecraft_info['skin_url']
            embed = discord.Embed(title="Minecraft Info for {}".format(username), color=0x0000ff)
            embed.set_thumbnail(url=skin_url)
            # Add other info about the player
            embed.add_field(name="UUID", value=minecraft_info['uuid'], inline=False)
            embed.add_field(name="Display Name", value=minecraft_info['display_name'], inline=False)
            embed.add_field(name="Level", value=minecraft_info['level'], inline=False)
            embed.add_field(name="Health", value=minecraft_info['health'], inline=False)
            embed.add_field(name="Location", value=minecraft_info['location'], inline=False)
            await ctx.send(embed=embed)
        else:
            await ctx.send("Minecraft info not found for {}".format(username))
    else:
        await ctx.send("Invalid syntax. Use #user <username>.")

@bot.command()
async def profile(ctx, user):
    profile_url = f"https://stats.pika-network.net/api/profile/{user}"
    response = requests.get(profile_url)
    
    if response.status_code == 200:
        profile_data = response.json()
        
        if profile_data:
            guild = profile_data.get('clan', {}).get('name')
            num_friends = len(profile_data.get('clan', {}).get('members', []))
            rank = profile_data.get('ranks', [])[0].get('displayName') if profile_data.get('ranks', []) else None
            email_verified = profile_data.get('email_verified')
            discord_boosting = profile_data.get('discord_boosting')
            skin_url = await get_skin(user)
            join_date = profile_data.get('clan', {}).get('creationTime')
            last_seen = profile_data.get('lastSeen')
            num_friends = len(profile_data.get('friends', []))
            
            # Convert ISO 8601 timestamps to a more human-readable format
            if join_date:
                join_date = datetime.fromisoformat(join_date).strftime('%Y-%m-%d')
            if last_seen:
                last_seen = datetime.fromtimestamp(last_seen / 1000).strftime('%Y-%m-%d %H:%M:%S')

            
            embed = discord.Embed(title=f"Profile for {user}", color=discord.Color.blue())
            
            if guild:
                embed.add_field(name="Guild", value=guild, inline=False)
            if num_friends:
                embed.add_field(name="Number of Friends", value=num_friends, inline=False)
            if rank:
                embed.add_field(name="Rank", value=rank, inline=False)
            if email_verified:
                embed.add_field(name="Email Verified", value=email_verified, inline=False)
            if discord_boosting:
                embed.add_field(name="Discord Boosting", value=discord_boosting, inline=False)
            if join_date:
                embed.add_field(name="Join Date", value=join_date, inline=False)
            if last_seen:
                embed.add_field(name="Last Seen", value=last_seen, inline=False)
            
            if skin_url:
                # Set the skin URL as the thumbnail and make it larger
                embed.set_thumbnail(url=skin_url + "?size=1000")  # Set the size to 512x512
                
            await ctx.send(embed=embed)
        else:
            await ctx.send("No data found for this user.")
    elif response.status_code == 400:
        await ctx.send("The player is not registered in the PikaNetwork database.")
    else:
        await ctx.send("There was a mistake in the link.")
    embed.set_image(url="attachment://thumb.png")  # Add static image as thumbnail
    file = discord.File("thumb.png", filename="thumb.png")
    embed.set_footer(text="Thumbnail", icon_url="attachment://thumb.png")

async def get_skin(username):
    response = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{username}")
    if response.status_code == 200:
        uuid = response.json()["id"]
        crafatar_url = f"https://crafatar.com/renders/body/{uuid}?overlay"
        
        # Upload image to Imgur
        client = ImgurClient(client_id, client_secret)
        image = client.upload_from_url(crafatar_url, anon=True)
        
        return image['link']
    else:
        return None


    
bot.run("MTIyNDk3MjY1OTE1NTE0NDc1Ng.GpZmW5.x4aX347wVzRV_VPN5qpPQ2uTfA3TRBAIzb5lM0")
