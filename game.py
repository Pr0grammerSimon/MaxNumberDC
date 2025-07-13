import random
import logging
import discord


NUMBER_CARDS = [i for i in range(1, 10)]
OPERATION_CARDS = ['/', '+', '*', '-']
NR_OPERATION_CARDS = 7
NR_NUMBER_CARDS = 10


class Game:

    def __init__(self, player1 : int, player2 : int, channel1 : discord.TextChannel, channel2 : discord.TextChannel):
        self.player1_id : int = player1
        self.player2_id : int = player2
        self.player1 : discord.Member | None = None
        self.player2 : discord.Member | None = None
        self.cards = {
            player1 : [1],
            player2 : [1]
        }

        self.current_turn = random.choice([player1, player2])
        self.available = [*random.choices(NUMBER_CARDS, k = NR_NUMBER_CARDS), *random.choices(OPERATION_CARDS, k = NR_OPERATION_CARDS)]
        random.shuffle(self.available) 

        self.messages = []
        self.channel1 = channel1
        self.channel2 = channel2

        self.player_choice = None
        self.card_choice = None
        self.pos_choice = None

        self.choice_texts = ["Pick a player", "Pick a card", "Pick a position to give a card"]
        self.choice_nr = 0

    async def setup_players(self) -> bool:
        try:
            guild1 = self.channel1.guild
            guild2 = self.channel2.guild

            self.player1 = guild1.get_member(self.player1_id) or await guild1.fetch_member(self.player1_id)
            self.player2 = guild2.get_member(self.player2_id) or await guild2.fetch_member(self.player2_id)

            if not self.player1 or not self.player2:
                logging.warning(f"One or both players not found: {self.player1}, {self.player2}")
                return False
            return True
        except discord.NotFound as e:
            logging.error(f"Player not found: {e}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error in setup_players: {e}", exc_info=True)
            return False

    
    async def start(self):
        try:
            if not await self.setup_players():
                if self.channel1.id == self.channel2.id:
                    await self.channel1.send("Couldn't find the player")
                else:
                    await self.channel2.send("Couldn't find the player")
                    await self.channel1.send("Couldn't find the player")
                return

            if self.channel1.id == self.channel2.id:
                cards_embed = await self.cards_embed()
                view = PlayerChoiceView(self)
                self.messages = [await self.channel1.send(embed=cards_embed, view=view)]
            else:
                cards_embed1 = await self.cards_embed()

                view1 = PlayerChoiceView(self)
                view2 = PlayerChoiceView(self)

                self.messages = [await self.channel1.send(embed=cards_embed1, view=view1), 
                                 await self.channel2.send(embed=cards_embed1, view=view2)]
        except Exception as e:
            logging.error(f"Error in start: {e}", exc_info=True)


    async def cards_embed(self):
        try:
            player1 = self.player1
            player2 = self.player2

            embed = discord.Embed(title=f"MAX NUMBER",
                                  description=f"<@{player1.id}> VS <@{player2.id}>",
                                  color=discord.Color.blue())

            embed.add_field(name=f"Player {player1.display_name} cards", 
                            value = f"```{''.join(list(map(str, self.cards[player1.id])))}```",
                            inline=False)
            
            embed.add_field(name=f"Available cards", 
                            value = f"```{', '.join(list(map(str, self.available)))}```", 
                            inline=False)
            
            embed.add_field(name=f"Player {player2.display_name} cards", 
                            value = f"```{''.join(list(map(str, self.cards[player2.id])))}```", 
                            inline=False)
            
            embed.add_field(name="What to do?", value=f"{self.choice_texts[self.choice_nr]}", inline=False)

            embed.set_footer(text=f"{player1.display_name if self.current_turn == self.player1_id else player2.display_name} turn!")

            return embed
        except Exception as e:
            logging.error(f"Error creating embed: {e}", exc_info=True)
            # Return a minimal embed so the bot won't crash completely
            return discord.Embed(title="Error", description="Failed to create game embed.")


    async def can_press(self, interaction : discord.Interaction):
        try:
            await interaction.response.defer()
            user_id = interaction.user.id

            if user_id != self.player1_id and user_id != self.player2_id:
                await interaction.followup.send("This is not your game!", ephemeral=True)
                return False
            
            if user_id != self.current_turn:
                await interaction.followup.send("It is not your turn!", ephemeral=True)
                return False

            return True
        except Exception as e:
            logging.error(f"Error in can_press: {e}", exc_info=True)
            return False
    
    async def valid_move(self):
        try:
            card = self.card_choice
            pos = self.pos_choice
            player = self.player_choice

            new_expr = "".join([str(element) for element in self.cards[player]])
            new_expr = new_expr[:pos] + str(card) + new_expr[pos:]

            for idx in range(len(new_expr) - 1):
                if new_expr[idx] in OPERATION_CARDS and new_expr[idx + 1] in OPERATION_CARDS:
                    return False

            if new_expr[0] == "/" or new_expr[0] == "*":
                return False
            
            if new_expr[-1] in OPERATION_CARDS:
                return False

            return True
        except Exception as e:
            logging.error(f"Error validating move: {e}", exc_info=True)
            return False
    

    async def end_embed(self):
        try:
            player1 = self.player1_id
            player2 = self.player2_id
            
            score1 = eval("".join([str(element) for element in self.cards[player1]]))
            score2 = eval("".join([str(element) for element in self.cards[player2]]))

            score1_rounded = f"{score1:.3f}"
            score2_rounded = f"{score2:.3f}"

            result = "DRAW!"

            if score1 > score2:
                result = f"{self.player1.display_name} WON!"
            elif score2 > score1:
                result = f"{self.player2.display_name} WON!"

            embed = discord.Embed(title=f"MAX NUMBER",
                                description=result,
                                color=discord.Color.blue())
            
            embed.add_field(name = f"{self.player1.display_name} SCORE", value = score1_rounded, inline = False)
            embed.add_field(name = f"{self.player2.display_name} SCORE", value = score2_rounded, inline = False)
            embed.add_field(name = f"{self.player1.display_name} Expression", 
                            value = f"```{''.join(list(map(str, self.cards[player1])))}```", 
                            inline = False)
            embed.add_field(name = f"{self.player2.display_name} Expression", 
                            value = f"```{''.join(list(map(str, self.cards[player2])))}```", 
                            inline = False)
            
            return embed
        except Exception as e:
            logging.error(f"Error creating end embed: {e}", exc_info=True)
            return discord.Embed(title="Error", description="Failed to create end game embed.")


