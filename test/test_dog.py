# tests/test_dog.py

import pytest
from server.py.dog import Dog, Card, Marble, PlayerState, Action, GameState, GamePhase


@pytest.fixture
def game_instance():
    """Fixture to create a fresh instance of the Dog game."""
    return Dog()


# --- Initialization Tests ---

def test_initialization(game_instance):
    """Test game initialization."""
    state = game_instance.get_state()
    assert state.phase == GamePhase.RUNNING, "Game should start in RUNNING phase."
    assert len(state.list_player) == 4, "There should be 4 players."
    assert len(state.list_card_draw) == 110 - (
                4 * 6), "Draw pile should have 86 cards after dealing 6 to each of 4 players."
    for player in state.list_player:
        assert len(player.list_card) == 6, "Each player should start with 6 cards."
        assert len(player.list_marble) == 4, "Each player should have 4 marbles."
        for marble in player.list_marble:
            assert 64 <= marble.pos <= 95, "Marble positions should start in the kennel (64 to 95)."
            assert not marble.is_save, "Marbles should not be in a saved state at initialization."


def test_reset_function(game_instance):
    """Test game reset functionality."""
    game_instance.reset()
    state = game_instance.get_state()
    assert state.phase == GamePhase.RUNNING, "Game should be in RUNNING phase after reset."
    assert len(state.list_player) == 4, "There should be 4 players after reset."
    assert len(state.list_card_draw) == 110 - (4 * 6), "Draw pile should have 86 cards after reset."
    for player in state.list_player:
        assert len(player.list_card) == 6, "Each player should have 6 cards after reset."
        for marble in player.list_marble:
            assert 64 <= marble.pos <= 95, "Marble positions should reset to the kennel (64 to 95)."
            assert not marble.is_save, "Marbles should not be in a saved state after reset."


# --- Path Blocking Tests ---

def test_is_path_blocked_no_block(game_instance):
    """Test path blocking when path is clear."""
    state = game_instance.get_state()
    game_instance.set_state(state)
    assert not game_instance.is_path_blocked(4, 8), "Path should not be blocked when no marbles are on it."


def test_is_path_blocked_with_block(game_instance):
    """Test path blocking with an obstacle marble."""
    state = game_instance.get_state()
    # Place a safe marble at position 6 to block the path from 4 to 8
    state.list_player[0].list_marble[0].pos = 6
    state.list_player[0].list_marble[0].is_save = True
    game_instance.set_state(state)
    assert game_instance.is_path_blocked(4, 8), "Path should be blocked by a safe marble at position 6."


def test_is_path_blocked_circular_path(game_instance):
    """Test path blocking with circular board logic."""
    state = game_instance.get_state()
    # Place a safe marble at position 1 to block the path from 62 to 2 (assuming circular board)
    state.list_player[0].list_marble[0].pos = 1
    state.list_player[0].list_marble[0].is_save = True
    game_instance.set_state(state)
    assert game_instance.is_path_blocked(62,
                                         2), "Path should be blocked by a safe marble at position 1 in circular path."


# --- Action Generation Tests ---

def test_generate_actions_start_card(game_instance):
    """Test generating actions for A/K cards to start marbles."""
    state = game_instance.get_state()
    active_player = state.list_player[0]
    # Assign an Ace to the active player
    active_player.list_card = [Card(suit='♠', rank='A')]
    # Ensure one marble is in the kennel (position 64)
    for marble in active_player.list_marble:
        marble.pos = 64
    game_instance.set_state(state)
    actions = game_instance.get_list_action()
    # Expect one action: moving a marble from kennel (64) to start position (0)
    expected_action = Action(
        card=Card(suit='♠', rank='A'),
        pos_from=64,
        pos_to=0,
        card_swap=None
    )
    assert expected_action in actions, "Should have an action to move a marble from kennel to start using Ace."


def test_generate_actions_normal_move(game_instance):
    """Test generating actions for normal forward move cards."""
    state = game_instance.get_state()
    active_player = state.list_player[0]
    # Assign a '5' card to the active player
    active_player.list_card = [Card(suit='♠', rank='5')]
    # Place a marble at position 10
    active_player.list_marble[0].pos = 10
    active_player.list_marble[0].is_save = False
    game_instance.set_state(state)
    actions = game_instance.get_list_action()
    # Expect one action: moving from 10 to 15
    expected_action = Action(
        card=Card(suit='♠', rank='5'),
        pos_from=10,
        pos_to=15,
        card_swap=None
    )
    assert expected_action in actions, "Should have an action to move marble from 10 to 15 using '5' card."


