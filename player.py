'''
Ultra-aggressive pokerbot, written in Python.
'''
from skeleton.actions import FoldAction, CallAction, CheckAction, RaiseAction
from skeleton.states import GameState, TerminalState, RoundState
from skeleton.states import NUM_ROUNDS, STARTING_STACK, BIG_BLIND, SMALL_BLIND
from skeleton.bot import Bot
from skeleton.runner import parse_args, run_bot

import random
import eval7

class Player(Bot):
    '''
    An ultra-aggressive pokerbot that applies constant pressure.
    '''

    def __init__(self):
        '''
        Initialize the bot with aggressive parameters.
        '''
        self.aggression_factor = 0.8  # High aggression factor
        self.min_raise_multiplier = 2.5  # Minimum raise size as multiple of pot
        self.bluff_frequency = 0.3  # Frequency of bluffs
        self.hand_history = []  # Track hand history for pattern recognition
        self.opponent_stats = {
            'folds': 0,
            'calls': 0,
            'raises': 0,
            'total_hands': 0
        }

    def handle_new_round(self, game_state, round_state, active):
        '''
        Called when a new round starts.
        '''
        self.current_hand = {
            'my_cards': round_state.hands[active],
            'board_cards': [],
            'my_position': 'BB' if active else 'SB',
            'actions_taken': []
        }

    def handle_round_over(self, game_state, terminal_state, active):
        '''
        Called when a round ends.
        '''
        # Update opponent statistics
        previous_state = terminal_state.previous_state
        if previous_state.street > 0:  # Only count completed hands
            self.opponent_stats['total_hands'] += 1
            if terminal_state.deltas[1-active] < 0:  # Opponent lost chips
                self.opponent_stats['folds'] += 1
            elif terminal_state.deltas[1-active] == 0:  # Opponent called
                self.opponent_stats['calls'] += 1
            else:  # Opponent raised
                self.opponent_stats['raises'] += 1

    def evaluate_hand_strength(self, my_cards, board_cards):
        '''
        Evaluate the current hand strength using eval7.
        '''
        if not board_cards:  # Pre-flop
            return 0.5  # Neutral pre-flop strength for aggressive play
        try:
            hole_cards = [eval7.Card(card) for card in my_cards]
            community_cards = [eval7.Card(card) for card in board_cards]
            score = eval7.evaluate(hole_cards + community_cards)
            return score / 7462  # Normalize score between 0 and 1
        except:
            return 0.5

    def get_action(self, game_state, round_state, active):
        '''
        Implement ultra-aggressive strategy.
        '''
        legal_actions = round_state.legal_actions()
        street = round_state.street
        my_cards = round_state.hands[active]
        board_cards = round_state.deck[:street]
        my_pip = round_state.pips[active]
        opp_pip = round_state.pips[1-active]
        my_stack = round_state.stacks[active]
        opp_stack = round_state.stacks[1-active]
        pot = my_pip + opp_pip
        to_call = opp_pip - my_pip

        # Update current hand information
        self.current_hand['board_cards'] = board_cards
        self.current_hand['actions_taken'].append({
            'street': street,
            'pot_size': pot,
            'continue_cost': to_call
        })

        # Calculate hand strength
        hand_strength = self.evaluate_hand_strength(my_cards, board_cards)

        # Ultra-aggressive strategy
        if RaiseAction in legal_actions:
            min_raise, max_raise = round_state.raise_bounds()
            raise_amount = int(pot * self.min_raise_multiplier)
            
            if hand_strength > 0.6:
                raise_amount = min(max_raise)
            elif street == 0:  # Pre-flop
                if self.current_hand['my_position'] == 'BB':
                    raise_amount = min(max_raise, pot * 3)
                else:
                    return CallAction()
            else:
                x = random.randint(0,500)
                if x % 7 == 0:
                    raise_amount = min(max_raise)
                else:
                    raise_amount = min(max_raise, raise_amount*6)

            # Ensure raise amount is within bounds
            raise_amount = max(min_raise, max_raise)
            return RaiseAction(raise_amount)

        # If we can't raise, call if the pot odds are favorable
        if CallAction in legal_actions:
            pot_odds = to_call / (pot + to_call)
            if hand_strength > pot_odds or random.random() < self.aggression_factor:
                return CallAction()

        # If we can't call or raise, check if possible
        if CheckAction in legal_actions:
            return CheckAction()
        
        # If nothing else is possible, fold
        return FoldAction()

if __name__ == '__main__':
    run_bot(Player(), parse_args())
