import discord
from discord.ext import commands
import json


class Rooms():

    def __init__(self) :
        self.rooms = {}
    
    #Return True if room was added, otherwise False
    def add(self, room_id, host_id) -> bool:
        if room_id in self.rooms:
            return False
        else:
            self.rooms[room_id] = host_id
            return True

    #Return True if room was deleted, otherwise False
    def delete(self, room_id, user_id) -> bool:
        if room_id in self.rooms:
            if self.rooms[room_id] == user_id:
                self.rooms.pop(room_id)
                return True
            else:
                return False
        else:
            return False
        
    #Return list of 2 players if the user joined the room, otherwise None
    def join(self, room_id, user_id) -> list[str] | None:
        if room_id in self.rooms:
            if user_id != self.rooms[room_id]:
                host = self.rooms[room_id]
                self.rooms.pop(room_id)
                return [host, user_id]
            else:
                return None
        else:
            return None
        


class RoomsCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.rooms = Rooms()
    
    @discord.app_commands.command(name="test", description="test")
    async def test(self, interaction: discord.Interaction):
        await interaction.response.send_message("OHH!")


    room = discord.app_commands.Group(name="room", description="Room commands")

    @room.command(name="create", description="Create a room with some name")
    async def create_room(self, interaction: discord.Interaction, room_name : str):
        with open("rooms.json", "r") as f:
            obj = json.load(f)
        rooms = obj["rooms"]

        if any(map(lambda x: x["name"] == room_name, rooms)):
            await interaction.response.send_message(f"Room with name {room_name} already exists!")

        rooms.append({
            "name": room_name,
            "created_by": interaction.user.id
        })
        
        with open("rooms.json", "w") as f:
            json.dump(obj, f)

        await interaction.response.send_message(f"Room with name {room_name} created!")



    @room.command(name="delete", description="Delete a room with some name")
    async def create_room(self, interaction: discord.Interaction, room_name : str):
        with open("rooms.json", "r") as f:
            obj = json.load(f)
        rooms: list = obj["rooms"]

        deleted_room = None
        for room in rooms:
            if room["name"] == room_name:
                if room["created_by"] != interaction.user.id:
                    await interaction.response.send_message(f"Romm with name {room_name} isn't yours!")
                    return
                deleted_room = room
                break

        if deleted_room is None:
            await interaction.response.send_message(f"Room with name {room_name} doesn't exist!")
            return
        
        rooms.remove(deleted_room)

        with open("rooms.json", "w") as f:
            json.dump(obj, f)
        await interaction.response.send_message(f"Room with name {room_name} deleted!")


    @room.command(name="join", description="Join a room with some name")
    async def create_room(self, interaction: discord.Interaction, room_name : str):
        await interaction.response.send_message(f"Joined to room with name {room_name} !")

    @room.command(name="list", description="List the current rooms")
    async def create_room(self, interaction: discord.Interaction):
        with open("rooms.json", "r") as f:
            obj = json.load(f)
        rooms: list = obj["rooms"]

        embed = discord.Embed(title = "The list of rooms", description="\n".join(map(lambda x: x["name"], rooms)))

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(RoomsCog(bot))