def test_generate_actions_joker_beginning_phase(game_instance):
    """Test generating actions for Joker card swaps in the beginning phase."""
    state = game_instance.get_state()
    active_player = state.list_player[0]
    # Assign a Joker to the active player
    joker_card = Card(suit='', rank='JKR')
    active_player.list_card = [joker_card]
    # Place a marble in the kennel
    active_player.list_marble[0].pos = 64
    active_player.list_marble[0].is_save = False
    # Ensure it's the beginning phase (all marbles >=64)
    for player in state.list_player:
        for marble in player.list_marble:
            marble.pos = 64  # All marbles in kennel
    game_instance.set_state(state)
    actions = game_instance.get_list_action()
    # Expect two actions:
    # 1. Move a marble from kennel (64) to start (0)
    # 2. Swap Joker with any 'A' or 'K'
    expected_move_action = Action(
        card=joker_card,
        pos_from=64,
        pos_to=0,
        card_swap=None
    )
    assert expected_move_action in actions, "Should have an action to move marble from kennel to start using Joker."
    # Since it's the beginning phase, swap actions should be available
    swap_actions = [action for action in actions if action.card == joker_card and action.card_swap is not None]
    assert len(swap_actions) > 0, "Should have at least one swap action available for Joker in beginning phase."


def test_generate_actions_joker_non_beginning_phase(game_instance):
    """Test generating actions for Joker card swaps in a non-beginning phase."""
    state = game_instance.get_state()
    active_player = state.list_player[0]
    # Assign a Joker to the active player
    joker_card = Card(suit='', rank='JKR')
    active_player.list_card = [joker_card]
    # Place a marble in the kennel
    active_player.list_marble[0].pos = 64
    active_player.list_marble[0].is_save = False
    # Move one marble out of kennel to transition out of beginning phase
    active_player.list_marble[1].pos = 0
    active_player.list_marble[1].is_save = True
    game_instance.set_state(state)
    actions = game_instance.get_list_action()
    # Expect two actions:
    # 1. Move a marble from kennel (64) to start (0)
    # 2. Swap Joker with any card except 'JKR'
    expected_move_action = Action(
        card=joker_card,
        pos_from=64,
        pos_to=0,
        card_swap=None
    )
    assert expected_move_action in actions, "Should have an action to move marble from kennel to start using Joker."
    # Since it's not the beginning phase, swap actions should be with any card except 'JKR'
    swap_actions = [action for action in actions if action.card == joker_card and action.card_swap is not None]
    assert len(swap_actions) > 0, "Should have at least one swap action available for Joker in non-beginning phase."


def test_generate_actions_j_with_opponent_marbles(game_instance):
    """Test generating actions for 'J' card when opponents have marbles to swap."""
    state = game_instance.get_state()
    active_player = state.list_player[0]
    opponent_player = state.list_player[1]
    # Assign a 'J' card to the active player
    j_card = Card(suit='♠', rank='J')
    active_player.list_card = [j_card]
    # Place active player's marble at position 10
    active_player.list_marble[0].pos = 10
    active_player.list_marble[0].is_save = False
    # Place opponent's marble at position 12
    opponent_player.list_marble[0].pos = 12
    opponent_player.list_marble[0].is_save = False
    game_instance.set_state(state)
    actions = game_instance.get_list_action()
    # Expect two actions:
    # 1. Swap active player's marble at 10 with opponent's marble at 12
    # 2. Swap opponent's marble at 12 with active player's marble at 10
    expected_action1 = Action(
        card=j_card,
        pos_from=10,
        pos_to=12,
        card_swap=None
    )
    expected_action2 = Action(
        card=j_card,
        pos_from=12,
        pos_to=10,
        card_swap=None
    )
    assert expected_action1 in actions, "Should have an action to swap marble from 10 to 12 using 'J' card."
    assert expected_action2 in actions, "Should have an action to swap marble from 12 to 10 using 'J' card."


