import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import discord
from api.base_client import BaseApiClient

class DiscordApiClient(BaseApiClient):
    def __init__(self, bot_client: discord.Client):
        self.bot = bot_client

    async def send_message(self, channel_id: str, message: str):
        try:
            channel = self.bot.get_channel(int(channel_id))
            if channel:
                await channel.send(message)
                print(f"Sent message to Discord channel {channel_id}")
        except Exception as e:
            print(f"Failed to send Discord message: {e}")

    async def remove_user(self, guild_id: str, user_id: str):
        try:
            guild = self.bot.get_guild(int(guild_id))
            member = await guild.fetch_member(int(user_id))
            if guild and member:
                await member.kick(reason="Automated removal due to inactivity.")
                print(f"Kicked user {user_id} from Discord guild {guild_id}")
        except discord.NotFound:
            print(f"User {user_id} not found in guild {guild_id}.")
        except Exception as e:
            print(f"Failed to kick Discord user: {e}")
            

# ==============================================================================
# KHỐI TEST
# ==============================================================================
if __name__ == "__main__":
    print("\n--- RUNNING DISCORD API CLIENT IN TEST MODE ---")
    if DiscordApiClient.client:
        print("✅ Test run: Client initialized successfully.")
    else:
        print("❌ Test run: Client failed to initialize.")