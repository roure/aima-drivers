import search
import random
from enum import Enum
import sys
from itertools import product
import copy


def manhattan_distance(origin, destination):
    return abs(origin[0]-destination[0]) + abs(origin[1]-destination[1])


class CO2(search.Problem):
    def path_cost(self, c, state1, action, state2):
        return super().path_cost(c, state1, action, state2)

    def __init__(self, initial, goal=None):
        super().__init__(initial, goal)

    def goal_test(self, state):
        return state.is_final_state()

    def result(self, state, action):
        act = action[0]
        new_state = copy.deepcopy(state)

        if act == 'add':
            old_driver, old_passenger = action[1:]
            driver = new_state.get_driver(old_driver.user['id'])
            passenger = new_state.get_user(old_passenger['id'])
            new_state.add_passenger_to_driver(passenger,driver)
        elif act == 'swap':
            old_driver1, old_driver2 = action[1:]
            driver1 = new_state.get_driver(old_driver1.user['id'])
            driver2 = new_state.get_driver(old_driver2.user['id'])
            new_state.swap_best_passengers(driver1, driver2)
        elif act == 'driver_as_passenger':
            old_driver, old_driver_as_passenger = action[1:]
            driver = new_state.get_driver(old_driver.user['id'])
            driver_as_passenger = new_state.get_driver(old_driver_as_passenger.user['id'])
            new_state.add_driver_as_passenger(driver, driver_as_passenger)

        return new_state

    def value(self, state):
        # print(state.global_distance())
        return state.N * 300 - state.global_distance()

    def actions(self, state):
        actions = self.generate_add_passenger_actions(state)
        if len(state.actual_drivers) > 1:
            actions.extend(self.generate_swap_actions(state))
        if not state.remaining_passengers and state.drivers_with_no_passengers:
            actions.extend(self.generate_driver_as_passenger_actions(state))

        # print(actions)
        return actions

    def generate_add_passenger_actions(self, state):
        actions = []
        for d, p in product(state.drivers, state.remaining_passengers):
            actions.append(['add',d,p])
        return actions

    def generate_swap_actions(self, state):
        actions = []
        pairs_of_drivers = [[d1, d2] for d1, d2 in product(state.actual_drivers, repeat=2) if d1 != d2 and \
                            d1 not in state.drivers_with_no_passengers and d2 not in state.drivers_with_no_passengers]
        for d1, d2 in pairs_of_drivers:
            actions.append(['swap',d1,d2])
        return actions

    def generate_driver_as_passenger_actions(self, state):
        actions = []
        pairs_of_drivers = [[d, p] for d, p in product(state.actual_drivers, state.drivers_with_no_passengers) if d != p]
        for d, p in pairs_of_drivers:
            actions.append(['driver_as_passenger', d, p])
        return actions