def test_generate_actions_j_with_no_opponent_marbles(game_instance):
    """Test generating actions for 'J' card when no opponent marbles are available to swap."""
    state = game_instance.get_state()
    active_player = state.list_player[0]
    # Assign a 'J' card to the active player
    j_card = Card(suit='♠', rank='J')
    active_player.list_card = [j_card]
    # Place active player's marbles on the board
    active_player.list_marble[0].pos = 10
    active_player.list_marble[0].is_save = False
    active_player.list_marble[1].pos = 15
    active_player.list_marble[1].is_save = False
    # Ensure no opponent has marbles on the board
    for player in state.list_player[1:]:
        for marble in player.list_marble:
            marble.pos = 64  # In kennel
            marble.is_save = False
    game_instance.set_state(state)
    actions = game_instance.get_list_action()
    # Since no opponent marbles are available, 'J' should allow swapping between active player's marbles
    expected_action1 = Action(
        card=j_card,
        pos_from=10,
        pos_to=15,
        card_swap=None
    )
    expected_action2 = Action(
        card=j_card,
        pos_from=15,
        pos_to=10,
        card_swap=None
    )
    assert expected_action1 in actions, "Should have an action to swap marble from 10 to 15 using 'J' card."
    assert expected_action2 in actions, "Should have an action to swap marble from 15 to 10 using 'J' card."


# --- Action Application Tests ---

def test_apply_action_move_marble(game_instance):
    """Test applying an action to move a marble."""
    state = game_instance.get_state()
    active_player = state.list_player[0]
    # Assign a '2' card to the active player
    move_card = Card(suit='♠', rank='2')
    active_player.list_card = [move_card]
    # Place a marble at position 10
    active_player.list_marble[0].pos = 10
    active_player.list_marble[0].is_save = False
    game_instance.set_state(state)
    # Define the action to move marble from 10 to 12
    action = Action(
        card=move_card,
        pos_from=10,
        pos_to=12,
        card_swap=None
    )
    game_instance.apply_action(action)
    updated_state = game_instance.get_state()
    # Verify the marble has moved to 12
    assert updated_state.list_player[0].list_marble[0].pos == 12, "Marble should have moved from 10 to 12."


def test_apply_action_kick_opponent(game_instance):
    """Test applying an action that kicks an opponent's marble."""
    state = game_instance.get_state()
    active_player = state.list_player[0]
    opponent_player = state.list_player[1]
    # Assign a '2' card to the active player
    move_card = Card(suit='♠', rank='2')
    active_player.list_card = [move_card]
    # Place active player's marble at 10
    active_player.list_marble[0].pos = 10
    active_player.list_marble[0].is_save = False
    # Place opponent's marble at 12
    opponent_player.list_marble[0].pos = 12
    opponent_player.list_marble[0].is_save = False
    game_instance.set_state(state)
    # Define the action to move from 10 to 12, kicking opponent's marble
    action = Action(
        card=move_card,
        pos_from=10,
        pos_to=12,
        card_swap=None
    )
    game_instance.apply_action(action)
    updated_state = game_instance.get_state()
    # Verify active player's marble moved to 12
    assert updated_state.list_player[0].list_marble[0].pos == 12, "Active player's marble should have moved to 12."
    # Verify opponent's marble was sent to kennel (72)
    assert updated_state.list_player[1].list_marble[
               0].pos == 72, "Opponent's marble should have been sent to kennel at 72."


def test_apply_action_joker_swap_beginning_phase(game_instance):
    """Test applying a Joker card swap action in the beginning phase."""
    state = game_instance.get_state()
    active_player = state.list_player[0]
    # Assign a Joker to the active player
    joker_card = Card(suit='', rank='JKR')
    active_player.list_card = [joker_card]
    # Define the action to swap Joker with an 'A' card
    swap_card = Card(suit='♠', rank='A')
    action = Action(
        card=joker_card,
        pos_from=None,
        pos_to=None,
        card_swap=swap_card
    )
    # Ensure the active player has a marble in the kennel to allow swapping
    active_player.list_marble[0].pos = 64
    active_player.list_marble[0].is_save = False
    game_instance.set_state(state)
    game_instance.apply_action(action)
    updated_state = game_instance.get_state()
    # Verify that the active player's card is now 'A'
    assert updated_state.card_active == swap_card, "Card active should now be 'A' after Joker swap."
    # Verify that Joker has been removed from the player's hand
    assert joker_card not in updated_state.list_player[
        0].list_card, "Joker card should be removed from player's hand after swap."


