import random

import comms
from object_types import ObjectTypes

import sys
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
        self.enemy_tank_id = tank_id_message["message"]["enemy-tank-id"]

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

        

        self.our_tank_pos_x, self.our_tank_pos_y = self.objects[self.tank_id]["position"][0], self.objects[self.tank_id]["position"][1]
        self.enemy_pos_x, self.enemy_pos_y = self.objects[self.enemy_tank_id]["position"][0], self.objects[self.enemy_tank_id]["position"][1]
        # print(self.objects, file=sys.stderr)
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
        
        # our_next_pos_x, our_next_pos_y = self.width //2, self.height // 2
        c = True # this means we are trying to dodge something

        try:        
            our_tank = self.current_turn_message["message"]["updated_objects"][self.tank_id]
            self.our_tank_pos_x = our_tank["position"][0]
            self.our_tank_pos_y = our_tank["position"][1]
        except:
            our_next_pos_x, our_tank_pos_y = self.our_tank_pos_x, self.our_tank_pos_y
            self.our_tank_pos_x, self.our_tank_pos_y = our_next_pos_x, our_tank_pos_y
            c = False
            pass

        # top left, bottom_left, bottom_right, top_right
        border_pos = self.current_turn_message["message"]["updated_objects"]["closing_boundary-1"]["position"]

        # this is our boundary
        x_boundary = [self.our_tank_pos_x - 300, self.our_tank_pos_x + 300]
        y_boundary = [self.our_tank_pos_y - 300, self.our_tank_pos_y + 300]

        bullet_array = []
        # try:
        msg: dict = self.current_turn_message["message"]["updated_objects"]
        # for item in self.current_turn_message["message"]["updated_objects"]:
        for item in msg.values():
            # print(item, file=sys.stderr)
            # if "bullet" in item:
            if item["type"] == ObjectTypes.BULLET.value:
                bullet_pos_x = item["position"][0]
                bullet_pos_y = item["position"][1]

                if bullet_pos_x <= x_boundary[1] and bullet_pos_x >= x_boundary[0] and bullet_pos_y <= y_boundary[1] and bullet_pos_y >= y_boundary[0]:
                    bullet_velocity_x = item["velocity"][0]
                    bullet_velocity_y = item["velocity"][1]

                    # calculating the bullets next location
                    # assuming that the bullets velocity is units/s and each tick gives us 0.1s to calculate
                    # we can estimate that the bullets position for the next tick will be it's velocity * 0.25
                    bullet_next_pos = ["bullet", bullet_velocity_x * 0.25 + bullet_pos_x, bullet_velocity_y * 0.25 + bullet_pos_y]
                    # the velocity units dont match up with actual difference in position. so i just manually calculated dist travelled ~= 7.83
                    
                    # angle = math.atan(bullet_velocity_y / bullet_velocity_x)
                    # bullet_next_pos = ["bullet", 7.83 * math.cos(angle) + bullet_pos_x, 7.83 * math.sin(angle) + bullet_pos_y]
                    bullet_array.append(bullet_next_pos)

        bullet_array = bullet_array + self.wall



        # assuming we are trying to reach the enemy tank

        # self.path = self.current_turn_message["message"]["updated_objects"][self.enemy_tank_id]["position"]
        # self.enemy_pos_x, self.enemy_pos_y = self.path[0], self.path[1]

        try:    # if this fails its because our tank isnt moving 

            # our tank is moving approx 2.36 units per tick. manual calculation
            tangent = our_tank["velocity"][1] / our_tank["velocity"][0]
            our_next_pos_x = our_tank["velocity"][0] * 0.25 + self.our_tank_pos_x
            our_next_pos_y = our_tank["velocity"][1] * 0.25 + self.our_tank_pos_y
            tank_ang = math.atan(tangent)
            # our_next_pos_x = 2.36 * math.cos(tank_ang) + self.our_tank_pos_x
            # our_next_pos_y = 2.36 * math.sin(tank_ang) + self.our_tank_pos_y
        except:
            our_next_pos_x = self.our_tank_pos_x
            our_next_pos_y = self.our_tank_pos_y
            tangent = 1

        # checking if our next_pos collides with any of the bullets
        # ik this method is a bit cursed, but the grid isn't exactly a graph so... here it is
        bullet_radius = 5 # treating this like a rectangle because ive got no idea how to calculate if its a circle
        tank_rectangle = 10
        
        plus_minus = True   # this is to alternate between adding and minusing 45 degrees
        count = 8
        cond = True # this means we haven't been hit
        hit = True
        while hit and count != 0:
            for bullet in bullet_array:
                if bullet[0] == "bullet":
                    bullet_x = bullet[1]
                    bullet_y = bullet[2]
                    # checking for collison
                    if (bullet_x + 5 < our_next_pos_x + 10 
                        and bullet_x - 5 > our_next_pos_x - 10 
                        and bullet_y + 5 < our_next_pos_y + 10 
                        and bullet_y - 5 > our_next_pos_y - 10):
                        # if we are hit, perform heuristic search
                        # idk how else to do it, but this method seems pretty legit
                        # so i will just +- the velocity by 45 degrees and check if it is still hit
                        # using the net velocity from when ying calculated when just moving right which = 141.42
                        cond = False
                        if count != 0:  # if count = 0, means we've exhausted all our paths
                            if plus_minus == True:
                                tangent = math.atan(tangent) + math.pi/2
                                our_next_pos_x = 141.42 * math.cos(tangent) * 0.25 + self.our_tank_pos_x
                                our_next_pos_y = 141.42  * math.sin(tangent) * 0.25 + self.our_tank_pos_y

                                plus_minus = False
                                count -= 1
                            else:
                                tangent = math.atan(tangent) - math.pi/2
                                our_next_pos_x = 141.42  * math.cos(tangent) * 0.25 + self.our_tank_pos_x
                                our_next_pos_y = 141.42  * math.sin(tangent) * 0.25 + self.our_tank_pos_y

                                plus_minus = True
                                count -= 1
                        break
                        
                else:   # this is a wall despite variable being called bulllet, msg me if code is confusing
                    bullet_x = bullet[0]
                    bullet_y = bullet[1]
                    # checking for collison
                    if (bullet_x + 18 < our_next_pos_x + 10 
                        and bullet_x - 18 > our_next_pos_x - 10 
                        and bullet_y + 18 < our_next_pos_y + 10 
                        and bullet_y - 18 > our_next_pos_y - 10):
                        # if we are hit, perform heuristic search
                        # idk how else to do it, but this method seems pretty legit
                        # so i will just +- the velocity by 45 degrees and check if it is still hit
                        # using the net velocity from when ying calculated when just moving right which = 141.42
                        cond = False
                        if count != 0:  # if count = 0, means we've exhausted all our paths
                            if plus_minus == True:
                                tangent = math.atan(tangent) + math.pi/2
                                our_next_pos_x = 141.42 * math.cos(tangent) * 0.25 + self.our_tank_pos_x
                                our_next_pos_y = 141.42 * math.sin(tangent) * 0.25 + self.our_tank_pos_y

                                plus_minus = False
                                count -= 1
                            else:
                                tangent = math.atan(tangent) - math.pi/2
                                our_next_pos_x = 141.42 * math.cos(tangent) * 0.25 + self.our_tank_pos_x
                                our_next_pos_y = 141.42 * math.sin(tangent) * 0.25 + self.our_tank_pos_y

                                plus_minus = True
                                count -= 1
                        break

            if count == 0:
                # our_next_pos_x = our_tank["velocity"][0] * 0.1 + self.our_tank_pos_x
                # our_next_pos_y = our_tank["velocity"][1] * 0.1 + self.our_tank_pos_y
                our_next_pos_x = 141.42 * math.cos(tank_ang) * 0.25 + self.our_tank_pos_x
                our_next_pos_y = 141.42 * math.sin(tank_ang) * 0.25 + self.our_tank_pos_y
                c = False
                break   # break the while loop. u have no choice but to be hit so might as well go in the direction we want

            if cond or bullet == bullet_array[-1]:
                hit = False

        # except:
        #     our_next_pos_x, our_next_pos_y = self.enemy_pos_x, self.enemy_pos_y

        if c:
            self.path = [our_next_pos_x, our_next_pos_y]        
        else:     
            self.path = [self.width //2, self.height // 2]

        return True

    def respond_to_turn(self):
        """
        This is where you should write your bot code to process the data and respond to the game.
        """

        # Write your code here... For demonstration, this bot just shoots randomly every turn.

        comms.post_message({
            # "shoot": random.uniform(0, random.randint(1, 360))
            "path": self.path,
            "shoot": random.uniform(0, random.randint(1, 360))
        })