class State:
    def __init__(self, n=200, m=100, num_streets=100, max_drive_distance=300):
        self.N = n
        self.M = m
        self.NUM_STREETS = num_streets
        self.MAX_DRIVE_DISTANCE = max_drive_distance
        self.users = []
        self.passengers = []
        self.drivers = []
        self.actual_drivers = []
        self.drivers_with_no_passengers = []
        self.remaining_passengers = []
        self.drivers_index = [None] * self.N

    def generate_random_problem (self):
        self.__generate_users()
        self.__generate_drivers_passengers()

    def __generate_users(self):
        for i in range(self.N):
            user = {}
            user['id'] = i
            user['origin'] = [random.randrange(self.NUM_STREETS) for _ in range(2)]
            user['destination'] = [random.randrange(self.NUM_STREETS) for _ in range(2)]
            self.users.append(user)

    def __generate_drivers_passengers(self):
        users_sequence = range(self.N)
        passengers = random.sample(users_sequence, self.M)
        for i in users_sequence:
            if i in passengers:
                self.passengers.append(self.users[i])
            else:
                self.drivers.append(Driver(self.users[i]))
                self.drivers_index[i] = self.drivers[-1]
        self.remaining_passengers = list(self.passengers)
        self.drivers_with_no_passengers = list(self.drivers)
        self.actual_drivers = list(self.drivers)

    def get_user(self, id):
        return self.users[id]

    def get_driver(self, id):
        return self.drivers_index[id]

    def is_final_state(self):
        return not self.remaining_passengers

    def global_distance(self):
        dist = 0
        for d in self.actual_drivers:
            dist += d.distance()

        dist += self.MAX_DRIVE_DISTANCE * len(self.remaining_passengers)

        return dist

    def swap_best_passengers(self, driver1, driver2):
        old_distance = driver1.distance() + driver2.distance()
        min_dist = {'dist': old_distance, 'passenger_d1': None, 'passenger_d2': None}
        for p1, p2 in product(driver1.get_passengers(), driver2.get_passengers()):
            cdriver1 = copy.deepcopy(driver1)
            cdriver2 = copy.deepcopy(driver2)

            cdriver1.remove_passenger(p1)
            cdriver2.remove_passenger(p2)

            cdriver1.add_passenger(p2)
            cdriver2.add_passenger(p1)
            if cdriver1.has_passenger(p2) and cdriver2.has_passenger(p1) and \
                            min_dist['dist'] > cdriver1.distance() + cdriver2.distance():
                min_dist['dist'] = cdriver1.distance() + cdriver2.distance()
                min_dist['passenger_d1'] = p2
                min_dist['passenger_d2'] = p1

        if min_dist['dist'] < old_distance:
            # Actually swap passengers
            pos = driver1.remove_passenger(min_dist['passenger_d2'])
            assert(len(pos) == 2)
            pos = driver2.remove_passenger(min_dist['passenger_d1'])
            assert(len(pos) == 2)
            driver1.add_passenger(min_dist['passenger_d1'])
            driver2.add_passenger(min_dist['passenger_d2'])
            return [p1,p2]
        return []

    def add_passenger_to_driver(self, passenger, driver):
        added = driver.add_passenger(passenger)
        if added:
            self.remaining_passengers.remove(passenger)
            if driver in self.drivers_with_no_passengers:
                self.drivers_with_no_passengers.remove(driver)

    def add_driver_as_passenger(self, driver, driver_as_passenger):
        added = driver.add_passenger(driver_as_passenger.user)
        if added:
            self.drivers_with_no_passengers.remove(driver_as_passenger)
            self.actual_drivers.remove(driver_as_passenger)
            if driver in self.drivers_with_no_passengers:
                self.drivers_with_no_passengers.remove(driver)

    def __str__(self):
        s = "Actual drivers: \n"
        for d in self.actual_drivers:
            s += d.__str__() + "\n"
        return s


class TravelOp(Enum):
    TAKE = 1
    DROP = 2


