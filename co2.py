import search
import random
from enum import Enum
import sys
from itertools import product
import copy

"""
user = {'id': 1, 'origin': [1, 2], 'destination': [2, 3]}

travel=[]
driver = {'user': user, 'travel': travel}

passenger = {'user':user, 'driver':user}
"""


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
        act, old_driver, old_passenger = action
        cstate = copy.deepcopy(state)

        driver = cstate.get_user(old_driver['id'])
        passenger =  cstate.get_user(old_passenger['id'])
        if act == 'add':
            driver.add_passenger(passenger)


        return cstate

    def value(self, state):
        # print(state.global_distance())
        return state.N * 30 - state.global_distance()

    def actions(self, state):
        actions = []
        for d, p in product(state.drivers, state.remaining_passengers):
            actions.append(['add',d,p])

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
        self.remaining_drivers = []
        self.remaining_passengers = []

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
        self.remaining_passengers = list(self.passengers)
        self.remaining_drivers = list(self.drivers)

    def get_user(self, pos):
        return self.users[pos]

    def is_final_state(self):
        return not self.remaining_passengers

    def global_distance(self):
        dist = 0
        counted_driver = []
        for d in self.actual_drivers:
            dist += d.distance()
            counted_driver.append(d)

        rd = [d for d in self.remaining_drivers if d not in counted_driver]
        for d in rd:
            dist += d.distance()
            counted_driver.append(d)

        for u in self.remaining_passengers:
            dist += manhattan_distance(u['origin'], u['destination'])

        return dist

    def generate_initial_random_solution(self):
        self.take_all_passengers_possible()
        self.take_empty_drivers_as_passenger()

    def take_all_passengers_possible(self):
        last_driver_idx = 0
        for driver in self.drivers:
            added_passengers = self.__take_passengers(driver)
            if added_passengers:
                self.actual_drivers.append(driver)
                self.remaining_drivers.remove(driver)
            self.remaining_passengers = [d for d in self.remaining_passengers if d not in added_passengers]
            if len(self.remaining_passengers) == 0:
                break
            last_driver_idx += 1
        self.remaining_drivers.insert(0,self.drivers[last_driver_idx]) # last driver may still have room
        return last_driver_idx

    def __take_passengers(self, driver):
        added_passengers = []
        for p in self.remaining_passengers:
            added = driver.add_passenger(p)
            if added:
                added_passengers.append(p)
        return added_passengers

    def take_empty_drivers_as_passenger(self):
        if len(self.remaining_drivers) < 2:
            return
        tried_driver = []
        passenger_candidates = [d for d in self.remaining_drivers[1:] if d not in self.actual_drivers]
        driver = self.remaining_drivers.pop()
        while passenger_candidates and driver not in tried_driver:
            tried_driver.append(driver)
            added_drivers_as_passengers = self.__take_drivers_as_passenger(driver, passenger_candidates)
            if added_drivers_as_passengers:
                self.remaining_drivers = [d for d in self.remaining_drivers if d not in added_drivers_as_passengers]
                if driver not in self.actual_drivers:
                    self.actual_drivers.append(driver)  # driver may drive on his own
            else:
                self.remaining_drivers.append(driver)  # may go as a passenger of another driver

            if len(self.remaining_drivers) > 1:
                passenger_candidates = [d for d in self.remaining_drivers[1:] if d not in self.actual_drivers]
                driver = self.remaining_drivers.pop(0)
            else:
                passenger_candidates = []

        # drivers going on their own
        self.actual_drivers.extend(self.remaining_drivers)
        print('drivers on their own {}'.format([d.user for d in self.remaining_drivers]))
        self.remaining_drivers = []

    def __take_drivers_as_passenger(self, driver, remaining_drivers):
        added_passengers = []
        for p in remaining_drivers:
            added = driver.add_passenger(p.user, mandatory=False) # take driver as passenger only if dist is reduced
            if added:
                added_passengers.append(p)
        return added_passengers

    def swap_passengers(self, driver1, driver2):
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

    def best_swap(self):
        print("SSSSSSSSSSSSSSSWWWWWWWWWWAAAAAAAAAAAPPPPPPPPPPIIIIIIIIIIIINNNNNNNNGGGGGGG")
        max_saved_distance = {'dist': 0, 'drivers': [], 'passengers': []}
        pairs_of_drivers = [[d1, d2] for d1, d2 in product(self.actual_drivers, repeat=2) if d1 != d2]
        for d1, d2 in pairs_of_drivers:
            old_distance = d1.distance() + d2.distance()
            cd1 = copy.deepcopy(d1)
            cd2 = copy.deepcopy(d2)
            passengers = self.swap_passengers(cd1, cd2)
            if passengers:
                saved_distance = old_distance - (cd1.distance() + cd2.distance())
                if saved_distance > max_saved_distance['dist']:
                    max_saved_distance['dist'] = saved_distance
                    max_saved_distance['drivers'] = [d1,d2]
                    max_saved_distance['passengers'] = passengers

        if max_saved_distance['dist'] > 0:
            passengers = self.swap_passengers(max_saved_distance['drivers'][0], max_saved_distance['drivers'][1])
            return [max_saved_distance['drivers'], max_saved_distance['passengers']]
        return []

    def add_best_passenger(self, alow_worsen=False):
        print("AAAAAAAAAAAAAAAAADDDDDDDDDDDDDDDIIIIIIIIIIIIIIINNNNNNNNNNNNNNNNNGGGGGGGGGGGG")
        max_saved_distance = {'dist': -300, 'driver': None, 'passenger': None}
        for d, p in product(self.drivers, self.remaining_passengers):
            old_distance = d.distance() + manhattan_distance(p['origin'], p['destination'])
            cd = copy.deepcopy(d)
            added = cd.add_passenger(p)
            if added:
                saved_distance = old_distance - cd.distance()
                if saved_distance > max_saved_distance['dist']:
                    max_saved_distance['dist'] = saved_distance
                    max_saved_distance['driver'] = d
                    max_saved_distance['passenger'] = p
        if alow_worsen or max_saved_distance['dist'] > 0:
            max_saved_distance['driver'].add_passenger(max_saved_distance['passenger'])
            if max_saved_distance['driver'] not in self.actual_drivers:
                self.actual_drivers.append(max_saved_distance['driver'])
                self.remaining_drivers.remove(max_saved_distance['driver'])
            self.remaining_passengers.remove(max_saved_distance['passenger'])
            return True
        return False

    def add_best_driver_as_passenger(self):
        passenger_candidates = list(self.remaining_drivers)
        max_saved_distance = {'dist': 0, 'driver': None, 'passenger': None}
        for p in passenger_candidates:
            drivers = [d for d in self.drivers if d is not p]
            for d in drivers:
                old_distance = d.distance() + p.distance()
                cd = copy.deepcopy(d)
                added = cd.add_passenger(p.user, mandatory=False)
                if added:
                    saved_distance = old_distance - cd.distance()
                    if saved_distance > max_saved_distance['dist']:
                        max_saved_distance['dist'] = saved_distance
                        max_saved_distance['driver'] = d
                        max_saved_distance['passenger'] = p
        if max_saved_distance['dist'] > 0:
            max_saved_distance['driver'].add_passenger(max_saved_distance['passenger'].user, mandatory=False)
            if max_saved_distance['driver'] not in self.actual_drivers:
                self.actual_drivers.append(max_saved_distance['driver'])
                if max_saved_distance['driver'] in self.remaining_drivers:
                    self.remaining_drivers.remove(max_saved_distance['driver'])
            self.remaining_drivers.remove(max_saved_distance['passenger'])
            return True
        return False

    # bad passenger: one that worsen the overall distance
    # def take_bad_passengers(self):



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
    def add_passenger_aux(self, passenger):
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

    # taking a driver as a passenger may not be worth if increments traveled distance
    def add_passenger(self, passenger, mandatory=True):
        if mandatory:
            added = self.add_passenger_aux(passenger)
            return added
        else:
            dist_old = self.distance() + manhattan_distance(passenger['origin'], passenger['destination'])
            driver = copy.deepcopy(self)
            added = driver.add_passenger_aux(passenger)
            dist_new = driver.distance()
            if dist_old > dist_new and added:
                self.add_passenger_aux(passenger)
                return True
            return False


    def add_passenger_in_pos(self, passenger, pos_take, pos_drop):
        # insert first the take operation ant then the pop one
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


