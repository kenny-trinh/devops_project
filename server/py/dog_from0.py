from server.py.game import Game, Player
from typing import List, Optional, ClassVar
from pydantic import BaseModel
from enum import Enum
import random


class Card(BaseModel):
    suit: str  # card suit (color)
    rank: str  # card rank


class Marble(BaseModel):
    pos: int       # position on board (0 to 95)
    is_save: bool  # true if marble was moved out of kennel and was not yet moved


class PlayerState(BaseModel):
    name: str                  # name of player
    list_card: List[Card]      # list of cards
    list_marble: List[Marble]  # list of marbles


class Action(BaseModel):
    card: Card                 # card to play
    pos_from: Optional[int]    # position to move the marble from
    pos_to: Optional[int]      # position to move the marble to
    card_swap: Optional[Card]  # optional card to swap ()


class GamePhase(str, Enum):
    SETUP = 'setup'            # before the game has started
    RUNNING = 'running'        # while the game is running
    FINISHED = 'finished'      # when the game is finished


class GameState(BaseModel):

    LIST_SUIT: ClassVar[List[str]] = ['♠', '♥', '♦', '♣']  # 4 suits (colors)
    LIST_RANK: ClassVar[List[str]] = [
        '2', '3', '4', '5', '6', '7', '8', '9', '10',      # 13 ranks + Joker
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
        # Jake: A marble must be exchanged
        Card(suit='♠', rank='J'), Card(suit='♥', rank='J'), Card(suit='♦', rank='J'), Card(suit='♣', rank='J'),
        # Queen: Move 12 spots forward
        Card(suit='♠', rank='Q'), Card(suit='♥', rank='Q'), Card(suit='♦', rank='Q'), Card(suit='♣', rank='Q'),
        # King: Start or move 13 spots forward
        Card(suit='♠', rank='K'), Card(suit='♥', rank='K'), Card(suit='♦', rank='K'), Card(suit='♣', rank='K'),
        # Ass: Start or move 1 or 11 spots forward
        Card(suit='♠', rank='A'), Card(suit='♥', rank='A'), Card(suit='♦', rank='A'), Card(suit='♣', rank='A'),
        # Joker: Use as any other card you want
        Card(suit='', rank='JKR'), Card(suit='', rank='JKR'), Card(suit='', rank='JKR')
    ] * 2

    cnt_player: int = 4                # number of players (must be 4)
    phase: GamePhase                   # current phase of the game
    cnt_round: int                     # current round
    bool_card_exchanged: bool          # true if cards was exchanged in round
    idx_player_started: int            # index of player that started the round
    idx_player_active: int             # index of active player in round
    list_player: List[PlayerState]     # list of players
    list_card_draw: List[Card]         # list of cards to draw
    list_card_discard: List[Card]      # list of cards discarded
    card_active: Optional[Card]        # active card (for 7 and JKR with sequence of actions)


