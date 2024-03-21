from rich import print
from random import shuffle, randint

COLORS = ["red", "green", "blue", "yellow"]
WILDCARD_COLOR = "gray"
CARD_TYPES = [
    # Number cards
    {"name": "0", "wildcard": False, "quantity": 1, "value": 0},
    {"name": "1", "wildcard": False, "quantity": 2, "value": 1},
    {"name": "2", "wildcard": False, "quantity": 2, "value": 2},
    {"name": "3", "wildcard": False, "quantity": 2, "value": 3},
    {"name": "4", "wildcard": False, "quantity": 2, "value": 4},
    {"name": "5", "wildcard": False, "quantity": 2, "value": 5},
    {"name": "6", "wildcard": False, "quantity": 2, "value": 6},
    {"name": "7", "wildcard": False, "quantity": 2, "value": 7},
    {"name": "8", "wildcard": False, "quantity": 2, "value": 8},
    {"name": "9", "wildcard": False, "quantity": 2, "value": 9},
    # Colored specials
    {"name": "+2", "wildcard": False, "quantity": 2, "value": 20},
    {"name": "🔄", "wildcard": False, "quantity": 2, "value": 20},
    {"name": "🚫", "wildcard": False, "quantity": 2, "value": 20},
    # Black cards
    {"name": "+4", "wildcard": True, "quantity": 4, "value": 40},
    {"name": "🌈", "wildcard": True, "quantity": 4, "value": 40},
]
PLAYERS = [
    "You",  # The only human player
    "R2D2",
    "C3PO",
    "BB8",
    "Wall-E",
    # "Eva",
    # "Optimus Prime",
    # "Megatron",
    # "Bender",
    # "HAL 9000",
    # "GLaDOS",
]
INITIAL_CARDS = 7


class UnoCard:
    def __init__(self, name, color, value):
        self.name = name
        self.color = color
        self.value = value

    def can_play(self, top_card):
        return (
            self.name == top_card.name
            or self.color == top_card.color
            or self.color == WILDCARD_COLOR
        )

    def print_card(self):
        print(f"[white on {self.color}]{self.name:^3}")

    def __str__(self) -> str:
        return f"{self.name} {self.color}"


class UnoPlayer:
    def __init__(self, name):
        self.name = name
        self.hand = []

    def print_hand(self, top_card=None):
        for i, card in enumerate(self.hand):
            if card.can_play(top_card):
                print(f"[green bold]{i+1:>2}. ", end="")
            else:
                print(f" x. ", end="")
            card.print_card()

    def can_play(self, top_card):
        return any(card.can_play(top_card) for card in self.hand)

    def play_card(self, card_index, game, color_override=None):
        card = self.hand[card_index]
        if card.can_play(game.top_card):
            self.hand.pop(card_index)

            # Override color if needed
            if color_override:
                card.color = color_override

            game.play_card(card)

            return card

    def draw_card(self, card):
        self.hand.append(card)

    def has_won(self):
        return len(self.hand) == 0

    def auto_play(self, game):
        playable_cards = [card for card in self.hand if card.can_play(game.top_card)]
        if playable_cards:
            # TODO: be smarter, e.g. play the highest value but save wildcards for last...
            # Play the first eligible one...
            card = playable_cards[0]

            # If the card is a wildcard, choose a random color to play
            color = None
            if card.color == WILDCARD_COLOR:
                color = COLORS[randint(0, 3)]

            return self.play_card(self.hand.index(card), game, color)
        return None

    def score(self):
        return sum(card.value for card in self.hand)


