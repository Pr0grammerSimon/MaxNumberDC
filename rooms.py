import discord
from discord.ext import commands


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
    def join(self, room_id, user_id) -> list[int] | None:
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
        await interaction.response.send_message(f"Room with name {room_name} created!")

    @room.command(name="delete", description="Delete a room with some name")
    async def create_room(self, interaction: discord.Interaction, room_name : str):
        await interaction.response.send_message(f"Room with name {room_name} deleted!")

    @room.command(name="join", description="Join a room with some name")
    async def create_room(self, interaction: discord.Interaction, room_name : str):
        await interaction.response.send_message(f"Joined to room with name {room_name} !")


async def setup(bot):
    await bot.add_cog(RoomsCog(bot))