class Dog(Game):
    def __init__(self) -> None:
        """Game initialization (set_state call not necessary, we expect 4 players)"""
        self.state = GameState(
            cnt_player=4,
            phase=GamePhase.RUNNING,
            cnt_round=1,
            bool_card_exchanged=False,
            idx_player_started=0,
            idx_player_active=0,
            list_player=[],
            list_card_draw=GameState.LIST_CARD.copy(),
            list_card_discard=[],
            card_active=None
        )
        
        # Create draw pile
        self.state.list_card_draw = GameState.LIST_CARD.copy()
        random.shuffle(self.state.list_card_draw)
        
        # Create 4 players
        for i in range(4):
            player = PlayerState(
                name=f"Player {i+1}",
                list_card=[],
                list_marble=[
                    Marble(pos=64+i*4+j, is_save=False) 
                    for j in range(4)
                ]
            )
            # Deal initial 6 cards
            for _ in range(6):
                if self.state.list_card_draw:
                    player.list_card.append(self.state.list_card_draw.pop())
            self.state.list_player.append(player)

    def set_state(self, state: GameState) -> None:
        """Set the game to a given state"""
        self.state = state

    def get_state(self) -> GameState:
        """Get the complete, unmasked game state"""
        return self.state

    def print_state(self) -> None:
        """Print the current game state"""
        print(str(self.state))

    def get_list_action(self) -> List[Action]:
        """Get a list of possible actions for the active player"""
        actions = []
        if not self.state.bool_card_exchanged:
            # Card exchange at start of round
            player = self.state.list_player[self.state.idx_player_active]
            for card in player.list_card:
                actions.append(Action(
                    card=card,
                    pos_from=None,
                    pos_to=None,
                    card_swap=None
                ))
            return actions

        player = self.state.list_player[self.state.idx_player_active]

        if not player.list_card:
            return []

        # For each card in hand
        for card in player.list_card:
            # Handle marbles in kennel
            for marble in player.list_marble:
                if marble.pos >= 64:  # In kennel
                    # Start cards: Ace, King, Joker
                    if card.rank in ['A', 'K', 'JKR']:
                        start_pos = (self.state.idx_player_active * 16) % 64
                        # Check if blocked
                        blocked = False
                        for p in self.state.list_player:
                            for m in p.list_marble:
                                if m.pos == start_pos and m.is_save:
                                    blocked = True
                        if not blocked:
                            actions.append(Action(
                                card=card,
                                pos_from=marble.pos,
                                pos_to=start_pos,
                                card_swap=None
                            ))
                else:
                    # Regular moves
                    if card.rank in ['2', '3', '4', '5', '6', '8', '9', '10', 'Q']:
                        steps = {
                            '2': 2, '3': 3, '4': 4, '5': 5, '6': 6,
                            '8': 8, '9': 9, '10': 10, 'Q': 12
                        }[card.rank]
                        pos_to = (marble.pos + steps) % 64
                        actions.append(Action(
                            card=card,
                            pos_from=marble.pos,
                            pos_to=pos_to,
                            card_swap=None
                        ))
                    elif card.rank == 'A':
                        # Ace can move 1 or 11
                        for steps in [1, 11]:
                            pos_to = (marble.pos + steps) % 64
                            actions.append(Action(
                                card=card,
                                pos_from=marble.pos,
                                pos_to=pos_to,
                                card_swap=None
                            ))
                    elif card.rank == 'K':
                        pos_to = (marble.pos + 13) % 64
                        actions.append(Action(
                            card=card,
                            pos_from=marble.pos,
                            pos_to=pos_to,
                            card_swap=None
                        ))

        return actions

    def apply_action(self, action: Optional[Action]) -> None:
        """Apply the given action to the game"""
        if action is None:
            # Handle skipping turn
            if len(self.state.list_player[self.state.idx_player_active].list_card) == 0:
                # Move to next player
                self.state.idx_player_active = (self.state.idx_player_active + 1) % 4
                
                # If round is over, start new round
                if self.state.idx_player_active == self.state.idx_player_started:
                    self.state.cnt_round += 1
                    self.state.bool_card_exchanged = False
                    cards_per_round = [6, 5, 4, 3, 2]
                    cards_to_deal = cards_per_round[(self.state.cnt_round - 1) % len(cards_per_round)]
                    
                    # Move cards to discard pile
                    for player in self.state.list_player:
                        self.state.list_card_discard.extend(player.list_card)
                        player.list_card = []
                    
                    # Reshuffle if needed
                    if len(self.state.list_card_draw) < cards_to_deal * 4:
                        self.state.list_card_draw.extend(self.state.list_card_discard)
                        self.state.list_card_discard = []
                        random.shuffle(self.state.list_card_draw)
                    
                    # Deal new cards
                    for player in self.state.list_player:
                        for _ in range(cards_to_deal):
                            if self.state.list_card_draw:
                                player.list_card.append(self.state.list_card_draw.pop())
            return

        player = self.state.list_player[self.state.idx_player_active]

        # Handle card exchange at start of round
        if not self.state.bool_card_exchanged and action.pos_from is None and action.pos_to is None:
            # Exchange with partner (2 players away)
            partner_idx = (self.state.idx_player_active + 2) % 4
            partner = self.state.list_player[partner_idx]
            
            player.list_card.remove(action.card)
            partner.list_card.append(action.card)
            
            self.state.idx_player_active = (self.state.idx_player_active + 1) % 4
            if self.state.idx_player_active == self.state.idx_player_started:
                self.state.bool_card_exchanged = True
            return

        # Handle marble movement
        if action.pos_from is not None and action.pos_to is not None:
            # Move marble
            for marble in player.list_marble:
                if marble.pos == action.pos_from:
                    marble.pos = action.pos_to
                    marble.is_save = (action.pos_to % 16 == 0)
                    break
            
            # Remove used card
            if action.card in player.list_card:
                player.list_card.remove(action.card)
                self.state.list_card_discard.append(action.card)
            
            # Next player
            if not self.state.card_active:
                self.state.idx_player_active = (self.state.idx_player_active + 1) % 4

    def get_player_view(self, idx_player: int) -> GameState:
        """Get the masked state for the active player"""
        state = self.get_state()
        
        masked_state = GameState(
            cnt_player=state.cnt_player,
            phase=state.phase,
            cnt_round=state.cnt_round,
            bool_card_exchanged=state.bool_card_exchanged,
            idx_player_started=state.idx_player_started,
            idx_player_active=state.idx_player_active,
            list_player=[],
            list_card_draw=state.list_card_draw.copy(),
            list_card_discard=state.list_card_discard.copy(),
            card_active=state.card_active
        )
        
        # Copy players, hiding others' cards
        for i, player in enumerate(state.list_player):
            if i == idx_player:
                masked_state.list_player.append(player)
            else:
                masked_player = PlayerState(
                    name=player.name,
                    list_card=[],
                    list_marble=player.list_marble.copy()
                )
                masked_state.list_player.append(masked_player)
                
        return masked_state


class RandomPlayer(Player):

    def select_action(self, state: GameState, actions: List[Action]) -> Optional[Action]:
        """ Given masked game state and possible actions, select the next action """
        if len(actions) > 0:
            return random.choice(actions)
        return None


if __name__ == '__main__':

    game = Dog()
