import logging
import os
import json
import discord
from discord.ext import commands
from game import Game

log = logging.getLogger(__name__)

class SafeInteraction:
    @staticmethod
    async def defer(interaction: discord.Interaction):
        try:
            if not interaction.response.is_done():
                await interaction.response.defer()
        except (discord.errors.InteractionResponded, discord.errors.NotFound):
            # ignorujemy, jeśli już było zrobione lub interakcja wygasła
            pass

    @staticmethod
    async def respond(interaction: discord.Interaction, **kwargs):
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(**kwargs)
            else:
                await interaction.followup.send(**kwargs)
        except (discord.errors.InteractionResponded, discord.errors.NotFound):
            pass
        except Exception as e:
            log.error(f"SafeInteraction.respond failed: {e}", exc_info=True)


class RoomsCog(commands.Cog):
    def __init__(self, bot, rooms_file="rooms.json"):
        self.bot = bot
        self.file = rooms_file

        if not os.path.exists(self.file):
            with open(self.file, "w") as f:
                json.dump({"rooms": []}, f, indent=4)

        with open(self.file, "r") as f:
            self.rooms = json.load(f)["rooms"]

    def _save(self):
        with open(self.file, "w") as f:
            json.dump({"rooms": self.rooms}, f, indent=4)

    room = discord.app_commands.Group(name="room", description="Room commands")

    @room.command(name="create", description="Create a room")
    @discord.app_commands.describe(room_name="Name of the room")
    async def create_room(self, interaction: discord.Interaction, room_name: str):
        await SafeInteraction.defer(interaction)

        if any(r["name"] == room_name for r in self.rooms):
            await SafeInteraction.respond(interaction, content=f"Room `{room_name}` already exists!")
            return

        self.rooms.append({
            "name": room_name,
            "created_by": interaction.user.id,
            "channel1": interaction.channel_id
        })
        self._save()
        await SafeInteraction.respond(interaction, content=f"Room `{room_name}` created!")

    @room.command(name="delete", description="Delete your room")
    @discord.app_commands.describe(room_name="Name of the room to delete")
    async def delete_room(self, interaction: discord.Interaction, room_name: str):
        await SafeInteraction.defer(interaction)

        for r in self.rooms:
            if r["name"] == room_name:
                if r["created_by"] != interaction.user.id:
                    await SafeInteraction.respond(interaction, content="You don't own that room!")
                    return
                self.rooms.remove(r)
                self._save()
                await SafeInteraction.respond(interaction, content=f"Room `{room_name}` deleted!")
                return

        await SafeInteraction.respond(interaction, content=f"No room named `{room_name}`.")

    @room.command(name="join", description="Join a room")
    @discord.app_commands.describe(room_name="Name of the room to join")
    async def join_room(self, interaction: discord.Interaction, room_name: str):
        await SafeInteraction.defer(interaction)

        for idx, r in enumerate(self.rooms):
            if r["name"] == room_name:
                if r["created_by"] == interaction.user.id:
                    await SafeInteraction.respond(interaction, content="You cannot join your own room!")
                    return

                channel1 = self.bot.get_channel(r["channel1"])
                if channel1 is None:
                    await SafeInteraction.respond(interaction, content="Original channel not found.")
                    return

                await SafeInteraction.respond(interaction, content=f"Joined `{room_name}`!")
                game = Game(
                    player1_id=r["created_by"],
                    player2_id=interaction.user.id,
                    channel1=channel1,
                    channel2=interaction.channel
                )
                # usuń pokój i zapisz
                self.rooms.pop(idx)
                self._save()
                await game.start()
                return

        await SafeInteraction.respond(interaction, content=f"No room named `{room_name}`.")

    @room.command(name="list", description="List all rooms")
    async def list_rooms(self, interaction: discord.Interaction):
        await SafeInteraction.defer(interaction)

        if not self.rooms:
            await SafeInteraction.respond(interaction, content="There are no rooms.")
            return

        desc = "\n".join(f"{i+1}. {r['name']}" for i, r in enumerate(self.rooms))
        embed = discord.Embed(title="Active Rooms", description=desc, color=discord.Color.blue())
        await SafeInteraction.respond(interaction, embed=embed)


async def setup(bot):
    await bot.add_cog(RoomsCog(bot))
