import random
import logging
import discord

NUMBER_CARDS = list(range(1, 10))
OPERATION_CARDS = ['/', '+', '*', '-']
NR_OPERATION_CARDS = 7
NR_NUMBER_CARDS = 10

log = logging.getLogger("game")


class Game:

    def __init__(self, player1_id: int, player2_id: int,
                 channel1: discord.TextChannel, channel2: discord.TextChannel):
        self.player1_id = player1_id
        self.player2_id = player2_id
        self.player1 = None  # discord.Member
        self.player2 = None
        self.cards = {
            player1_id: [1],
            player2_id: [1]
        }
        self.current_turn = random.choice([player1_id, player2_id])
        self.available = (
            random.choices(NUMBER_CARDS, k=NR_NUMBER_CARDS) +
            random.choices(OPERATION_CARDS, k=NR_OPERATION_CARDS)
        )
        random.shuffle(self.available)

        self.channel1 = channel1
        self.channel2 = channel2
        self.messages = []

        # stan wyborów
        self.player_choice = None
        self.card_choice = None
        self.pos_choice = None
        self.choice_nr = 0
        self.choice_texts = ["Pick a player", "Pick a card", "Pick a position"]

    async def setup_players(self) -> bool:
        try:
            g1 = self.channel1.guild
            g2 = self.channel2.guild
            self.player1 = g1.get_member(self.player1_id) or await g1.fetch_member(self.player1_id)
            self.player2 = g2.get_member(self.player2_id) or await g2.fetch_member(self.player2_id)
            if not (self.player1 and self.player2):
                log.warning("Nie znaleziono któregoś z graczy")
                return False
            return True
        except Exception as e:
            log.error("Błąd w setup_players", exc_info=True)
            return False

    async def start(self):
        if not await self.setup_players():
            msg = "Couldn't find the player"
            await self.channel1.send(msg)
            if self.channel2 != self.channel1:
                await self.channel2.send(msg)
            return

        embed = await self.cards_embed()
        if self.channel1 == self.channel2:
            view = PlayerChoiceView(self)
            self.messages = [await self.channel1.send(embed=embed, view=view)]
        else:
            view1 = PlayerChoiceView(self)
            view2 = PlayerChoiceView(self)
            self.messages = [
                await self.channel1.send(embed=embed, view=view1),
                await self.channel2.send(embed=embed, view=view2)
            ]

    async def cards_embed(self) -> discord.Embed:
        e = discord.Embed(
            title="MAX NUMBER",
            description=f"<@{self.player1.id}> VS <@{self.player2.id}>",
            color=discord.Color.blue()
        )
        e.add_field(
            name=f"{self.player1.display_name} cards",
            value=f"```{''.join(map(str, self.cards[self.player1_id]))}```",
            inline=False
        )
        e.add_field(
            name="Available",
            value=f"```{', '.join(map(str, self.available))}```",
            inline=False
        )
        e.add_field(
            name=f"{self.player2.display_name} cards",
            value=f"```{''.join(map(str, self.cards[self.player2_id]))}```",
            inline=False
        )
        e.add_field(
            name="What to do?",
            value=self.choice_texts[self.choice_nr],
            inline=False
        )
        turn_name = self.player1.display_name if self.current_turn == self.player1_id else self.player2.display_name
        e.set_footer(text=f"{turn_name}'s turn")
        return e

    def can_press(self, user_id: int) -> bool:
        """Tylko sprawdza, czy user_id może wykonać ruch."""
        if user_id not in (self.player1_id, self.player2_id):
            return False
        if user_id != self.current_turn:
            return False
        return True

    async def valid_move(self) -> bool:
        try:
            expr = ''.join(map(str, self.cards[self.player_choice]))
            expr = expr[:self.pos_choice] + str(self.card_choice) + expr[self.pos_choice:]
            # dwa operatory obok
            for a, b in zip(expr, expr[1:]):
                if a in OPERATION_CARDS and b in OPERATION_CARDS:
                    return False
            # nie zaczyna się od */ i nie kończy operatorem
            if expr[0] in ('*', '/') or expr[-1] in OPERATION_CARDS:
                return False
            return True
        except Exception:
            return False

    async def end_embed(self) -> discord.Embed:
        s1 = eval(''.join(map(str, self.cards[self.player1_id])))
        s2 = eval(''.join(map(str, self.cards[self.player2_id])))
        if s1 > s2:
            desc = f"{self.player1.display_name} WON!"
        elif s2 > s1:
            desc = f"{self.player2.display_name} WON!"
        else:
            desc = "DRAW!"
        e = discord.Embed(title="MAX NUMBER", description=desc, color=discord.Color.blue())
        e.add_field(name=f"{self.player1.display_name} SCORE", value=f"{s1:.3f}")
        e.add_field(name=f"{self.player2.display_name} SCORE", value=f"{s2:.3f}")
        e.add_field(
            name=f"{self.player1.display_name} EXPR",
            value=f"```{''.join(map(str, self.cards[self.player1_id]))}```",
            inline=False
        )
        e.add_field(
            name=f"{self.player2.display_name} EXPR",
            value=f"```{''.join(map(str, self.cards[self.player2_id]))}```",
            inline=False
        )
        return e