class BackButton(discord.ui.Button):
    
    def __init__(self, game : Game):
        super().__init__(
            label = "Back"
        )

        self.game = game
    
    async def callback(self, interaction : discord.Interaction):
        try:
            await interaction.response.defer()

            if not await self.game.can_press(interaction): return
            if self.game.choice_nr == 0: return

            self.game.choice_nr -= 1
            if self.game.choice_nr == 0:
                await interaction.message.edit(view = PlayerChoiceView(self.game), embed = await self.game.cards_embed())
            elif self.game.choice_nr == 1:
                await interaction.message.edit(view = CardChoiceView(self.game), embed = await self.game.cards_embed())

            await interaction.followup.send("Returned to last choice", ephemeral=True)
        except Exception as e:
            logging.error(f"Error in BackButton callback: {e}", exc_info=True)


class PlayerChoiceView(discord.ui.View):

    def __init__(self, game : Game):
        super().__init__()
        self.game : Game = game
        game.choice_nr = 0
        self.timeout = None

        self.add_item(PlayerChoiceButton(game.player1, game))
        self.add_item(PlayerChoiceButton(game.player2, game))


class PlayerChoiceButton(discord.ui.Button):

    def __init__(self, player : discord.Member, game : Game):

        super().__init__(
            label=f"{player.display_name}",
            style=discord.ButtonStyle.primary,
        )

        self.player = player
        self.game = game
    
    async def callback(self, interaction : discord.Interaction):
        try:
            await interaction.response.defer()

            if not await self.game.can_press(interaction): return

            self.game.player_choice = self.player.id
        
            await interaction.message.edit(view = CardChoiceView(self.game), embed = await self.game.cards_embed())
        except Exception as e:
            logging.error(f"Error in PlayerChoiceButton callback: {e}", exc_info=True)


class CardChoiceView(discord.ui.View):
    
    def __init__(self, game : Game):
        super().__init__()
        self.game = game
        game.choice_nr = 1
        self.timeout = None
        
        for card in game.available:
            self.add_item(CardChoiceButton(card, game))

        self.add_item(BackButton(game))


class CardChoiceButton(discord.ui.Button):

    def __init__(self, card, game):
        super().__init__(
            label = str(card),
            style = discord.ButtonStyle.secondary,
        )
        self.card = card
        self.game = game
    
    async def callback(self, interaction : discord.Interaction):
        try:
            await interaction.response.defer()
            if not await self.game.can_press(interaction): return

            self.game.card_choice = self.card
            await interaction.message.edit(view = PositionChoiceView(self.game), embed = await self.game.cards_embed())
        except Exception as e:
            logging.error(f"Error in CardChoiceButton callback: {e}", exc_info=True)


class PositionChoiceView(discord.ui.View):

    def __init__(self, game : Game):
        super().__init__()
        self.game = game
        game.choice_nr = 2
        self.timeout = None

        # number of positions = length of chosen player's cards + 1
        for i in range(len(game.cards[game.player_choice]) + 1):
            self.add_item(PositionChoiceButton(i, game))
        
        self.add_item(BackButton(game))


class PositionChoiceButton(discord.ui.Button):

    def __init__(self, pos : int, game : Game):
        super().__init__(
            label = str(pos),
            style = discord.ButtonStyle.success,
        )
        self.pos = pos
        self.game = game
    
    async def callback(self, interaction : discord.Interaction):
        try:
            await interaction.response.defer()
            if not await self.game.can_press(interaction): return

            self.game.pos_choice = self.pos

            if not await self.game.valid_move():
                await interaction.followup.send("Invalid move! Two operations in a row or invalid position.", ephemeral=True)
                return

            self.game.cards[self.game.player_choice].insert(self.pos, self.game.card_choice)
            self.game.available.remove(self.game.card_choice)
            
            # Reset choices
            self.game.player_choice = None
            self.game.card_choice = None
            self.game.pos_choice = None

            # Change turn
            if self.game.current_turn == self.game.player1_id:
                self.game.current_turn = self.game.player2_id
            else:
                self.game.current_turn = self.game.player1_id

            # Reset to first choice
            self.game.choice_nr = 0

            if len(self.game.available) == 0:
                await interaction.message.edit(view=None, embed=await self.game.end_embed())
            else:
                await interaction.message.edit(view=PlayerChoiceView(self.game), embed=await self.game.cards_embed())
        except Exception as e:
            logging.error(f"Error in PositionChoiceButton callback: {e}", exc_info=True)
