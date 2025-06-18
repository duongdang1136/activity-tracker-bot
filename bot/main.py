import discord
from services.activity_service import ActivityService
from config.config import settings

# --- Khởi tạo ---
activity_service = ActivityService()

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.reactions = True
intents.guilds = True
client = discord.Client(intents=intents)

# --- Sự kiện ---
@client.event
async def on_ready():
    print(f'🤖 Bot {client.user} is online and ready!')

@client.event
async def on_message(message):
    if message.author == client.user or not message.guild:
        return

    activity_service.track_message(
        platform_name="Discord",
        user_id=str(message.author.id),
        user_name=message.author.display_name,
        group_id=str(message.guild.id),
        group_name=message.guild.name
    )

def run_bot():
    try:
        client.run(settings.bot.discord_token)
    except Exception as e:
        print(f"❌ Failed to run bot: {e}")

if __name__ == "__main__":
    run_bot()
