import random

class MontyHallSimulator(object):

    """
    TODO: build a Monty Hall game simulator

    https://en.wikipedia.org/wiki/Monty_Hall_problem
    """

    def __init__(self):
        self.num_doors = 3
        self.doors = [''] * self.num_doors
        self.pos_car = random.randint(0,self.num_doors-1)
        self.doors[self.pos_car] = 'c'
        for i, d in enumerate(self.doors):
            if d != 'c':
                self.doors[i] = 'g'

        self.player_guess = None
        self.host_select = None

    def player_selects_door(self, d):
        self.player_selection = d
        return d
    
    def reveal_goat(self):
        goat_positions = []
        for i, d in enumerate(self.doors):
            if d == 'g' and i != self.player_selection:
                goat_positions.append(i)
        return goat_positions[random.randint(0,len(goat_positions)-1)]

    def reveal_car(self):
        for i, d in enumerate(self.doors):
            if d == 'c':
                return i

    def run_game(self, num, strategy):
        correct_guesses = 0
        for _ in range(num):
            initial_choice = random.randint(0,self.num_doors-1)
            self.player_selects_door(initial_choice)
            pos_goat = self.reveal_goat()

            new_player_selection = initial_choice
            if strategy == 'switch':
                for i in range(self.num_doors):
                    if i != pos_goat and i != initial_choice:
                        new_player_selection = i

            pos_car = self.reveal_car()
            if pos_car == new_player_selection:
                correct_guesses += 1
        
        return float(correct_guesses) / num


N = 10000
correct_guesses_stay = 0

s = MontyHallSimulator()
print("stay", s.run_game(N,'stay'))
print("switch", s.run_game(N,'switch'))