# state = State(n=10, m=1)
# state.generate_random_problem()
# state.generate_initial_random_solution()
# print(state.remaining_passengers)
# print(state.remaining_drivers)
# print([d.user['id'] for d in state.actual_drivers])
# for d in state.actual_drivers:
#     print(d.travel)

# print("user: " + str(state.users[0]))
# print("user: " + str(state.users[1]))
# print("user: " + str(state.users[2]))
# print("user: " + str(state.users[3]))
# driver = Driver(state.users[0])
# driver.add_passenger(state.users[1])
# driver.add_passenger(state.users[2])
# print(driver.travel)
# driver.add_passenger(state.users[3])
# print(driver.travel)
# print(driver.distance())

# print()
# print()

state = State(n=100, m=50)
state.generate_random_problem()

# print(state.global_distance())
# state.add_best_passenger()
# print(state.global_distance())
#

# state.generate_initial_random_solution()

# print(state.is_final_state())
# print(state.global_distance())
#
# co2 = CO2(state)
#
# final = search.hill_climbing(co2)
#
# print(final.is_final_state())
# print(final.global_distance())



print("global distance: ")
print(state.global_distance())
cont = True
old_dist = state.global_distance()
while state.remaining_passengers:
    #state.best_swap()
    print('add passenger')
    print(state.add_best_passenger(alow_worsen=True))
    dist = state.global_distance()
    cont = old_dist > dist
    old_dist = dist
    print("global distance: ")
    print(dist)
    if not cont:
        print("hhhhhhhhhheeeeeeeeyyyyyyy")

cont = True
while len(state.remaining_drivers) > 1 and cont:
    print('add driver')
    state.add_best_driver_as_passenger()
    dist = state.global_distance()
    cont = old_dist > dist
    old_dist = dist
    print("global distance: ")
    print(dist)

cont = True
while cont:
    print('swap')
    state.best_swap()
    dist = state.global_distance()
    cont = old_dist > dist
    old_dist = dist
    print("global distance: ")
    print(dist)


"""
print(state.drivers[0].travel)
print(state.drivers[1].travel)
sw = state.swap_passengers(state.drivers[0], state.drivers[1])
if sw:
    print("Swapped -----")
    print(state.drivers[0].travel)
    print(state.drivers[1].travel)

"""

"""print(random.choices(range(34),k=2))

for i in range(10):
    my_randoms=[random.randrange(100) for _ in range (2)]
    print(my_randoms)

sequence = range(30)
users = []
for i in range(10):
    user = {}
    user['id'] = i
    user['origin'] = random.choices(sequence,k=2)
    user['destination'] = random.choices(sequence,k=2)
    print(user)
    users.append(user)

print(users)
"""