def test_apply_action_joker_swap_non_beginning_phase(game_instance):
    """Test applying a Joker card swap action in a non-beginning phase."""
    state = game_instance.get_state()
    active_player = state.list_player[0]
    # Assign a Joker to the active player
    joker_card = Card(suit='', rank='JKR')
    active_player.list_card = [joker_card]
    # Place a marble in the kennel
    active_player.list_marble[0].pos = 64
    active_player.list_marble[0].is_save = False
    # Move one marble out of kennel to transition out of beginning phase
    active_player.list_marble[1].pos = 0
    active_player.list_marble[1].is_save = True
    game_instance.set_state(state)
    # Define the action to swap Joker with an 'A' card
    swap_card = Card(suit='♠', rank='A')
    action = Action(
        card=joker_card,
        pos_from=None,
        pos_to=None,
        card_swap=swap_card
    )
    game_instance.apply_action(action)
    updated_state = game_instance.get_state()
    # Verify that the active player's card is now 'A'
    assert updated_state.card_active == swap_card, "Card active should now be 'A' after Joker swap."
    # Verify that Joker has been removed from the player's hand
    assert joker_card not in updated_state.list_player[
        0].list_card, "Joker card should be removed from player's hand after swap."


def test_apply_action_seven_card_initial_move(game_instance):
    """Test applying a SEVEN card's initial move."""
    state = game_instance.get_state()
    active_player = state.list_player[0]
    # Assign a '7' card to the active player
    seven_card = Card(suit='♠', rank='7')
    active_player.list_card = [seven_card]
    # Place a marble at position 12
    active_player.list_marble[0].pos = 12
    active_player.list_marble[0].is_save = False
    game_instance.set_state(state)
    # Define the action to move from 12 to 76 (5 steps)
    action = Action(
        card=seven_card,
        pos_from=12,
        pos_to=76,
        card_swap=None
    )
    game_instance.apply_action(action)
    updated_state = game_instance.get_state()
    # Verify the marble has moved to 76
    assert updated_state.list_player[0].list_marble[
               0].pos == 76, "Marble should have moved from 12 to 76 using SEVEN card."
    # Verify steps_remaining is updated correctly (7 - 5 = 2)
    assert game_instance.steps_remaining == 2, "Steps remaining should be 2 after moving 5 steps with SEVEN card."
    # Verify that SEVEN card is still active
    assert updated_state.card_active == seven_card, "SEVEN card should still be active after partial movement."


def test_apply_action_seven_card_final_move(game_instance):
    """Test applying a SEVEN card's final move."""
    state = game_instance.get_state()
    active_player = state.list_player[0]
    # Assign a '7' card to the active player and set steps_remaining to 2
    seven_card = Card(suit='♠', rank='7')
    active_player.list_card = [seven_card]
    game_instance.steps_remaining = 2
    active_player.list_marble[0].pos = 76
    active_player.list_marble[0].is_save = False
    game_instance.set_state(state)
    # Define the action to move from 76 to 78 (2 steps)
    action = Action(
        card=seven_card,
        pos_from=76,
        pos_to=78,
        card_swap=None
    )
    game_instance.apply_action(action)
    updated_state = game_instance.get_state()
    # Verify the marble has moved to 78
    assert updated_state.list_player[0].list_marble[
               0].pos == 78, "Marble should have moved from 76 to 78 using SEVEN card."
    # Verify steps_remaining is reset
    assert game_instance.steps_remaining is None, "Steps remaining should be None after completing SEVEN card actions."
    # Verify SEVEN card is removed from player's hand
    assert seven_card not in updated_state.list_player[
        0].list_card, "SEVEN card should be removed from player's hand after completion."


