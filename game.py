import random

import discord


NUMBER_CARDS = [i for i in range(9)]
OPERATION_CARDS = ['/', '+', '*', '-']
NR_OPERATION_CARDS = 7
NR_NUMBER_CARDS = 10


class Game:

    def __init__(self, player_1 : discord.Member.id, player_2 : discord.Member.id, channel : discord.TextChannel):
        self.player_1 = player_1
        self.player_2 = player_2
        self.cards = {
            player_1 : ['1'],
            player_2 : ['2']
        }
        self.current_turn = player_1
        self.available = [*random.choices(NUMBER_CARDS, k = NR_NUMBER_CARDS), *random.choices(OPERATION_CARDS, NR_OPERATION_CARDS)]
        random.shuffle(self.available)

        self.message = None
        self.channel = channel
    
    async def start(self):
        cards_embed = self.cards_embed()

        self.message = await self.channel.send(embed=cards_embed)
    
    def cards_embed(self):

        embed = discord.Embed(title="MaxNumber")
        embed.add_field(name=f"Player {self.player_1} cards", value = self.cards[self.player_1])
        embed.add_field(name=f"Available cards", value = self.available)
        embed.add_field(name=f"Player {self.player_2} cards", value = self.cards[self.player_2])
        embed.set_footer(text=f"{self.current_turn} turn!")

        return embed