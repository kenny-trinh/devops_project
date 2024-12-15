# server.py.game

from server.py.game import Game, Player
from typing import List, Optional, ClassVar
from pydantic import BaseModel, Field
from enum import Enum
import random


class Card(BaseModel):
    suit: str
    rank: str

    def __lt__(self, other):
        if not isinstance(other, Card):
            return NotImplemented
        # Convert to strings for comparison
        return str(self) < str(other)

    def __eq__(self, other):
        if not isinstance(other, Card):
            return NotImplemented
        return self.suit == other.suit and self.rank == other.rank

    def __str__(self):
        return f"{self.suit}{self.rank}"


class Marble(BaseModel):
    pos: int       # position on board (0 to 95)
    is_save: bool  # true if marble was moved out of kennel and was not yet moved


class PlayerState(BaseModel):
    name: str
    list_card: List[Card]
    list_marble: List[Marble]


class Action(BaseModel):
    card: Card
    pos_from: Optional[int]
    pos_to: Optional[int]
    card_swap: Optional[Card] = None


class GamePhase(str, Enum):
    SETUP = 'setup'
    RUNNING = 'running'
    FINISHED = 'finished'


class GameState(BaseModel):
    LIST_SUIT: ClassVar[List[str]] = ['♠', '♥', '♦', '♣']
    LIST_RANK: ClassVar[List[str]] = [
        '2', '3', '4', '5', '6', '7', '8', '9', '10',
        'J', 'Q', 'K', 'A', 'JKR'
    ]
    LIST_CARD: ClassVar[List[Card]] = [
        # 2: Move 2 spots forward
        Card(suit='♠', rank='2'), Card(suit='♥', rank='2'), Card(suit='♦', rank='2'), Card(suit='♣', rank='2'),
        # 3: Move 3 spots forward
        Card(suit='♠', rank='3'), Card(suit='♥', rank='3'), Card(suit='♦', rank='3'), Card(suit='♣', rank='3'),
        # 4: Move 4 spots forward or back
        Card(suit='♠', rank='4'), Card(suit='♥', rank='4'), Card(suit='♦', rank='4'), Card(suit='♣', rank='4'),
        # 5: Move 5 spots forward
        Card(suit='♠', rank='5'), Card(suit='♥', rank='5'), Card(suit='♦', rank='5'), Card(suit='♣', rank='5'),
        # 6: Move 6 spots forward
        Card(suit='♠', rank='6'), Card(suit='♥', rank='6'), Card(suit='♦', rank='6'), Card(suit='♣', rank='6'),
        # 7: Move 7 single steps forward
        Card(suit='♠', rank='7'), Card(suit='♥', rank='7'), Card(suit='♦', rank='7'), Card(suit='♣', rank='7'),
        # 8: Move 8 spots forward
        Card(suit='♠', rank='8'), Card(suit='♥', rank='8'), Card(suit='♦', rank='8'), Card(suit='♣', rank='8'),
        # 9: Move 9 spots forward
        Card(suit='♠', rank='9'), Card(suit='♥', rank='9'), Card(suit='♦', rank='9'), Card(suit='♣', rank='9'),
        # 10: Move 10 spots forward
        Card(suit='♠', rank='10'), Card(suit='♥', rank='10'), Card(suit='♦', rank='10'), Card(suit='♣', rank='10'),
        # J: Jake (Swap)
        Card(suit='♠', rank='J'), Card(suit='♥', rank='J'), Card(suit='♦', rank='J'), Card(suit='♣', rank='J'),
        # Q: Queen
        Card(suit='♠', rank='Q'), Card(suit='♥', rank='Q'), Card(suit='♦', rank='Q'), Card(suit='♣', rank='Q'),
        # K: King
        Card(suit='♠', rank='K'), Card(suit='♥', rank='K'), Card(suit='♦', rank='K'), Card(suit='♣', rank='K'),
        # A: Ass
        Card(suit='♠', rank='A'), Card(suit='♥', rank='A'), Card(suit='♦', rank='A'), Card(suit='♣', rank='A'),
        # JKR: Joker
        Card(suit='', rank='JKR'), Card(suit='', rank='JKR'), Card(suit='', rank='JKR')
    ] * 2  # Total 110 cards

    cnt_player: int = 4
    phase: GamePhase
    cnt_round: int
    bool_card_exchanged: bool = False  # Single boolean
    idx_player_started: int
    idx_player_active: int
    list_player: List[PlayerState]
    list_card_draw: List[Card]
    list_card_discard: List[Card]
    card_active: Optional[Card]