def test_apply_action_seven_card_exceed_steps(game_instance):
    """Test applying a SEVEN card exceeding remaining steps."""
    state = game_instance.get_state()
    active_player = state.list_player[0]
    # Assign a '7' card to the active player and set steps_remaining to 2
    seven_card = Card(suit='♠', rank='7')
    active_player.list_card = [seven_card]
    game_instance.steps_remaining = 2
    active_player.list_marble[0].pos = 76
    active_player.list_marble[0].is_save = False
    game_instance.set_state(state)
    # Define the action to move from 76 to 80 (4 steps), exceeding remaining steps
    action = Action(
        card=seven_card,
        pos_from=76,
        pos_to=80,
        card_swap=None
    )
    # Applying this action should raise a ValueError
    with pytest.raises(ValueError, match="Exceeded remaining steps for SEVEN."):
        game_instance.apply_action(action)
    updated_state = game_instance.get_state()
    # Marble should remain at 76
    assert updated_state.list_player[0].list_marble[0].pos == 76, "Marble should not move when exceeding steps."
    # Steps_remaining should remain unchanged
    assert game_instance.steps_remaining == 2, "Steps remaining should not change when action is invalid."


def test_apply_action_j_swap_with_opponent_marble(game_instance):
    """Test applying a 'J' card to swap with an opponent's marble."""
    state = game_instance.get_state()
    active_player = state.list_player[0]
    opponent_player = state.list_player[1]
    # Assign a 'J' card to the active player
    j_card = Card(suit='♠', rank='J')
    active_player.list_card = [j_card]
    # Place active player's marble at 10
    active_player.list_marble[0].pos = 10
    active_player.list_marble[0].is_save = False
    # Place opponent's marble at 12
    opponent_player.list_marble[0].pos = 12
    opponent_player.list_marble[0].is_save = False
    game_instance.set_state(state)
    # Define the action to swap active player's marble at 10 with opponent's at 12
    action = Action(
        card=j_card,
        pos_from=10,
        pos_to=12,
        card_swap=None
    )
    game_instance.apply_action(action)
    updated_state = game_instance.get_state()
    # Verify active player's marble is now at 12
    assert updated_state.list_player[0].list_marble[0].pos == 12, "Active player's marble should have moved to 12."
    # Verify opponent's marble is now at 10
    assert updated_state.list_player[1].list_marble[0].pos == 10, "Opponent's marble should have moved to 10."


def test_apply_action_j_swap_no_opponent_marble(game_instance):
    """Test applying a 'J' card when no opponent's marble is present at target position."""
    state = game_instance.get_state()
    active_player = state.list_player[0]
    # Assign a 'J' card to the active player
    j_card = Card(suit='♠', rank='J')
    active_player.list_card = [j_card]
    # Place active player's marble at 10
    active_player.list_marble[0].pos = 10
    active_player.list_marble[0].is_save = False
    # Ensure no opponent has a marble at 15
    for player in state.list_player[1:]:
        for marble in player.list_marble:
            marble.pos = 20  # Different position
            marble.is_save = False
    game_instance.set_state(state)
    # Define the action to swap active player's marble at 10 with opponent's at 15 (no marble there)
    action = Action(
        card=j_card,
        pos_from=10,
        pos_to=15,
        card_swap=None
    )
    # Applying this action should not change any marbles
    game_instance.apply_action(action)
    updated_state = game_instance.get_state()
    # Marble should remain at 10
    assert updated_state.list_player[0].list_marble[
               0].pos == 10, "Marble should not move when no opponent's marble is present."
    # No marbles should be at 15
    for player in updated_state.list_player[1:]:
        for marble in player.list_marble:
            assert marble.pos != 15, "No opponent's marble should be at 15."


# --- Game Progression Tests ---

