import os
import time
import discord
from discord.ext import commands
import json

from game import Game


class RoomsCog(commands.Cog):

    def __init__(self, bot, rooms_file_url="rooms.json"):
        self.bot = bot
        self.rooms_file_url : str = rooms_file_url

        if not os.path.exists(rooms_file_url):
            with open(rooms_file_url, "w") as f:
                json.dump({"rooms" : []}, f, indent=4)

        with open(rooms_file_url, "r") as f:
            self.rooms : list = json.load(f)["rooms"]

    
    def update_rooms_file(self):
        with open(self.rooms_file_url, "w") as f:
            json.dump({"rooms" : self.rooms}, f, indent=4)
    

    room = discord.app_commands.Group(name="room", description="Room commands")

    async def safe_defer(self, interaction: discord.Interaction):
        try:
            if not interaction.response.is_done():
                await interaction.response.defer()
        except discord.NotFound:
            # Interaction no longer valid
            pass
        except discord.InteractionResponded:
            # Already responded, ignore
            pass

    async def safe_followup_send(self, interaction: discord.Interaction, *args, **kwargs):
        try:
            await interaction.followup.send(*args, **kwargs)
        except discord.NotFound:
            # Interaction no longer valid
            pass
        except discord.HTTPException as e:
            # Other HTTP issues
            print(f"Failed to send followup message: {e}")

    @room.command(name="create", description="Create a room with some name")
    @discord.app_commands.describe(room_name="The name of the room to create")
    async def create_room(self, interaction: discord.Interaction, room_name : str):
        await self.safe_defer(interaction)

        if any(map(lambda x: x["name"] == room_name, self.rooms)):
            await self.safe_followup_send(interaction, f"Room with name `{room_name}` already exists!")
            return

        self.rooms.append({
            "name": room_name,
            "created_by": interaction.user.id,
            "channel1": interaction.channel_id
        })

        self.update_rooms_file()
        await self.safe_followup_send(interaction, f"Room with name `{room_name}` created!")

    @room.command(name="delete", description="Delete a room with some name")
    @discord.app_commands.describe(room_name="The name of the room to delete")
    async def delete_room(self, interaction: discord.Interaction, room_name : str):
        await self.safe_defer(interaction)

        deleted_room = None
        for room in self.rooms:
            if room["name"] == room_name:
                if room["created_by"] != interaction.user.id:
                    await self.safe_followup_send(interaction, f"Room with name `{room_name}` isn't yours!")
                    return
                deleted_room = room
                break

        if deleted_room is None:
            await self.safe_followup_send(interaction, f"Room with name `{room_name}` doesn't exist!")
            return
        
        self.rooms.remove(deleted_room)

        self.update_rooms_file()
        await self.safe_followup_send(interaction, f"Room with name `{room_name}` deleted!")

    @room.command(name="join", description="Join a room with some name")
    @discord.app_commands.describe(room_name="The name of the room to join to")
    async def join_room(self, interaction: discord.Interaction, room_name: str):
        await self.safe_defer(interaction)
        
        matches = list(map(lambda x: x["name"] == room_name, self.rooms))
        if any(matches):
            index = matches.index(True)

            if self.rooms[index]["created_by"] == interaction.user.id: 
                await self.safe_followup_send(interaction, f"You can't join to your own room!")
                return
            
            first_channel = self.bot.get_channel(self.rooms[index]["channel1"])

            if first_channel is None:
                await self.safe_followup_send(interaction, f"Couldn't join to room with name `{room_name}`")
                return
            

            await self.safe_followup_send(interaction, f"Joined to room with name `{room_name}` !")

            game =  Game(
                player1=self.rooms[index]["created_by"], 
                player2=interaction.user.id, 
                channel1 = first_channel, 
                channel2 = interaction.channel)
            
            self.rooms.pop(index)

            self.update_rooms_file()
            await game.start()
        else:
            await self.safe_followup_send(interaction, f"No room with name `{room_name}`")

    @room.command(name="list", description="List the current rooms")
    async def list_rooms(self, interaction: discord.Interaction):
        start = time.monotonic()
        try:
            await self.safe_defer(interaction)
            elapsed = (time.monotonic() - start) * 1000
            print(f"Defer succeeded in {elapsed:.0f}ms")
        except Exception as e:
            elapsed = (time.monotonic() - start) * 1000
            print(f"Defer failed in {elapsed:.0f}ms")
            print(f"❌ Defer failed — {e}")
            return

        if len(self.rooms) == 0:
            await self.safe_followup_send(interaction, 'There are no rooms!')
            return

        embed = discord.Embed(title = "The list of rooms", 
                              description="\n".join(
                                  map(lambda x: f"{x[0]}. {x[1]['name']}", 
                                      list(enumerate(self.rooms))))
                              , colour= discord.Color.blue())

        await self.safe_followup_send(interaction, embed=embed)


async def setup(bot):
    await bot.add_cog(RoomsCog(bot))
