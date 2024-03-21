import sys

from random import randint, shuffle
from rich import print

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
    {"name": "+4", "wildcard": True, "quantity": 4, "value": 50},
    {"name": "🌈", "wildcard": True, "quantity": 4, "value": 50},
]
PLAYERS = [
    # Humans
    {"name": "You", "strategy": "human"},
    # Dumb Robots
    {"name": "R2D2", "strategy": "random"},
    {"name": "C3PO", "strategy": "random"},
    {"name": "BB8", "strategy": "random"},
    {"name": "Bender", "strategy": "random"},
    # Smart robots
    {"name": "Wall-E", "strategy": "smart"},
    {"name": "Optimus Prime", "strategy": "smart"},
    {"name": "Megatron", "strategy": "smart"},
    {"name": "HAL 9000", "strategy": "smart"},
    {"name": "TARS", "strategy": "smart"},
]
INITIAL_CARDS = 7

# Get number of players from arguments
n_players = 4
try:
    n_players = int(sys.argv[1])
except Exception:
    pass


class UnoCard:
    """
    A card definition in absolute, not related to any particular game
    """

    def __init__(self, name, color, value):
        self.name = name
        self.color = color
        self.value = value
        self.penalty = None

        match self.name:
            case "+4":
                self.penalty = 4
            case "+2":
                self.penalty = 2
            case "🚫":
                self.penalty = 0

    def print_card(self, end="\n"):
        """
        Pretty-print the card to the console
        """
        print(f"[white on {self.color}]{self.name:^3}", end=end)

    def __str__(self) -> str:
        return f"{self.name} {self.color}"


class UnoPlayer:
    """
    A player in a specific game
    """

    def __init__(self, name, game, strategy="smart"):
        self.name = name
        self.game = game
        self.hand = []
        self.strategy = strategy

    def print_hand_prompt(self):
        """
        Display the player's hand, with a number for each card so it can be played,
        and an indicator if the card can be played
        """
        for i, card in enumerate(self.hand):
            if self.game.can_play_card(card):
                print(f"[green bold]{i+1:>2}. ", end="")
            else:
                print(" x. ", end="")
            card.print_card()

    def show_hand(self):
        """
        Display the player's hand, without any prompt or playability indicator
        """
        for card in self.hand:
            card.print_card(end=" ")
        print()

    def can_play(self):
        """
        Check if the player can play any card in their hand
        """
        return any(self.game.can_play_card(card) for card in self.hand)

    def play_card(self, card_index, new_color_override=None):
        """
        Play a specific card from the player's hand, including an overriding color for wildcard cards
        """
        card = self.hand[card_index]
        if self.game.can_play_card(card):
            self.hand.pop(card_index)

            # Override color if needed
            if new_color_override:
                card.color = new_color_override

            self.game.play_card(card)

            return card
        return None

    def draw_card(self, card):
        """
        Add a new card to the player's hand
        """
        self.hand.append(card)

    def has_won(self):
        """
        Check if the player has won the game, i.e. has no cards left
        """
        return self.card_count() == 0

    def card_value(self, card):
        """
        Estimates a card's playing strength based on the player's strategy
        """
        value = 0
        match self.strategy:
            case "random":
                value = randint(0, 100)
            case "smart":
                # Play higher card to reduce points
                value = card.value

                # Play wildcards last
                if card.color != WILDCARD_COLOR:
                    value += 100

                # Play highest penalties first
                value += card.penalty or 0

        return value

    def auto_play(self):
        """
        Plays the best card according to the player's strategy
        """
        playable_cards = [card for card in self.hand if self.game.can_play_card(card)]
        if playable_cards:
            card = playable_cards[0]
            for c in playable_cards:
                if self.card_value(c) > self.card_value(card):
                    card = c

            # If the card is a wildcard, choose a random color to play
            color = None
            if card.color == WILDCARD_COLOR:
                color = COLORS[randint(0, 3)]

            return self.play_card(self.hand.index(card), color)
        return None

    def score(self):
        """
        Calculate the player's penalty score based on the cards left in their hand
        """
        return sum(card.value for card in self.hand)

    def card_count(self):
        """
        Return the number of cards in the player's hand
        """
        return len(self.hand)