def test_round_progression(game_instance):
    """Test if the game progresses to the next round correctly."""
    game_instance.reset()  # Ensure starting from a fresh state
    state = game_instance.get_state()

    # Ensure game is in RUNNING phase
    assert state.phase == GamePhase.RUNNING, "Game should be in RUNNING phase."
    initial_cnt_round = state.cnt_round
    initial_idx_player_started = state.idx_player_started

    # Set active player to last before starting player
    state.idx_player_active = (state.idx_player_started - 1) % state.cnt_player

    # Temporarily bypass win condition by setting all marbles' positions to 0
    for player in state.list_player:
        for marble in player.list_marble:
            marble.pos = 0  # Positions set to 0 are on the board and not in finish

    # Ensure no actions are available for the active player by clearing their hand
    active_player = state.list_player[state.idx_player_active]
    active_player.list_card = []  # Clear the active player's hand

    game_instance.set_state(state)

    # Check available actions before applying
    available_actions = game_instance.get_list_action()
    assert len(available_actions) == 0, "There should be no available actions for the active player."

    # Apply action to simulate end of turn
    game_instance.apply_action(None)

    updated_state = game_instance.get_state()

    # Validate that the round has incremented
    assert updated_state.cnt_round == initial_cnt_round + 1, f"Expected cnt_round to be {initial_cnt_round + 1}, got {updated_state.cnt_round}"

    # Validate that idx_player_active has advanced correctly
    expected_idx_player_active = (initial_idx_player_started) % state.cnt_player
    assert updated_state.idx_player_active == expected_idx_player_active, \
        f"Expected idx_player_active to be {expected_idx_player_active}, got {updated_state.idx_player_active}"

    # Validate that idx_player_started has advanced correctly
    expected_idx_player_started = (initial_idx_player_started + 1) % state.cnt_player
    assert updated_state.idx_player_started == expected_idx_player_started, \
        f"Expected idx_player_started to be {expected_idx_player_started}, got {updated_state.idx_player_started}"

    # Validate that bool_card_exchanged is reset
    assert not updated_state.bool_card_exchanged, "bool_card_exchanged should be reset after round progression."

    # Validate that new cards have been dealt based on the new cnt_round
    # Round 2: cards_per_player = 7 - 2 = 5
    expected_cards_per_player = 7 - updated_state.cnt_round  # 7 - 2 = 5
    for player in updated_state.list_player:
        assert len(player.list_card) == expected_cards_per_player, \
            f"Each player should have {expected_cards_per_player} cards in round {updated_state.cnt_round}."


def test_win_condition(game_instance):
    """Test if the game ends when a team wins."""
    state = game_instance.get_state()
    active_player = state.list_player[0]
    partner_player = state.list_player[2]
    # Set all active player's marbles to positions >=68
    for marble in active_player.list_marble:
        marble.pos = 68
    # Set all partner player's marbles to positions >=68
    for marble in partner_player.list_marble:
        marble.pos = 76
    # Ensure no actions are possible
    active_player.list_card = []
    partner_player.list_card = []
    game_instance.set_state(state)
    # Apply action to check win condition
    game_instance.apply_action(None)
    updated_state = game_instance.get_state()
    assert updated_state.phase == GamePhase.FINISHED, "Game should be FINISHED when a team has all marbles in the finish area."


# --- Additional Edge Case Tests ---

def test_apply_action_move_beyond_board(game_instance):
    """Test attempting to move a marble beyond the board limits."""
    state = game_instance.get_state()
    active_player = state.list_player[0]
    # Assign a '10' card to the active player
    move_card = Card(suit='♠', rank='10')
    active_player.list_card = [move_card]
    # Place a marble at position 60
    active_player.list_marble[0].pos = 60
    active_player.list_marble[0].is_save = False
    game_instance.set_state(state)
    # Define the action to move from 60 to 70 (beyond 63)
    action = Action(
        card=move_card,
        pos_from=60,
        pos_to=70,
        card_swap=None
    )
    # Applying this action should not be allowed; expecting no change
    # Since dog.py does not raise an exception, we check that the move is not applied
    game_instance.apply_action(action)
    updated_state = game_instance.get_state()
    # Marble should remain at 60
    assert updated_state.list_player[0].list_marble[0].pos == 60, "Marble should not move beyond the board."


def test_apply_action_invalid_action(game_instance):
    """Test applying an invalid action that doesn't exist in player's hand."""
    state = game_instance.get_state()
    active_player = state.list_player[0]
    # Assign a '3' card to the active player
    move_card = Card(suit='♠', rank='3')
    active_player.list_card = [move_card]
    # Place a marble at position 5
    active_player.list_marble[0].pos = 5
    active_player.list_marble[0].is_save = False
    game_instance.set_state(state)
    # Define an action with a card not in player's hand
    invalid_card = Card(suit='♥', rank='4')
    action = Action(
        card=invalid_card,
        pos_from=5,
        pos_to=8,
        card_swap=None
    )
    # Applying this action should not affect the game state
    # Since dog.py does not raise an exception, we check that the move is not applied
    game_instance.apply_action(action)
    updated_state = game_instance.get_state()
    # Marble should remain at 5
    assert updated_state.list_player[0].list_marble[
               0].pos == 5, "Marble should not move when applying an invalid action."


