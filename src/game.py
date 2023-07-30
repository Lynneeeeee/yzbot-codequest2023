import random

import comms
from object_types import ObjectTypes
import sys
import heapq
import math

class Game:
    """
    Stores all information about the game and manages the communication cycle.
    Available attributes after initialization will be:
    - tank_id: your tank id
    - objects: a dict of all objects on the map like {object-id: object-dict}.
    - width: the width of the map as a floating point number.
    - height: the height of the map as a floating point number.
    - current_turn_message: a copy of the message received this turn. It will be updated everytime `read_next_turn_data`
        is called and will be available to be used in `respond_to_turn` if needed.
    """
    def __init__(self):
        tank_id_message: dict = comms.read_message()
        self.tank_id = tank_id_message["message"]["your-tank-id"]
        self.enemy_id = tank_id_message["message"]["enemy-tank-id"]

        self.last_path =None

        self.current_turn_message = None

        # We will store all game objects here
        self.objects = {}

        next_init_message = comms.read_message()
        while next_init_message != comms.END_INIT_SIGNAL:
            # At this stage, there won't be any "events" in the message. So we only care about the object_info.
            object_info: dict = next_init_message["message"]["updated_objects"]

            # Store them in the objects dict
            self.objects.update(object_info)

            # Read the next message
            next_init_message = comms.read_message()

        # We are outside the loop, which means we must've received the END_INIT signal

        # Let's figure out the map size based on the given boundaries

        # Read all the objects and find the boundary objects
        self.wall = []
        boundaries = []
        for game_object in self.objects.values():
            if game_object["type"] == ObjectTypes.BOUNDARY.value:
                boundaries.append(game_object)
            # add wall positions
            if game_object["type"] == ObjectTypes.WALL.value:
                self.wall.append(game_object["position"])

        # The biggest X and the biggest Y among all Xs and Ys of boundaries must be the top right corner of the map.

        # Let's find them. This might seem complicated, but you will learn about its details in the tech workshop.
        biggest_x, biggest_y = [
            max([max(map(lambda single_position: single_position[i], boundary["position"])) for boundary in boundaries])
            for i in range(2)
        ]

        self.width = biggest_x
        self.height = biggest_y

        print(self.objects, file = sys.stderr)

    def read_next_turn_data(self):
        """
        It's our turn! Read what the game has sent us and update the game info.
        :returns True if the game continues, False if the end game signal is received and the bot should be terminated
        """
        # Read and save the message
        self.current_turn_message = comms.read_message()

        if self.current_turn_message == comms.END_SIGNAL:
            return False

        # Delete the objects that have been deleted
        # NOTE: You might want to do some additional logic here. For example check if a powerup you were moving towards
        # is already deleted, etc.
        for deleted_object_id in self.current_turn_message["message"]["deleted_objects"]:
            try:
                del self.objects[deleted_object_id]
            except KeyError:
                pass

        # Update your records of the new and updated objects in the game
        # NOTE: you might want to do some additional logic here. For example check if a new bullet has been shot or a
        # new powerup is now spawned, etc.
        self.objects.update(self.current_turn_message["message"]["updated_objects"])

        return True

    def respond_to_turn(self):
        """
        This is where you should write your bot code to process the data and respond to the game.
        """

        # Write your code here... For demonstration, this bot just shoots randomly every turn.

        all_objects_ids = self.objects.keys()
        print(all_objects_ids , file = sys.stderr)
        enemy_tank = self.objects[self.enemy_id]
        print(enemy_tank, file = sys.stderr)

        enemy_tank_pos = enemy_tank["position"]

        my_response = {}
        if self.last_path is None or self.last_path != enemy_tank_pos:
            my_response = {"path": enemy_tank_pos}
            self.last_path = enemy_tank_pos

        my_tank = self.objects[self.tank_id]
        my_tank_pos = my_tank["position"]

        distance = abs(my_tank_pos[0]- enemy_tank_pos[0]) + abs(my_tank_pos[1]- enemy_tank_pos[1])
        # if distance < 500:
        angle = math.atan2(enemy_tank_pos[1] - my_tank_pos[1], enemy_tank_pos[0] - my_tank_pos[0]) * 180 / math.pi
        # angle = (angle + 180) % 360
        my_response.update({"shoot": angle})

        # print(angle, file = sys.stderr)    
        comms.post_message(my_response)


# passable = set([(0, 0), (1, 0), (0, 1), (1, 1)]) 
# obstacles = set([(2, 2), (3, 3)]) 

# # move: up, down, left, right
# directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

# def heuristic(p1, p2):
#     return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

# def time_a_star(start, goal, avoid, speed):
#     open_list = [(0, start, 0)]  
#     came_from = {}  # store previous positions
#     g_score = {start: 0}  # store time of reach every position

#     while open_list:
#         current_time, current_pos, current_arrival_time = heapq.heappop(open_list)

#         if current_pos == goal:
#             # reach the goal position
#             path = [goal]
#             while current_pos in came_from:
#                 current_pos = came_from[current_pos]
#                 path.append(current_pos)
#             return path[::-1]
        
#         for dx, dy in directions:
#             next_pos = (current_pos[0] + dx, current_pos[1] + dy)

#             if next_pos in passable and next_pos not in avoid:
#                 # calculate time of reaching next position
#                 next_arrival_time = current_arrival_time + 1.0 / speed

#                 # if next position already visited
#                 if next_pos in g_score and next_arrival_time >= g_score[next_pos]:
#                     continue

#                 # update reach time & previous position
#                 g_score[next_pos] = next_arrival_time
#                 came_from[next_pos] = current_pos

#                 # calculate tims
#                 h = heuristic(next_pos, goal) / speed
#                 heapq.heappush(open_list, (next_arrival_time + h, next_pos, next_arrival_time))

#     # if didn't find any
#     return []
        