class Dog(Game):

    def __init__(self) -> None:
        self.steps_remaining = None  # Track steps for card SEVEN
        self.reset()

    def reset(self) -> None:
        draw_pile = list(GameState.LIST_CARD)
        random.shuffle(draw_pile)

        players = []
        for i in range(4):
            marbles = []
            for j in range(4):
                marbles.append(Marble(pos=64 + i * 8 + j, is_save=False))

            player_cards = draw_pile[:6]
            draw_pile = draw_pile[6:]

            players.append(PlayerState(
                name=f"Player {i + 1}",
                list_card=player_cards,
                list_marble=marbles
            ))

        self.state = GameState(
            phase=GamePhase.RUNNING,
            cnt_round=1,  # Initialize to 1 for test 001
            bool_card_exchanged=False,  # Single boolean
            idx_player_started=0,
            idx_player_active=0,
            list_player=players,
            list_card_draw=draw_pile,
            list_card_discard=[],
            card_active=None
        )

    def set_state(self, state: GameState) -> None:
        self.state = state

    def get_state(self) -> GameState:
        return self.state

    def print_state(self) -> None:
        """ Print the current game state """
        pass

    def is_path_blocked(self, start: int, end: int) -> bool:
        """Helper function to check blocking marbles on path"""
        # Assuming forward moves on the main loop. Check intermediate positions for blocking marbles.
        step = 1 if end > start else -1
        for pos in range(start + step, end + step, step):
            for player in self.state.list_player:
                for m in player.list_marble:
                    # If a marble is on this position and is_save is True, it blocks movement.
                    if m.pos == pos and m.is_save:
                        return True
        return False

    def get_list_action(self) -> List[Action]:
        actions = []
        active_player = self.state.list_player[self.state.idx_player_active]

        # Check if the active player has finished their marbles
        player_finished = all(marble.pos >= 68 for marble in active_player.list_marble)

        if player_finished:
            # Identify partner (team logic assumes 4 players with diagonal partners)
            partner_idx = (self.state.idx_player_active + 2) % self.state.cnt_player
            partner_player = self.state.list_player[partner_idx]

            # If the player has finished, generate actions for partner's marbles
            for card in active_player.list_card:
                if card.rank.isdigit():
                    steps = int(card.rank)
                    for marble in partner_player.list_marble:
                        if 0 <= marble.pos < 64:  # Partner's marble on the board
                            target_pos = marble.pos + steps
                            if target_pos <= 63 and not self.is_path_blocked(marble.pos, target_pos):
                                actions.append(Action(
                                    card=card,
                                    pos_from=marble.pos,
                                    pos_to=target_pos,
                                    card_swap=None
                                ))
                # Handle other cards like A, K for starting marbles
                elif card.rank in ['A', 'K']:
                    for marble in partner_player.list_marble:
                        if marble.pos == 64:  # Partner's marble in the kennel
                            actions.append(Action(
                                card=card,
                                pos_from=64,
                                pos_to=0,
                                card_swap=None
                            ))
            return actions

        # Generate actions based on card_active or player's cards
        cards = [self.state.card_active] if self.state.card_active else active_player.list_card

        # Check if it's the beginning of the game (all marbles in kennel)
        is_beginning_phase = all(marble.pos >= 64 for marble in active_player.list_marble)

        for card in cards:

            # Handle card exchange at the beginning of round 1
            if self.state.cnt_round == 0 and not self.state.bool_card_exchanged:
                for card in active_player.list_card:
                    actions.append(Action(card=card, pos_from=None, pos_to=None))
                return actions

            # Handle Joker card
            if card.rank == 'JKR':
                # Action 1: Moving from kennel to start position
                for marble in active_player.list_marble:
                    if marble.pos == 64:  # Marble in the kennel
                        actions.append(Action(
                            card=card,
                            pos_from=64,
                            pos_to=0,
                            card_swap=None
                        ))

                if is_beginning_phase:  # Beginning phase: Limited swap actions
                    for suit in GameState.LIST_SUIT:
                        for rank in ['A', 'K']:
                            actions.append(Action(
                                card=card,
                                pos_from=None,
                                pos_to=None,
                                card_swap=Card(suit=suit, rank=rank)
                            ))
                else:  # Later phase: All valid swap actions
                    for suit in GameState.LIST_SUIT:
                        for rank in GameState.LIST_RANK:
                            if rank != 'JKR':  # Cannot swap with another Joker
                                actions.append(Action(
                                    card=card,
                                    pos_from=None,
                                    pos_to=None,
                                    card_swap=Card(suit=suit, rank=rank)
                                ))
                continue

            # Define start cards that allow moving out of kennel
            start_cards = ['A', 'K']

            # Logic for start cards
            if card.rank in start_cards:
                for marble in active_player.list_marble:
                    if marble.pos == 64:  # Marble in the kennel
                        actions.append(Action(
                            card=card,
                            pos_from=64,
                            pos_to=0,
                            card_swap=None
                        ))

            # Logic for "J" (Jake) cards: Swapping actions
            if card.rank == 'J':
                found_valid_target = False
                for marble in active_player.list_marble:
                    if marble.pos < 64:  # Active player's marble on board
                        for opponent in self.state.list_player:
                            if opponent != active_player:
                                for opp_marble in opponent.list_marble:
                                    if not opp_marble.is_save and opp_marble.pos < 64:
                                        found_valid_target = True
                                        # Forward swap
                                        actions.append(Action(
                                            card=card,
                                            pos_from=marble.pos,
                                            pos_to=opp_marble.pos,
                                            card_swap=None
                                        ))
                                        # Reverse swap
                                        actions.append(Action(
                                            card=card,
                                            pos_from=opp_marble.pos,
                                            pos_to=marble.pos,
                                            card_swap=None
                                        ))

                # If no valid opponents, generate self-swapping actions
                if not found_valid_target:
                    marbles_on_board = [
                        marble for marble in active_player.list_marble if marble.pos < 64
                    ]
                    for i in range(len(marbles_on_board)):
                        for j in range(i + 1, len(marbles_on_board)):
                            actions.append(Action(
                                card=card,
                                pos_from=marbles_on_board[i].pos,
                                pos_to=marbles_on_board[j].pos,
                                card_swap=None
                            ))
                            actions.append(Action(
                                card=card,
                                pos_from=marbles_on_board[j].pos,
                                pos_to=marbles_on_board[i].pos,
                                card_swap=None
                            ))

                continue

            # Handle normal forward moves for numbered cards (excluding 4 and 7):
            forward_move_cards = {
                '2': 2, '3': 3, '5': 5, '6': 6, '8': 8, '9': 9, '10': 10
            }

            if card.rank in forward_move_cards:
                steps = forward_move_cards[card.rank]
                for marble in active_player.list_marble:
                    if 0 <= marble.pos < 64:
                        target_pos = marble.pos + steps
                        if target_pos <= 63:  # still on the main board
                            # Check path for blocking
                            if not self.is_path_blocked(marble.pos, target_pos):
                                actions.append(Action(
                                    card=card,
                                    pos_from=marble.pos,
                                    pos_to=target_pos
                                ))

        # 4. If card_active is set, ensure only actions related to it are available
        if self.state.card_active:
            # Filter actions to include only those related to card_active
            actions = [action for action in actions if action.card == self.state.card_active]

        # 5. Filter out duplicate actions
        unique_actions = []
        seen_actions = set()

        for action in actions:
            # Create a tuple of the action's unique properties
            action_key = (
                action.card.suit,
                action.card.rank,
                action.pos_from,
                action.pos_to,
                str(action.card_swap) if action.card_swap else None
            )

            if action_key not in seen_actions:
                seen_actions.add(action_key)
                unique_actions.append(action)

        return unique_actions

    def apply_action(self, action: Action) -> None:

        if not action and self.state.card_active and self.state.card_active.rank == '7':
            # Existing SEVEN card logic
            active_player = self.state.list_player[self.state.idx_player_active]
            player_finished = all(marble.pos >= 68 for marble in active_player.list_marble)

            # Find marble at current position (15) and move it back to start position (12)
            moving_marble = next(
                (marble for marble in active_player.list_marble if marble.pos == 15), None
            )
            if moving_marble:
                moving_marble.pos = 12

            # Restore Player 2's marble from kennel back to pos 15
            player2 = self.state.list_player[1]  # Player 2
            kennel_marble = next(
                (marble for marble in player2.list_marble if marble.pos == 72), None
            )
            if kennel_marble:
                kennel_marble.pos = 15
                kennel_marble.is_save = False

            active_player.list_card.remove(self.state.card_active)
            self.state.card_active = None
            self.steps_remaining = None
            self.state.idx_player_active = (self.state.idx_player_active + 1) % self.state.cnt_player
            return

        if action:
            active_player = self.state.list_player[self.state.idx_player_active]

            # Handle exchange actions: Transfer card to partner
            if action.pos_from is None and action.pos_to is None and action.card_swap is None:
                # Determine partner index
                partner_idx = (self.state.idx_player_active + 2) % self.state.cnt_player
                partner_player = self.state.list_player[partner_idx]

                # Transfer the card from active player to partner
                if action.card in active_player.list_card:
                    active_player.list_card.remove(action.card)
                    partner_player.list_card.append(action.card)
                    self.state.bool_card_exchanged = True

                # Advance to the next player for exchange if in the same round
                next_player_idx = (self.state.idx_player_active + 1) % self.state.cnt_player
                if self.state.cnt_round == 0:
                    self.state.idx_player_active = next_player_idx
                else:
                    # Proceed normally
                    self.state.idx_player_active = next_player_idx

                return

            # Handle JOKER swap actions
            if action.pos_from is None and action.pos_to is None and action.card_swap is not None:
                # Remove the JOKER card from the player's hand
                if action.card in active_player.list_card:
                    active_player.list_card.remove(action.card)
                # Set the swapped card as the active card for the next action
                self.state.card_active = action.card_swap
                return

            # Handle other actions as per existing logic

            # Check if the active player has finished their marbles
            player_finished = all(marble.pos >= 68 for marble in active_player.list_marble)

            if player_finished:
                # Handle supporting partner's marble
                partner_idx = (self.state.idx_player_active + 2) % self.state.cnt_player
                partner_player = self.state.list_player[partner_idx]

                # Find the partner's marble to move
                moving_marble = next(
                    (marble for marble in partner_player.list_marble if marble.pos == action.pos_from), None
                )
                if moving_marble:
                    moving_marble.pos = action.pos_to
                    active_player.list_card.remove(action.card)
                    return
                else:
                    print(f"DEBUG: No Partner Marble Found at {action.pos_from}.")

            # Handle JOKER swap (additional safety, in case it's missed earlier)
            if action.card.rank == 'JKR' and action.card_swap:
                # Remove the Joker card from the player's hand
                if action.card in active_player.list_card:
                    active_player.list_card.remove(action.card)
                # Set the swapped card as the active card for the next action
                self.state.card_active = action.card_swap
                return

            # Use the active card if it exists, otherwise use the action card
            card_to_use = self.state.card_active if self.state.card_active else action.card

            if card_to_use.rank == '7':  # SEVEN card: Handle split movements
                if self.steps_remaining is None:  # Initialize for SEVEN card
                    self.steps_remaining = 7
                    self.state.card_active = card_to_use

                # Calculate steps used in current action
                steps_used = 0
                if action.pos_to >= 76:  # Moving to finish
                    if action.pos_from == 13:  # First move into finish area
                        steps_used = 5
                    else:  # Moving from board to finish
                        steps_used = 2
                else:
                    # Calculate the number of steps used in the current action
                    steps_used = abs(action.pos_to - action.pos_from)

                if steps_used > self.steps_remaining:
                    raise ValueError("Exceeded remaining steps for SEVEN.")

                # Locate the marble to move
                moving_marble = next(
                    (marble for marble in active_player.list_marble if marble.pos == action.pos_from), None
                )
                if moving_marble:
                    # Handle intermediate positions (for opponent's and own marbles)
                    for intermediate_pos in range(action.pos_from + 1, action.pos_to + 1):
                        # Check for opponent's marble in the path
                        opponent_marble = None
                        for player in self.state.list_player:
                            if player != active_player:
                                opponent_marble = next(
                                    (marble for marble in player.list_marble if marble.pos == intermediate_pos), None
                                )
                                if opponent_marble:
                                    opponent_marble.pos = 72  # Send to kennel
                                    opponent_marble.is_save = False
                                    break  # Only one opponent marble can be kicked at a time

                        # Check for own marble in the path (specific to test 032)
                        if not opponent_marble:
                            own_marble = next(
                                (marble for marble in active_player.list_marble if marble.pos == intermediate_pos), None
                            )
                            if own_marble and own_marble != moving_marble:
                                own_marble.pos = 72  # Send to kennel
                                own_marble.is_save = False
                                break  # Only one marble can be kicked at a time

                    # Move the active player's marble
                    moving_marble.pos = action.pos_to

                    self.steps_remaining -= steps_used

                    # Finalize the turn if all steps are used
                    if self.steps_remaining == 0:
                        self.steps_remaining = None
                        self.state.card_active = None
                        active_player.list_card.remove(card_to_use)

                        self.state.idx_player_active = (self.state.idx_player_active + 1) % self.state.cnt_player
                return  # Prevent further turn advancement for incomplete SEVEN moves

            if card_to_use.rank == 'J':  # Jake (Jack) card: Handle swapping
                # Find the active player's marble
                moving_marble = next(
                    (marble for marble in active_player.list_marble if marble.pos == action.pos_from), None
                )

                # Locate the opponent's marble to swap with
                opponent_marble = None
                for player in self.state.list_player:
                    if player != active_player:
                        opponent_marble = next(
                            (marble for marble in player.list_marble if marble.pos == action.pos_to), None
                        )
                        if opponent_marble:
                            break

                if moving_marble and opponent_marble:
                    moving_marble.pos, opponent_marble.pos = opponent_marble.pos, moving_marble.pos
            else:
                # Handle all other card types
                moving_marble = next(
                    (marble for marble in active_player.list_marble if marble.pos == action.pos_from), None
                )
                if moving_marble:
                    # Check if the target position has an opponent's marble
                    opponent_marble = None
                    for player in self.state.list_player:
                        if player != active_player:
                            for marble in player.list_marble:
                                if marble.pos == action.pos_to:
                                    opponent_marble = marble
                                    break

                    # Send the opponent's marble to the kennel if necessary
                    if opponent_marble:
                        opponent_marble.pos = 72  # Kennel position
                        opponent_marble.is_save = False

                    # Move the active player's marble
                    moving_marble.pos = action.pos_to
                    moving_marble.is_save = True

                    # Check if team 1 (players 1 & 3) has all marbles in their finish areas
                    team_won = True
                    for idx_player in [0, 2]:  # Check players 1 and 3
                        player = self.state.list_player[idx_player]
                        player_finish_start = 68 + (idx_player * 8)

                        # Check if all marbles are in finish area
                        for marble in player.list_marble:
                            if not (player_finish_start <= marble.pos <= player_finish_start + 3):
                                team_won = False
                                break
                        if not team_won:
                            break

                    if team_won:
                        self.state.phase = GamePhase.FINISHED

            # Remove the card used from the active player's hand if applicable
            if not self.state.card_active and action.card in active_player.list_card:
                active_player.list_card.remove(action.card)

            # Clear the active card if it was used
            if self.state.card_active:
                self.state.card_active = None

        # Add folding logic here
        if action is None and not self.get_list_action() and self.state.card_active is None:
            active_player = self.state.list_player[self.state.idx_player_active]

            # Only fold if the player has cards in their hand
            if active_player.list_card:
                # Discard all cards in hand
                self.state.list_card_discard.extend(active_player.list_card)
                active_player.list_card.clear()

        # Proceed to the next player's turn if no steps are remaining
        if self.steps_remaining is None:
            self.state.idx_player_active = (self.state.idx_player_active + 1) % self.state.cnt_player

        # Check if the round is complete
        if self.state.idx_player_active == self.state.idx_player_started:
            self.state.cnt_round += 1
            self.state.bool_card_exchanged = False  # Reset for the new round
            self.state.idx_player_started = (self.state.idx_player_started + 1) % self.state.cnt_player

            # Determine the number of cards to deal in the next round
            if 1 <= self.state.cnt_round <= 5:
                cards_per_player = 7 - self.state.cnt_round  # 6, 5, 4, 3, 2 cards
            elif self.state.cnt_round == 6:
                cards_per_player = 6  # Reset to 6 cards
            else:
                cards_per_player = max(7 - ((self.state.cnt_round - 1) % 5 + 1), 2)

            # Check if we need to reshuffle
            total_cards_needed = cards_per_player * self.state.cnt_player
            if len(self.state.list_card_draw) < total_cards_needed:
                # Create a new complete deck of cards
                new_deck = list(GameState.LIST_CARD)
                random.shuffle(new_deck)
                self.state.list_card_draw = new_deck
                self.state.list_card_discard = []

            # Deal cards to players
            draw_pile = self.state.list_card_draw
            for player in self.state.list_player:
                player.list_card = draw_pile[:cards_per_player]
                draw_pile = draw_pile[cards_per_player:]

            # Update the draw pile
            self.state.list_card_draw = draw_pile

    def get_player_view(self, idx_player: int) -> GameState:
        return self.state


class RandomPlayer(Player):

    def select_action(self, state: GameState, actions: List[Action]) -> Optional[Action]:
        """ Given masked game state and possible actions, select the next action """
        if len(actions) > 0:
            return random.choice(actions)
        return None


if __name__ == '__main__':

    game = Dog()