def test_apply_action_swap_without_opponent_marble(game_instance):
    """Test swapping with a marble when no opponent's marble is present."""
    state = game_instance.get_state()
    active_player = state.list_player[0]
    # Assign a 'J' card to the active player
    swap_card = Card(suit='♠', rank='J')
    active_player.list_card = [swap_card]
    # Place active player's marble at position 10
    active_player.list_marble[0].pos = 10
    active_player.list_marble[0].is_save = False
    # Ensure no opponent has a marble at position 15
    for player in state.list_player[1:]:
        for marble in player.list_marble:
            marble.pos = 20  # Different position
            marble.is_save = False
    game_instance.set_state(state)
    # Define the action to swap active player's marble with a non-existent opponent's marble
    action = Action(
        card=swap_card,
        pos_from=10,
        pos_to=15,
        card_swap=None
    )
    # Applying this action should not change any marbles
    game_instance.apply_action(action)
    updated_state = game_instance.get_state()
    # Marble should remain at 10
    assert updated_state.list_player[0].list_marble[
               0].pos == 10, "Marble should not move when no opponent's marble is present."


# --- Comprehensive Coverage Tests ---

def test_apply_action_joker_swap_all_possible_swaps(game_instance):
    """Test Joker card swap actions for all possible A/K cards in beginning phase."""
    state = game_instance.get_state()
    active_player = state.list_player[0]
    # Assign a Joker to the active player
    joker_card = Card(suit='', rank='JKR')
    active_player.list_card = [joker_card]
    # Place a marble in the kennel
    active_player.list_marble[0].pos = 64
    active_player.list_marble[0].is_save = False
    # Ensure it's the beginning phase (all marbles >=64)
    for player in state.list_player:
        for marble in player.list_marble:
            marble.pos = 64  # All marbles in kennel
    game_instance.set_state(state)
    actions = game_instance.get_list_action()
    # There should be multiple swap actions for all A and K suits
    swap_cards = [Card(suit=suit, rank=rank) for suit in GameState.LIST_SUIT for rank in ['A', 'K']]
    swap_actions = [action for action in actions if action.card == joker_card and action.card_swap in swap_cards]
    assert len(swap_actions) == len(
        GameState.LIST_SUIT) * 2, f"Should have {len(GameState.LIST_SUIT) * 2} swap actions for Joker."


def test_apply_action_joker_swap_invalid_swap_card(game_instance):
    """Test Joker card swap with an invalid card (not A/K)."""
    state = game_instance.get_state()
    active_player = state.list_player[0]
    # Assign a Joker to the active player
    joker_card = Card(suit='', rank='JKR')
    active_player.list_card = [joker_card]
    # Place a marble in the kennel
    active_player.list_marble[0].pos = 64
    active_player.list_marble[0].is_save = False
    # Assign an invalid swap card (e.g., 'Q')
    invalid_swap_card = Card(suit='♠', rank='Q')
    action = Action(
        card=joker_card,
        pos_from=64,
        pos_to=0,
        card_swap=invalid_swap_card
    )
    game_instance.set_state(state)
    # Applying this action should swap the card_active to 'Q'
    game_instance.apply_action(action)
    updated_state = game_instance.get_state()
    # Verify that card_active is now 'Q'
    assert updated_state.card_active == invalid_swap_card, "Card active should now be 'Q' after Joker swap."
    # Verify that Joker has been removed from the player's hand
    assert joker_card not in updated_state.list_player[
        0].list_card, "Joker card should be removed from player's hand after swap."


# --- Random Player Tests ---

def test_random_player_selects_valid_action(game_instance):
    """Test that RandomPlayer selects a valid action from the available actions."""
    # Assuming RandomPlayer class is properly implemented
    # For this test, we'll mock the RandomPlayer's select_action method
    from server.py.dog import RandomPlayer
    import random

    state = game_instance.get_state()
    active_player = state.list_player[0]
    # Assign multiple actions to the active player
    active_player.list_card = [Card(suit='♠', rank='2'), Card(suit='♥', rank='3')]
    active_player.list_marble[0].pos = 10
    active_player.list_marble[0].is_save = False
    active_player.list_marble[1].pos = 20
    active_player.list_marble[1].is_save = False
    game_instance.set_state(state)
    actions = game_instance.get_list_action()
    # Initialize RandomPlayer
    random_player = RandomPlayer()
    selected_action = random_player.select_action(state, actions)
    assert selected_action in actions, "RandomPlayer should select an action from the available actions."