# ---- UI ----

class SafeInteraction:
    """Pomocnicze metody na interakcję."""
    @staticmethod
    async def defer(interaction: discord.Interaction):
        try:
            await interaction.response.defer()
        except discord.errors.InteractionResponded:
            pass
        except discord.errors.NotFound:
            pass

    @staticmethod
    async def respond(interaction: discord.Interaction, **kwargs):
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(**kwargs)
            else:
                await interaction.followup.send(**kwargs)
        except Exception as e:
            log.error(f"Failed to respond: {e}", exc_info=True)


class BackButton(discord.ui.Button):
    def __init__(self, game: Game):
        super().__init__(label="Back")
        self.game = game

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user.id
        if not self.game.can_press(user):
            await SafeInteraction.respond(interaction, content="Nie Twoja kolej!", ephemeral=True)
            return
        await SafeInteraction.defer(interaction)

        # cofnij stan
        if self.game.choice_nr > 0:
            self.game.choice_nr -= 1

        # edytuj widok
        view = PlayerChoiceView(self.game) if self.game.choice_nr == 0 else CardChoiceView(self.game)
        embed = await self.game.cards_embed()
        await interaction.message.edit(embed=embed, view=view)
        await SafeInteraction.respond(interaction, content="Cofnięto", ephemeral=True)


class PlayerChoiceView(discord.ui.View):
    def __init__(self, game: Game):
        super().__init__(timeout=None)
        self.game = game
        game.choice_nr = 0
        self.add_item(PlayerChoiceButton(game.player1, game))
        self.add_item(PlayerChoiceButton(game.player2, game))


class PlayerChoiceButton(discord.ui.Button):
    def __init__(self, player: discord.Member, game: Game):
        super().__init__(label=player.display_name, style=discord.ButtonStyle.primary)
        self.player = player
        self.game = game

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user.id
        if not self.game.can_press(user):
            await SafeInteraction.respond(interaction, content="Nie Twoja kolej!", ephemeral=True)
            return

        await SafeInteraction.defer(interaction)
        self.game.player_choice = self.player.id
        self.game.choice_nr = 1
        embed = await self.game.cards_embed()
        await interaction.message.edit(embed=embed, view=CardChoiceView(self.game))


class CardChoiceView(discord.ui.View):
    def __init__(self, game: Game):
        super().__init__(timeout=None)
        self.game = game
        game.choice_nr = 1
        for c in self.game.available:
            self.add_item(CardChoiceButton(c, game))
        self.add_item(BackButton(game))


class CardChoiceButton(discord.ui.Button):
    def __init__(self, card, game: Game):
        super().__init__(label=str(card), style=discord.ButtonStyle.secondary)
        self.card = card
        self.game = game

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user.id
        if not self.game.can_press(user):
            await SafeInteraction.respond(interaction, content="Nie Twoja kolej!", ephemeral=True)
            return

        await SafeInteraction.defer(interaction)
        self.game.card_choice = self.card
        self.game.choice_nr = 2
        embed = await self.game.cards_embed()
        await interaction.message.edit(embed=embed, view=PositionChoiceView(self.game))


class PositionChoiceView(discord.ui.View):
    def __init__(self, game: Game):
        super().__init__(timeout=None)
        self.game = game
        game.choice_nr = 2
        for i in range(len(game.cards[game.player_choice]) + 1):
            self.add_item(PositionChoiceButton(i, game))
        self.add_item(BackButton(game))


class PositionChoiceButton(discord.ui.Button):
    def __init__(self, pos: int, game: Game):
        super().__init__(label=str(pos), style=discord.ButtonStyle.success)
        self.pos = pos
        self.game = game

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user.id
        if not self.game.can_press(user):
            await SafeInteraction.respond(interaction, content="Nie Twoja kolej!", ephemeral=True)
            return

        await SafeInteraction.defer(interaction)
        self.game.pos_choice = self.pos
        if not await self.game.valid_move():
            await SafeInteraction.respond(interaction, content="Invalid move!", ephemeral=True)
            return

        # wykonaj ruch
        self.game.cards[user].insert(self.pos, self.game.card_choice)
        self.game.available.remove(self.game.card_choice)
        # reset
        self.game.card_choice = None
        self.game.player_choice = None
        self.game.pos_choice = None
        # zmiana kolejki
        self.game.current_turn = (
            self.game.player2_id
            if user == self.game.player1_id
            else self.game.player1_id
        )
        # zaktualizuj widok / embed
        if not self.game.available:
            embed = await self.game.end_embed()
            await interaction.message.edit(embed=embed, view=None)
        else:
            embed = await self.game.cards_embed()
            await interaction.message.edit(embed=embed, view=PlayerChoiceView(self.game))
