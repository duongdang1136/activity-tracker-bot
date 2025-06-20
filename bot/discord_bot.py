import discord
from services import activity_service
from config import settings
from api.discord_api import DiscordApiClient

# --- Khởi tạo ---
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.reactions = True
intents.guilds = True
intents.members = True # Cần để fetch_member
client = discord.Client(intents=intents)

# Tạo API client và truyền client của bot vào
# Biến này sẽ được import bởi ManagementService
discord_api_client = DiscordApiClient(client)

# --- Sự kiện ---
@client.event
async def on_ready():
    print(f'🤖 Discord Bot {client.user} is online and ready!')

@client.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    activity_service.track_message(
        platform_name="Discord",
        user_id=str(message.author.id),
        user_name=message.author.display_name,
        group_id=str(message.guild.id),
        group_name=message.guild.name
    )

@client.event
async def on_reaction_add(reaction, user):
    if user.bot or not reaction.message.guild:
        return

    activity_service.track_reaction(
        platform_name="Discord",
        user_id=str(user.id),
        user_name=user.display_name,
        group_id=str(reaction.message.guild.id),
        group_name=reaction.message.guild.name
    )

# Hàm để chạy bot, được gọi từ main.py
async def start_discord_bot():
    try:
        await client.start(settings.discord.token)
    except Exception as e:
        print(f"❌ Failed to run Discord bot: {e}")
    finally:
        await client.close()