def test_random_player_no_action(game_instance):
    """Test that RandomPlayer returns None when no actions are available."""
    from server.py.dog import RandomPlayer
    import random

    state = game_instance.get_state()
    active_player = state.list_player[0]
    # Clear active player's hand and set marbles in finish to ensure no actions
    active_player.list_card = []
    for marble in active_player.list_marble:
        marble.pos = 68  # All marbles in finish
    game_instance.set_state(state)
    actions = game_instance.get_list_action()
    random_player = RandomPlayer()
    selected_action = random_player.select_action(state, actions)
    assert selected_action is None, "RandomPlayer should return None when no actions are available."


# --- Cleanup and Teardown Tests ---

def test_game_finish_phase(game_instance):
    """Test that the game phase is set to FINISHED when a team wins."""
    state = game_instance.get_state()
    active_player = state.list_player[0]
    partner_player = state.list_player[2]
    # Set all active player's marbles to positions >=68
    for marble in active_player.list_marble:
        marble.pos = 68
    # Set all partner player's marbles to positions >=68
    for marble in partner_player.list_marble:
        marble.pos = 76
    # Ensure no actions are possible
    active_player.list_card = []
    partner_player.list_card = []
    game_instance.set_state(state)
    # Apply action to check win condition
    game_instance.apply_action(None)
    updated_state = game_instance.get_state()
    assert updated_state.phase == GamePhase.FINISHED, "Game should be FINISHED when a team has all marbles in the finish area."


def test_game_continue_if_no_winner(game_instance):
    """Test that the game continues if no team has won."""
    state = game_instance.get_state()
    active_player = state.list_player[0]
    partner_player = state.list_player[2]
    # Set active player's marbles to positions >=68
    for marble in active_player.list_marble:
        marble.pos = 68
    # Set partner player's marbles to positions <68
    for marble in partner_player.list_marble:
        marble.pos = 60
    # Ensure there are actions available
    active_player.list_card = []
    partner_player.list_card = []
    game_instance.set_state(state)
    # Apply action to check that game continues
    game_instance.apply_action(None)
    updated_state = game_instance.get_state()
    assert updated_state.phase == GamePhase.RUNNING, "Game should continue running when no team has won."


def test_apply_action_exchange_card(game_instance):
    """Test exchanging a card between players."""
    state = game_instance.get_state()
    active_player = state.list_player[0]
    partner_player = state.list_player[2]
    # Assign a card to active player
    exchange_card = Card(suit='♠', rank='5')
    active_player.list_card = [exchange_card]
    # Ensure it's round 0 and no card has been exchanged
    state.cnt_round = 0
    state.bool_card_exchanged = False
    game_instance.set_state(state)
    # Define the action to exchange the card
    action = Action(
        card=exchange_card,
        pos_from=None,
        pos_to=None,
        card_swap=None
    )
    game_instance.apply_action(action)
    updated_state = game_instance.get_state()
    # Verify that the card has been moved to the partner player's hand
    assert exchange_card not in updated_state.list_player[
        0].list_card, "Exchanged card should be removed from active player's hand."
    assert exchange_card in updated_state.list_player[
        2].list_card, "Exchanged card should be added to partner player's hand."
    # Verify that bool_card_exchanged is set to True
    assert updated_state.bool_card_exchanged, "bool_card_exchanged should be True after exchanging a card."


def test_apply_action_end_round_no_actions(game_instance):
    """Test ending the round when no actions are available."""
    state = game_instance.get_state()
    active_player = state.list_player[0]
    # Clear active player's hand and set marbles in a state with no actions
    active_player.list_card = []
    for marble in active_player.list_marble:
        marble.pos = 68  # All marbles in finish
    game_instance.set_state(state)
    # Apply action to end turn
    game_instance.apply_action(None)
    updated_state = game_instance.get_state()
    # Verify that round has incremented
    assert updated_state.cnt_round == state.cnt_round + 1, "Round should have incremented after ending turn with no actions."
    # Verify that the active player has advanced
    expected_idx_player_active = (state.idx_player_active + 1) % state.cnt_player
    assert updated_state.idx_player_active == expected_idx_player_active, "Active player should have advanced to the next player."