class UnoGame:
    def __init__(self):
        self.deck = self.create_deck()
        self.players = [UnoPlayer(player) for player in PLAYERS]
        self.top_card = None
        self.current_player_idx = 0
        self.direction = 1
        self.winner = None
        self.penalty = None

    def create_deck(self):
        deck = []
        for card in CARD_TYPES:
            if card["wildcard"]:
                for _ in range(card["quantity"]):
                    deck.append(UnoCard(card["name"], WILDCARD_COLOR, card["value"]))
            else:
                for color in COLORS:
                    for _ in range(card["quantity"]):
                        deck.append(UnoCard(card["name"], color, card["value"]))

        shuffle(deck)
        return deck

    def print_top_card(self):
        self.top_card.print_card()

    def play_card(self, card):
        # NOTE: we're not checking card legality here, because its color might have been overridden...
        self.top_card = card

        # Change game direction if needed
        if card.name == "🔄":
            self.direction *= -1

        # Set the penalty for next player if any
        match card.name:
            case "+4":
                self.penalty = 4
            case "+2":
                self.penalty = 2
            case "🚫":
                self.penalty = 0
        # The reverse acts as a skip if there's only 2 players
        if card.name == "🔄" and len(self.players) == 2:
            self.penalty = 0

        return card

    def can_play_card(self, card):
        return card.can_play(self.top_card)

    def deal_card_to_player(self, player_idx):
        card = self.draw_card()
        if card:
            self.players[player_idx].draw_card(card)
            return True
        return False

    def deal_card(self):
        return self.deal_card_to_player(self.current_player_idx)

    def has_winner(self):
        for player in self.players:
            if player.has_won():
                self.winner = player
                return True
        return False

    def next_player(self):
        self.current_player_idx = (self.current_player_idx + self.direction) % len(
            self.players
        )

    def play_new_card(self):
        card = self.draw_card()
        if card:
            self.play_card(card)
            return True
        return False

    def draw_card(self):
        if self.deck and len(self.deck):
            return self.deck.pop()
        return None

    def current_player(self):
        return self.players[self.current_player_idx]

    def apply_penalty(self):
        if self.penalty is not None:
            for _ in range(self.penalty):
                self.deal_card()
            self.penalty = None
            self.next_player()
            return True
        return False


def prompt_color():
    print("[bold green]Choose a color to play:")
    for i, color in enumerate(COLORS):
        print(f"[white on {color}]{i+1:^3}")
    while True:
        try:
            return COLORS[int(input()) - 1]
        except Exception:
            print("[red]Invalid input, try again")


def prompt_card(player, game):
    while True:
        try:
            card_index = int(input()) - 1
            card = player.hand[card_index]

            # If the card is a wildcard, prompt for color to play
            if card.can_play(game.top_card):
                color = None
                if card.color == WILDCARD_COLOR:
                    color = prompt_color()

                return card_index, color
            else:
                print("[red]You can't play that card!")
        except Exception:
            print("[red]Invalid input, try again")


game = UnoGame()

# Deal cards
for _ in range(INITIAL_CARDS):
    for player in range(len(game.players)):
        game.deal_card_to_player(player)

# Place top card
game.play_new_card()

while not game.has_winner():
    player = game.current_player()
    print(f"[bold blue]{player.name}'s turn")

    # print(current_game)

    print("Top card: ", end="")
    game.print_top_card()

    # Apply penalties if needed
    if game.penalty is not None:
        match game.penalty:
            case 4:
                print("[red]Penalty: 4 cards 🥵")
            case 2:
                print("[red]Penalty: 2 cards 😓")
            case 0:
                print("[red]Penalty: Skipping 😔")
        game.apply_penalty()
        continue

    # Draw if you cannot play anything
    if not player.can_play(game.top_card):
        print("[yellow]Can't play, drawing")
        game.deal_card()

    # Skip if you still cannot play anything
    if not player.can_play(game.top_card):
        print("[yellow]Still can't play, skipping")
        game.next_player()
        continue

    played_card = None
    if game.current_player_idx == 0:
        # It's the only human player, show hand and prompt for play
        print("Your hand:")
        player.print_hand(game.top_card)

        print("[green bold]Which card do you want to play?")
        idx, color_override = prompt_card(player, game)
        played_card = player.play_card(idx, game, color_override)
    else:
        # It's an AI player, play automatically
        played_card = player.auto_play(game)

    if played_card:
        print(f"{player.name} played: ", end="")
        played_card.print_card()

    # Check if anyone won
    if game.has_winner():
        print(f"[bold green]{game.winner.name} wins! 🎉")
        break

    game.next_player()


# Show scores
print()
print("[blue]Final scores:")
for player in game.players:
    print(f"{player.name}: {player.score()} {'🏆' if player.has_won() else ''}")