class Driver:
    def __init__(self, user):
        self.user = user
        self.travel = []  # a list of {'op': take/drop, 'passenger': user}

    def distance(self):
        if not self.travel:
            return manhattan_distance(self.user['origin'], self.user['destination'])
        else:
            dist = manhattan_distance(self.user['origin'], self.travel[0]['passenger']['origin'])
            for i in range(len(self.travel)-1):
                org = self.__get_passenger_origin_or_dest_upon_travelop(i)
                dest = self.__get_passenger_origin_or_dest_upon_travelop(i+1)
                dist += manhattan_distance(org, dest)
            dist += manhattan_distance(self.travel[-1]['passenger']['destination'], self.user['destination'])
            return dist

    def __get_passenger_origin_or_dest_upon_travelop(self, i):
        return self.travel[i]['passenger']['origin'] if self.travel[i]['op'] == TravelOp.TAKE \
                else self.travel[i]['passenger']['destination']

    def __calculate_legal_takes_drops(self):
        take = 0
        legal_takes_drops = []
        for t in range(len(self.travel)):
            for d in range(t, len(self.travel)+1):
                if self.__is_legal_take_drop_op(t, d):
                    legal_takes_drops.append([t,d])
        legal_takes_drops.append([len(self.travel), len(self.travel)])
        return legal_takes_drops

    def __is_legal_take_drop_op(self, t, d):
        take = 0
        for op in self.travel[0:t]:
            if op['op'] == TravelOp.TAKE:
                take += 1
            else:
                take -= 1
        if take >= 2:
            return False

        take += 1
        for op in self.travel[t:d]:
            if op['op'] == TravelOp.TAKE:
                take += 1
            else:
                take -= 1
            if take > 2:
                return False
        if take <= 2:
            return True

    # mandatory or not
    def add_passenger(self, passenger):
        added = False
        if not self.travel:
            self.travel.insert(0, {'op': TravelOp.TAKE, 'passenger': passenger})
            self.travel.insert(1, {'op': TravelOp.DROP, 'passenger': passenger})
            added = True
            if self.distance() > 300:
                self.travel.pop()
                self.travel.pop()
                added = False
        else:
            l = len(self.travel)
            min_dist = {'dist': sys.maxsize, 'pos': [0,0]}
            legal_takes_pos = self.__calculate_legal_takes_drops()
            for p in legal_takes_pos:
                self.travel.insert(p[1], {'op': TravelOp.DROP, 'passenger': passenger})
                self.travel.insert(p[0], {'op': TravelOp.TAKE, 'passenger': passenger})
                dist = self.distance()
                if dist < min_dist['dist']:
                    min_dist = {'dist': dist, 'pos': p}
                self.travel.pop(p[0])
                self.travel.pop(p[1])
            if min_dist['dist'] <= 300:
                self.travel.insert(min_dist['pos'][1], {'op': TravelOp.DROP, 'passenger': passenger})
                self.travel.insert(min_dist['pos'][0], {'op': TravelOp.TAKE, 'passenger': passenger})
                added = True
        if self.is_over_occupied():
            print('Overocupied: {}'.format(self.travel))
        assert(not self.is_over_occupied())
        return added

    def add_passenger_in_pos(self, passenger, pos_take, pos_drop):
        # insert first the take operation and then the drop one
        self.travel.insert(pos_take, {'op': TravelOp.TAKE, 'passenger': passenger})
        self.travel.insert(pos_drop, {'op': TravelOp.DROP, 'passenger': passenger})
        assert(not self.is_over_occupied())

    def is_over_occupied(self):
        take = 0
        for op in self.travel:
            if op['op'] == TravelOp.TAKE:
                take += 1
            else:
                take -= 1
            if take > 2:
                return True
        return False

    def get_passengers(self):
        return [op['passenger'] for op in self.travel if op['op'] == TravelOp.TAKE]

    def has_passenger(self, passenger):
        return passenger in self.get_passengers()

    def remove_passenger(self, user):
        pos = self.__find_pos_passenger(user)
        if pos:
            self.travel.pop(pos[1])  # drop operation
            self.travel.pop(pos[0])  # take operation
        return pos

    def __find_pos_passenger(self, user):
        pos = []
        idx = 0
        for op in self.travel:
            if op['passenger']['id'] == user['id']:
                pos.append(idx)
            idx += 1
        assert(len(pos) == 2 or not pos)
        return pos

    def __str__(self):
        return 'driver: {} Route: {}'.format(self.user['id'], self.travel)

"""
This is going to call the Hill Climbing algorithm
"""

state = State(n=100, m=50)
state.generate_random_problem()

print('Initial global distance: {}'.format(state.global_distance()))

hc = CO2(state)

print('Initial value: {}'.format(hc.value(state)))
print()

final = search.hill_climbing(hc)

print()
print('Final global distance: {}'.format(final.global_distance()))
print('Final value: {}'.format(hc.value(final)))

print()
print("Final state:")
print(final)