from rich import print
from random import shuffle, randint

COLORS = ["red", "green", "blue", "yellow"]
CARD_TYPES = [
    # Number cards
    {"name": "0", "colored": True, "quantity": 1, "value": 0},
    {"name": "1", "colored": True, "quantity": 2, "value": 1},
    {"name": "2", "colored": True, "quantity": 2, "value": 2},
    {"name": "3", "colored": True, "quantity": 2, "value": 3},
    {"name": "4", "colored": True, "quantity": 2, "value": 4},
    {"name": "5", "colored": True, "quantity": 2, "value": 5},
    {"name": "6", "colored": True, "quantity": 2, "value": 6},
    {"name": "7", "colored": True, "quantity": 2, "value": 7},
    {"name": "8", "colored": True, "quantity": 2, "value": 8},
    {"name": "9", "colored": True, "quantity": 2, "value": 9},
    # Colored specials
    {"name": "+2", "colored": True, "quantity": 2, "value": 20},
    {"name": "🔄", "colored": True, "quantity": 2, "value": 20},
    {"name": "🚫", "colored": True, "quantity": 2, "value": 20},
    # Black cards
    {"name": "+4", "colored": False, "quantity": 4, "value": 40},
    {"name": "🌈", "colored": False, "quantity": 4, "value": 40},
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


def create_deck():
    deck = []
    for card in CARD_TYPES:
        if card["colored"]:
            for color in COLORS:
                for _ in range(card["quantity"]):
                    deck.append(
                        {"name": card["name"], "color": color, "value": card["value"]}
                    )
        else:
            for _ in range(card["quantity"]):
                deck.append({"name": card["name"], "color": "grey"})

    shuffle(deck)
    return deck


def print_card(card):
    if card and "name" in card and "color" in card:
        print(f"[white on {card['color']}]{card['name']:^3}", end="")


def print_top_card(game):
    top_card = game["top_card"]
    print_card(top_card)
    print()


def print_hand(game, player):
    for i, card in enumerate(game["players"][player]["hand"]):
        if can_play_card(game, card):
            print(f"[green bold]{i+1:>2}. ", end="")
        else:
            print(f"[gray] x. ", end="")
        print_card(card)
        print()


def can_play_card(game, card):
    top_card = game["top_card"]
    return (
        card["name"] == top_card["name"]
        or card["color"] == top_card["color"]
        or card["color"] == "grey"
    )


def player_can_play(game, player):
    player_hand = game["players"][player]["hand"]
    return any(can_play_card(game, card) for card in player_hand)


def deal_card(game, player):
    if game["deck"] and len(game["deck"]):
        game["players"][player]["hand"].append(game["deck"].pop())
        return True
    return False


def draw_card(game):
    if game["deck"] and len(game["deck"]):
        game["top_card"] = game["deck"].pop()
        return True
    return False


def play_card(game, player, card_index, color_override=None):
    if can_play_card(game, game["players"][player]["hand"][card_index]):
        card = game["players"][player]["hand"].pop(card_index)

        # Override color if needed
        if color_override:
            card["color"] = color_override

        game["top_card"] = card

        # Change game direction if needed
        if card["name"] == "🔄":
            game["direction"] *= -1

        # Set the penalty for next player if any
        if card["name"] in ["+2", "+4", "🚫"]:
            game["penalty"] = card["name"]

        print(f"{game['players'][player]['name']} played ", end="")
        print_card(card)
        print()

        return True
    return False


def auto_play(game, player):
    player_hand = game["players"][player]["hand"]
    playable_cards = [card for card in player_hand if can_play_card(game, card)]
    if playable_cards:
        # TODO: be smarter, e.g. play the highest value but save wildcards for last...
        # Play the first eligible one...
        card = playable_cards[0]

        # If the card is a wildcard, choose a random color to play
        color = None
        if card["color"] == "grey":
            color = COLORS[randint(0, 3)]

        return play_card(game, player, player_hand.index(card), color)
    return False


def check_winner(game):
    for player in game["players"]:
        if len(player["hand"]) == 0:
            game["winner"] = player
            return True
    return False


def next_player(game):
    game["current_player"] = (game["current_player"] + game["direction"]) % len(
        game["players"]
    )


def prompt_color():
    print("[bold green]Choose a color to play:")
    for i, color in enumerate(COLORS):
        print(f"[white on {color}]{i+1:^2}")
    while True:
        try:
            return COLORS[int(input()) - 1]
        except Exception:
            print("[red]Invalid input, try again")


current_game = {
    "deck": create_deck(),
    "players": [{"name": player, "hand": []} for player in PLAYERS],
    "top_card": None,
    "current_player": 0,
    "direction": 1,
    "winner": None,
    "penalty": None,
}

# Deal cards
for _ in range(INITIAL_CARDS):
    for player in range(len(PLAYERS)):
        # print(f"Dealing to {PLAYERS[player]}")
        deal_card(current_game, player)

# Place top card
draw_card(current_game)

while not current_game["winner"]:
    player = current_game["current_player"]
    print(f"[bold blue]{current_game['players'][player]['name']}'s turn")

    # print(current_game)

    print("Top card: ", end="")
    print_top_card(current_game)

    # Apply penalties if needed
    if current_game["penalty"]:
        match current_game["penalty"]:
            case "+4":
                print("[red]Penalty: 4 cards 🥵")
                deal_card(current_game, player)
                deal_card(current_game, player)
                deal_card(current_game, player)
                deal_card(current_game, player)
            case "+2":
                print("[red]Penalty: 2 cards 😓")
                deal_card(current_game, player)
                deal_card(current_game, player)
            case "🚫":
                print("[red]Penalty: Skipping 😔")
        current_game["penalty"] = None
        next_player(current_game)
        continue

    # Draw if you cannot play anything
    if not player_can_play(current_game, player):
        print("[yellow]Can't play, drawing")
        deal_card(current_game, player)

    # Skip if you still cannot play anything
    if not player_can_play(current_game, player):
        print("[yellow]Still can't play, skipping")
        next_player(current_game)
        continue

    if player == 0:
        # It's the only human player, show hand and prompt for play
        print("Your hand:")
        print_hand(current_game, player)

        print("[green bold]Which card do you want to play?")
        valid_play = False
        while not valid_play:
            try:
                card_index = int(input()) - 1

                # If the card is a wildcard, prompt for color to play
                color = None
                if (
                    current_game["players"][player]["hand"][card_index]["color"]
                    == "grey"
                ):
                    color = prompt_color()

                if play_card(current_game, player, card_index, color):
                    valid_play = True

                else:
                    print("[red]You can't play that card!")
            except Exception:
                print("[red]Invalid input, try again")
    else:
        # It's an AI player, play automatically
        auto_play(current_game, player)

    # Check if anyone won/lost
    if check_winner(current_game):
        print(f"[bold green]{current_game['winner']['name']} wins! 🎉")
        break

    next_player(current_game)


# Show scores
print()
print("[blue]Final scores:")
for player in current_game["players"]:
    print(f"{player['name']}: {sum(card['value'] for card in player['hand'])}")