class UnoGame:
    """
    A game of Uno with a specific set of players
    """

    def __init__(self, n_players=len(PLAYERS)):
        self.deck = self.create_deck()
        self.players = [
            UnoPlayer(player["name"], game=self, strategy=player["strategy"])
            for player in PLAYERS[:n_players]
        ]
        self.top_card = None
        self.current_player_idx = 0
        self.direction = 1
        self.penalty = None
        self.discard_pile = []

        # Deal initial hands
        for _ in range(INITIAL_CARDS):
            for player_idx in range(self.player_count()):
                self.deal_card_to_player(player_idx)

        # Place top card
        self.play_card(self.draw_card())

    def create_deck(self):
        """
        Returns a new full deck of Uno cards, shuffled
        """
        deck = []
        for card_type in CARD_TYPES:
            if card_type["wildcard"]:
                for _ in range(card_type["quantity"]):
                    deck.append(
                        UnoCard(card_type["name"], WILDCARD_COLOR, card_type["value"])
                    )
            else:
                for color in COLORS:
                    for _ in range(card_type["quantity"]):
                        deck.append(
                            UnoCard(card_type["name"], color, card_type["value"])
                        )

        shuffle(deck)
        return deck

    def print_top_card(self):
        """
        Pretty-print the top card of the discard pile
        """
        self.top_card.print_card()

    def play_card(self, card):
        """
        Play a card on top of the discard pile, updating the game state accordingly
        """
        # NOTE: we're not checking card legality here, because its color might have been overridden...
        self.top_card = card
        self.discard_pile.append(card)

        # Set the penalty for next player if any
        self.penalty = card.penalty

        # Change game direction if needed
        if card.name == "🔄":
            if self.player_count() > 2:
                self.direction *= -1
            else:
                # The reverse card acts as a skip if there's only 2 players
                self.penalty = 0

        return card

    def can_play_card(self, card):
        """
        Check if a card can be played on top of the current top card
        """
        return (
            card.name == self.top_card.name
            or card.color == self.top_card.color
            or card.color == WILDCARD_COLOR
            or self.top_card.color == WILDCARD_COLOR  # If the first card is a wildcard
        )

    def deal_card_to_player(self, player_idx):
        """
        Draw a new card from the pile and deal it to a specific player
        """
        card = self.draw_card()
        if card:
            self.players[player_idx].draw_card(card)
            return True
        return False

    def deal_card(self):
        """
        Draw a new card from the pile and deal it to the current player
        """
        return self.deal_card_to_player(self.current_player_idx)

    def has_winner(self):
        """
        Check if any player has won the game
        """
        return any(player.has_won() for player in self.players)

    def next_player(self):
        """
        Move to the next player in the game, considering the direction
        """
        self.current_player_idx = (
            self.current_player_idx + self.direction
        ) % self.player_count()

    def draw_card(self):
        """
        Draw a new card from the deck and return it,
        reshuffling the discard pile if needed, so we never run out of cards
        """
        # Shuffle discard pile and use it as the new deck if the deck is empty
        if not len(self.deck):
            self.deck = self.discard_pile
            shuffle(self.deck)
            self.discard_pile = []

        return self.deck.pop()

    def current_player(self):
        """
        Return the player whose turn it is
        """
        return self.players[self.current_player_idx]

    def apply_penalty(self):
        """
        Apply the penalty to the current player, if any
        """
        if self.penalty is not None:
            for _ in range(self.penalty):
                self.deal_card()
            self.penalty = None
            self.next_player()
            return True
        return False

    def player_count(self):
        """
        Return the number of players in the game
        """
        return len(self.players)


def prompt_color():
    print("[bold green]Choose a color to play:")
    for i, color in enumerate(COLORS):
        print(f"[white on {color}]{i+1:^3}")
    while True:
        try:
            return COLORS[int(input()) - 1]
        except Exception:
            print("[red]Invalid input, try again")


def prompt_card(player):
    while True:
        try:
            card_index = int(input()) - 1
            card = player.hand[card_index]

            # If the card is a wildcard, prompt for color to play
            if player.game.can_play_card(card):
                color = None
                if card.color == WILDCARD_COLOR:
                    color = prompt_color()

                return card_index, color
            else:
                print("[red]You can't play that card!")
        except Exception:
            print("[red]Invalid input, try again")


try:
    game = UnoGame(n_players)
    print(
        f"Starting game with {game.player_count()} players:",
        ", ".join([p.name for p in game.players]),
    )

    while not game.has_winner():
        player = game.current_player()
        print()
        print(f"[bold blue]{player.name}'s turn ({player.card_count()} cards left)")

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
        if not player.can_play():
            print("[yellow]Can't play, drawing")
            game.deal_card()

        # Skip if you still cannot play anything
        if not player.can_play():
            print("[red]Still can't play, skipping")
            game.next_player()
            continue

        played_card = None
        if player.strategy == "human":
            # It's the only human player, show hand and prompt for play
            print("Your hand:")
            player.print_hand_prompt()

            print("[green bold]Which card do you want to play?")
            idx, color_override = prompt_card(player)
            played_card = player.play_card(idx, color_override)
        else:
            # It's an AI player, play automatically
            # input("Press Enter to continue...")
            played_card = player.auto_play()

        if played_card:
            print(f"{player.name} played: ", end="")
            played_card.print_card()
            if played_card.name == "🔄" and game.player_count() > 2:
                print(
                    f"[yellow]Reversing game direction to {'clockwise' if game.direction == 1 else 'counterclockwise'}"
                )

        # Check if we need to say UNO
        if player.card_count() == 1:
            print(f"[yellow]{player.name} says UNO!")

        # Check if anyone won
        if player.has_won():
            print(f"[bold green]{player.name} wins! 🎉")
            break

        game.next_player()

    # Show scores
    print()
    print("[bold blue]Final penalties:")
    score = 0
    winner = None
    for player in game.players:
        score += player.score()
        print(
            f"[bold blue]{player.name}[/bold blue]: {player.score()} ",
            end="",
        )
        if player.has_won():
            winner = player
            print(" 🏆")
        else:
            player.show_hand()

    print()
    print(f"Total score for [bold blue]{winner.name}[/bold blue]: [red]{score}")

except KeyboardInterrupt:
    print("[red]Game interrupted, exiting...")
