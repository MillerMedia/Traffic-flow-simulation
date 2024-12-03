import simpy
import random
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import defaultdict, deque

NUM_LANES = 1 # In each direction ✅
LANE_WIDTH = 0.04

GREEN_DURATION = 30
YELLOW_DURATION = 2
OBSERVATION_ZONE_LENGTH = 0.5 # @todo can we change the size of the map when adjusting this
AVERAGE_SPEED = 60

TRAFFIC_VOLUME = 25 # Average total number of cars at intersection per minute
AVERAGE_ARRIVAL_RATE = 60/TRAFFIC_VOLUME # per second arrival rate

CAR_LENGTH = 0.04
MINIMUM_FOLLOW_DISTANCE = 0.05 + (CAR_LENGTH/2)

TURN_PROBABILITY = 0.7  # 30% chance for right lane vehicles to turn right

class Vehicle:
    def __init__(self, id: int, direction: str, lane: int):
        self.id = id
        self.direction = direction
        self.lane = lane
        self.wait_start = None
        self.stop_count = 0
        self.is_waiting = False  # New flag to track if vehicle is currently stopped
        self.last_position = None  # To track if vehicle has moved
        
        # 95% chance of normal length, 5% chance of larger length
        if random.random() < 0.95:
            self.length = CAR_LENGTH  # Normal length
        else:
            self.length = CAR_LENGTH * 2  # 200% (like a semi truck or something)
        
        # Calculate lane offset based on lane number
        lane_offset = 0.02 + (lane * 0.04)
        
        # Set initial position and offset based on direction
        if direction == "north":
            self.position = OBSERVATION_ZONE_LENGTH  # Start at top
            self.x = -lane_offset  # Offset based on lane (right side)
        elif direction == "south":
            self.position = -OBSERVATION_ZONE_LENGTH  # Start at bottom
            self.x = lane_offset  # Offset based on lane (right side)
        elif direction == "east":
            self.position = OBSERVATION_ZONE_LENGTH  # Start at right
            self.y = lane_offset  # Offset based on lane (right side)
        else:  # west
            self.position = -OBSERVATION_ZONE_LENGTH  # Start at left
            self.y = -lane_offset  # Offset based on lane (right side)
        
        self.last_position = self.position  # Initialize last position
        self.speed = 0.01
        self.crossed_intersection = False
        self.completed = False
        
        # Determine if vehicle will turn right (only for right lane)
        self.turning_right = lane == NUM_LANES-1 and random.random() < TURN_PROBABILITY
        
        # Track turning progress
        self.turn_progress = 0  # 0 to 1 for turn animation

    def update_waiting_status(self, current_position):
        # Check if vehicle has moved by comparing positions
        MOVEMENT_THRESHOLD = 0.00001  # Small threshold
        has_moved = abs(current_position - self.last_position) > MOVEMENT_THRESHOLD
        
        # Update waiting status
        was_waiting = self.is_waiting
        self.is_waiting = not has_moved
        
        # Debug status change
        if was_waiting != self.is_waiting:
            print(f"Vehicle {self.id} waiting status changed from {was_waiting} to {self.is_waiting}")
            print(f"  Current pos: {current_position:.6f}, Last pos: {self.last_position:.6f}")
        
        self.last_position = current_position

class TrafficStats:
    def __init__(self):
        self.completed_count = 0
        self.wait_times = deque(maxlen=50)  # Rolling window of recent wait times
        self.waiting_count = 0
        self.current_waiting = {}  # Track currently waiting vehicles by ID

    def start_waiting(self, vehicle_id, time):
        if vehicle_id not in self.current_waiting:
            self.current_waiting[vehicle_id] = time

    def stop_waiting(self, vehicle_id, current_time):
        if vehicle_id in self.current_waiting:
            wait_time = current_time - self.current_waiting[vehicle_id]
            self.wait_times.append(wait_time)
            del self.current_waiting[vehicle_id]

class TrafficLight:
    def __init__(self, env):
        self.env = env
        self.states = {"NS": "red", "EW": "green"}
        self.env.process(self.run())
    
    def run(self):
        while True:
            # EW green, NS red
            self.states = {"NS": "red", "EW": "green"}
            yield self.env.timeout(GREEN_DURATION)
            
            # EW yellow
            self.states["EW"] = "yellow"
            yield self.env.timeout(YELLOW_DURATION)
            
            # NS green, EW red
            self.states = {"NS": "green", "EW": "red"}
            yield self.env.timeout(GREEN_DURATION)
            
            # NS yellow
            self.states["NS"] = "yellow"
            yield self.env.timeout(YELLOW_DURATION)

class TrafficSimulation:
    def __init__(self):
        self.env = simpy.Environment()
        # Initialize vehicles dict with lanes
        self.vehicles = {
            "north": [[] for _ in range(NUM_LANES)],
            "south": [[] for _ in range(NUM_LANES)],
            "east": [[] for _ in range(NUM_LANES)],
            "west": [[] for _ in range(NUM_LANES)]
        }
        self.stats = {
            "north": TrafficStats(),
            "south": TrafficStats(),
            "east": TrafficStats(),
            "west": TrafficStats()
        }
        self.traffic_light = TrafficLight(self.env)
        
        # Start vehicle generators for each lane in each direction
        for direction in self.vehicles.keys():
            for lane in range(NUM_LANES):
                self.env.process(self.generate_vehicles(direction, lane))

        # Initialize decorative elements
        self.decorations = self._init_decorations()

    def _init_decorations(self):
        building_colors = ['#A0522D', '#8B4513', '#6B4423', '#CD853F']  # Brown shades
        building_positions = {
            'ne_buildings': [(0.15 + (i * 0.12), 0.15) for i in range(4)],
            'sw_buildings': [(-0.15 - (i * 0.12), 0.05) for i in range(3)],
            'se_buildings': [(0.15 + (i * 0.12), 0.15) for i in range(3)]  # Adjusted to align the top of SE buildings
        }
        decorations = {
            'nw_trees': [(random.uniform(-0.45, -0.15), random.uniform(0.15, 0.45)) 
                        for _ in range(15)],
            'ne_buildings': [(0.15 + (i * 0.12), 0.15, 
                            random.uniform(0.08, 0.15), random.uniform(0.08, 0.15),
                            random.choice(building_colors)) 
                           for i in range(4)],
            'sw_buildings': [],
            'se_buildings': [],
            'se_trees': [(random.uniform(0.15, 0.45), random.uniform(-0.45, -0.15)) 
                        for _ in range(8)],
            'ne_trees': [(random.uniform(0.15, 0.45), random.uniform(0.15, 0.45)) 
                        for _ in range(12)],
            'sw_trees': [(random.uniform(-0.45, -0.15), random.uniform(-0.45, -0.15)) 
                        for _ in range(12)]
        }
        # Remove trees that overlap with buildings
        for tree_group in ['nw_trees', 'se_trees', 'ne_trees', 'sw_trees']:
            decorations[tree_group] = [tree for tree in decorations[tree_group] 
                                       if not any(abs(tree[0] - building[0]) < 0.15 and abs(tree[1] - building[1]) < 0.15 
                                                  for building_group, buildings in building_positions.items() 
                                                  for building in buildings)]
        return decorations

    def update_stats(self):
        # Update waiting counts for each direction
        for direction, lanes in self.vehicles.items():
            stats = self.stats[direction]
            waiting_count = 0
            
            # Define waiting zone parameters
            INTERSECTION_ZONE = 0.15  # Width of the intersection zone
            
            light_group = "NS" if direction in ["north", "south"] else "EW"
            is_red = self.traffic_light.states[light_group] == "red"
            
            for lane_idx, lane in enumerate(lanes):
                # Keep track of last waiting vehicle's position for each lane
                last_waiting_pos = None
                
                for vehicle in lane:
                    print(f"Checking {direction} vehicle {vehicle.id}:")
                    print(f"  Position: {vehicle.position:.4f}")
                    print(f"  Light is red: {is_red}")
                    
                    is_in_zone = abs(vehicle.position) <= INTERSECTION_ZONE
                    is_right_turner = vehicle.turning_right and lane_idx == NUM_LANES-1
                    
                    should_wait = False
                    
                    # Check if vehicle should be counted as waiting:
                    # 1. At red light in intersection zone
                    if is_in_zone and is_red and not is_right_turner and not vehicle.crossed_intersection:
                        should_wait = True
                        print(f"  Waiting at red light")
                    
                    # 2. Queued behind another waiting vehicle
                    elif last_waiting_pos is not None:
                        dist_to_prev = abs(abs(vehicle.position) - abs(last_waiting_pos))
                        min_spacing = MINIMUM_FOLLOW_DISTANCE + max(vehicle.length, CAR_LENGTH)/2
                        if dist_to_prev <= min_spacing:
                            should_wait = True
                            print(f"  Queued behind vehicle")
                    
                    if should_wait:
                        waiting_count += 1
                        last_waiting_pos = abs(vehicle.position)
                        print(f"  COUNTED AS WAITING")
            
            print(f"{direction.upper()} Total Waiting: {waiting_count}")
            stats.waiting_count = waiting_count

    def generate_vehicles(self, direction, lane):
        id_counter = 0
        while True:
            # Get total number of vehicles across all lanes in all directions
            num_vehicles = sum(sum(len(lane) for lane in lanes) for lanes in self.vehicles.values())
            
            # Only generate new vehicle if within 30% of target traffic volume
            if num_vehicles <= TRAFFIC_VOLUME * 1.3:
                # Add new vehicle if there's space
                if not self.vehicles[direction][lane]:
                    vehicle = Vehicle(id_counter, direction, lane)
                    self.vehicles[direction][lane].append(vehicle)
                    id_counter += 1
                else:
                    # Check if there's enough space from the last vehicle
                    last_vehicle = self.vehicles[direction][lane][-1]
                    if abs(abs(last_vehicle.position) - OBSERVATION_ZONE_LENGTH) > MINIMUM_FOLLOW_DISTANCE:
                        vehicle = Vehicle(id_counter, direction, lane)
                        self.vehicles[direction][lane].append(vehicle)
                        id_counter += 1
            
            # Random interval between vehicles based on average arrival rate
            yield self.env.timeout(random.expovariate(AVERAGE_ARRIVAL_RATE))
    
    def update(self):
        # Move vehicles based on traffic light state
        base_movement = AVERAGE_SPEED / 3600  # Convert from miles/hour to miles/second

        # Store initial positions for all vehicles
        for direction, lanes in self.vehicles.items():
            for lane in lanes:
                for vehicle in lane:
                    # Only initialize last_position if it hasn't been set
                    if vehicle.last_position is None:
                        vehicle.last_position = vehicle.position
                    else:
                        # Store current position before movement
                        old_pos = vehicle.position
        
        for direction, lanes in self.vehicles.items():
            light_group = "NS" if direction in ["north", "south"] else "EW"
            light_state = self.traffic_light.states[light_group]
            can_move = light_state not in ["red", "yellow"]
            
            for lane_idx, vehicles in enumerate(lanes):
                if not vehicles:
                    continue
                
                for i, vehicle in enumerate(vehicles[:]):
                    # Store current position to check if vehicle moves
                    initial_position = vehicle.position

                    # Vary movement speed randomly around average
                    movement_per_step = base_movement * (0.8 + 0.4 * random.random())
                    
                    # Check if this vehicle can proceed through intersection
                    allow_movement = can_move
                    
                    # Right turns can proceed on red if in rightmost lane
                    if vehicle.turning_right and lane_idx == NUM_LANES-1:
                        allow_movement = True
                    
                    # Start wait time tracking
                    if not allow_movement and not vehicle.crossed_intersection and abs(vehicle.position) < MINIMUM_FOLLOW_DISTANCE:
                        if vehicle.wait_start is None:
                            vehicle.wait_start = self.env.now

                    # Remove completed vehicles
                    if abs(vehicle.position) >= OBSERVATION_ZONE_LENGTH and vehicle.crossed_intersection:
                        if vehicle.wait_start is not None:
                            wait_time = self.env.now - vehicle.wait_start
                            self.stats[direction].wait_times.append(wait_time)
                        self.stats[direction].completed_count += 1
                        vehicles.remove(vehicle)
                        continue
                    
                    # Handle intersection crossing
                    if abs(vehicle.position) <= (0.1 * (NUM_LANES/2)) and not vehicle.crossed_intersection:
                        # Only allow crossing if:
                        # 1. Light is green OR
                        # 2. Vehicle is turning right in rightmost lane
                        if allow_movement:
                            vehicle.crossed_intersection = True
                            vehicle.wait_start = None
                        else:
                            continue
                    
                    # Check for vehicle ahead
                    if i > 0:
                        try:
                            vehicle_ahead = vehicles[i-1]
                            # Use the larger of the two vehicles' lengths for minimum following distance
                            min_follow = 0.05 + max(vehicle.length, vehicle_ahead.length)/2
                            within_following_distance = abs(vehicle.position - vehicle_ahead.position) >= min_follow

                            # Special case: if vehicle ahead is turning and has crossed, we can move
                            if vehicle_ahead.turning_right and vehicle_ahead.crossed_intersection:
                                within_following_distance = True
                            
                            if not within_following_distance:
                                continue
                                
                        except IndexError:
                            continue
                    
                    # Stop at red light near intersection
                    stop_position = 0.1 * (NUM_LANES/2) + CAR_LENGTH
                    if not vehicle.crossed_intersection and abs(vehicle.position) < stop_position:
                        if not allow_movement:
                            continue
                    
                    # Move vehicle using varied speed
                    if direction == "north":
                        if vehicle.turning_right and vehicle.crossed_intersection:
                            vehicle.x -= movement_per_step
                            vehicle.position = 0.02 + (lane_idx * 0.04)
                            if abs(vehicle.x) >= OBSERVATION_ZONE_LENGTH:
                                vehicles.remove(vehicle)
                        else:
                            vehicle.position -= movement_per_step
                    elif direction == "south":
                        if vehicle.turning_right and vehicle.crossed_intersection:
                            vehicle.x += movement_per_step
                            vehicle.position = -0.02 - (lane_idx * 0.04)
                            if abs(vehicle.x) >= OBSERVATION_ZONE_LENGTH:
                                vehicles.remove(vehicle)
                        else:
                            vehicle.position += movement_per_step
                    elif direction == "east":
                        if vehicle.turning_right and vehicle.crossed_intersection:
                            vehicle.y += movement_per_step
                            vehicle.position = 0.02 + (lane_idx * 0.04)
                            if abs(vehicle.y) >= OBSERVATION_ZONE_LENGTH:
                                vehicles.remove(vehicle)
                        else:
                            vehicle.position -= movement_per_step
                    elif direction == "west":
                        if vehicle.turning_right and vehicle.crossed_intersection:
                            vehicle.y -= movement_per_step
                            vehicle.position = -0.02 - (lane_idx * 0.04)
                            if abs(vehicle.y) >= OBSERVATION_ZONE_LENGTH:
                                vehicles.remove(vehicle)
                        else:
                            vehicle.position += movement_per_step
                    
                    # After all movement logic, update waiting status with the actual new position
                    vehicle.update_waiting_status(vehicle.position)
                    
                    # Update wait time tracking if near intersection
                    stop_position = 0.1 * (NUM_LANES/2) + CAR_LENGTH
                    is_at_intersection = abs(vehicle.position) <= stop_position
                    
                    if vehicle.is_waiting and not vehicle.crossed_intersection and is_at_intersection:
                        if vehicle.wait_start is None:
                            vehicle.wait_start = self.env.now
                            print(f"Starting wait for vehicle {vehicle.id} in {direction}")
                            self.stats[direction].start_waiting(vehicle.id, self.env.now)
                    else:
                        if vehicle.wait_start is not None:
                            print(f"Stopping wait for vehicle {vehicle.id} in {direction}")
                            self.stats[direction].stop_waiting(vehicle.id, self.env.now)
                            vehicle.wait_start = None
            
            self.update_stats()
            self.env.step()

def animate(frame_num, sim, ax, stats_ax):
    sim.update()
    ax.clear()
    stats_ax.clear()
    
    # Draw roads with lane markings
    total_road_width = LANE_WIDTH * NUM_LANES
    
    # Draw north-south road
    ax.add_patch(plt.Rectangle((-0.6, -total_road_width), 1.2, 2*total_road_width, color='gray'))
    
    # Draw east-west road
    ax.add_patch(plt.Rectangle((-total_road_width, -0.6), 2*total_road_width, 1.2, color='gray'))
    
    # Draw lane dividers for north-south lanes
    for i in range(1, NUM_LANES):
        offset = i * LANE_WIDTH
        # North lanes
        ax.axhline(y=offset, xmin=0.3, xmax=0.7, color='white', linestyle='-')
        # South lanes
        ax.axhline(y=-offset, xmin=0.3, xmax=0.7, color='white', linestyle='-')
    
    # Draw lane dividers for east-west lanes
    for i in range(1, NUM_LANES):
        offset = i * LANE_WIDTH
        # East lanes
        ax.axvline(x=offset, ymin=0.3, ymax=0.7, color='white', linestyle='-')
        # West lanes
        ax.axvline(x=-offset, ymin=0.3, ymax=0.7, color='white', linestyle='-')
    
    # Draw lane markers
    marker_style = dict(color='white', linestyle='--', linewidth=1)
    ax.axhline(y=0, **marker_style)
    ax.axvline(x=0, **marker_style)
    
    # Draw traffic lights
    ns_color = {"green": "green", "yellow": "yellow", "red": "red"}[sim.traffic_light.states["NS"]]
    ew_color = {"green": "green", "yellow": "yellow", "red": "red"}[sim.traffic_light.states["EW"]]
    
    light_offset = 0.02
    
    # Traffic light boxes
    ax.add_patch(plt.Rectangle((-0.01, light_offset-0.01), 0.02, 0.02, color='black'))
    ax.add_patch(plt.Rectangle((-0.01, -light_offset-0.01), 0.02, 0.02, color='black'))
    ax.add_patch(plt.Rectangle((light_offset-0.01, -0.01), 0.02, 0.02, color='black'))
    ax.add_patch(plt.Rectangle((-light_offset-0.01, -0.01), 0.02, 0.02, color='black'))
    
    # Traffic light colors
    ax.plot(0, light_offset, marker='o', color=ns_color, markersize=4)
    ax.plot(0, -light_offset, marker='o', color=ns_color, markersize=4)
    ax.plot(light_offset, 0, marker='o', color=ew_color, markersize=4)
    ax.plot(-light_offset, 0, marker='o', color=ew_color, markersize=4)
    
    # Add decorative elements in corners
    tree_green = '#228B22'
    
    # Trees in all corners
    for tree_group in ['nw_trees', 'se_trees', 'ne_trees', 'sw_trees']:
        for x, y in sim.decorations[tree_group]:
            ax.add_patch(plt.Circle((x, y), 0.02, color=tree_green))
    
    # Buildings
    for building_group in ['ne_buildings', 'sw_buildings', 'se_buildings']:
        for x, y, width, height, color in sim.decorations[building_group]:
            ax.add_patch(plt.Rectangle((x, y), width, height, color=color))

    # Draw vehicles
    for direction, lanes in sim.vehicles.items():
        for lane_idx, vehicles in enumerate(lanes):
            for vehicle in vehicles:
                # Determine color based on length and turning status
                if vehicle.turning_right:
                    color = 'red'  # Turning vehicles stay red
                else:
                    # Normal length vehicles are blue, longer vehicles are purple
                    color = 'blue' if vehicle.length == CAR_LENGTH else 'purple'
                
                # Create car shape using vehicle's specific length
                car_width = 0.02   # Width of car stays constant
                
                if direction in ["north", "south"]:
                    x = vehicle.x
                    y = vehicle.position
                    if vehicle.turning_right and vehicle.crossed_intersection:
                        # Draw horizontally for turned vehicles
                        rect = plt.Rectangle((x - vehicle.length/2, y - car_width/2),
                                          vehicle.length, car_width,
                                          color=color)
                    else:
                        # Draw vertically for straight vehicles
                        rect = plt.Rectangle((x - car_width/2, y - vehicle.length/2), 
                                          car_width, vehicle.length, 
                                          color=color)
                    ax.add_patch(rect)
                    
                else:  # east or west
                    x = vehicle.position
                    y = vehicle.y
                    if vehicle.turning_right and vehicle.crossed_intersection:
                        # Draw vertically for turned vehicles
                        rect = plt.Rectangle((x - car_width/2, y - vehicle.length/2),
                                          car_width, vehicle.length,
                                          color=color)
                    else:
                        # Draw horizontally for straight vehicles
                        rect = plt.Rectangle((x - vehicle.length/2, y - car_width/2),
                                          vehicle.length, car_width,
                                          color=color)
                    ax.add_patch(rect)
    
    ax.set_xlim(-0.6, 0.6)
    ax.set_ylim(-0.6, 0.6)
    ax.set_title("Traffic Flow Simulation")
    ax.grid(True)
    ax.set_aspect('equal')
    
    # Draw statistics
    stats_ax.axis('off')
    y_pos = 0.95
    stats_ax.text(0.5, 1.0, f"Time: {sim.env.now:.1f}s", ha='center', va='top')
    
    for direction in ["North", "South", "East", "West"]:
        dir_lower = direction.lower()
        stats = sim.stats[dir_lower]
        avg_wait = np.mean(list(stats.wait_times)) if stats.wait_times else 0
        current_waiting = stats.waiting_count  # Use the actual count
        
        text = (
            f"{direction}:\n"
            f"  Current Volume: {sum(len(lane) for lane in sim.vehicles[dir_lower])}\n"
            f"  Waiting at Light: {current_waiting}\n"
            f"  Avg Wait Time: {avg_wait:.1f}s\n"
            f"  Total Completed: {stats.completed_count}"
        )
        stats_ax.text(0.1, y_pos, text, va='top', fontsize=9)
        y_pos -= 0.25

def main():
    # Create figure with two subplots
    sim = TrafficSimulation()
    fig = plt.figure(figsize=(15, 8))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.5, 1])
    ax = fig.add_subplot(gs[0, 0])
    stats_ax = fig.add_subplot(gs[0, 1])
    
    ani = FuncAnimation(
        fig,
        animate,
        fargs=(sim, ax, stats_ax),
        interval=50,
        frames=None,
        repeat=False
    )
    
    plt.show()

if __name__ == "__main__":
    main()

# @todo fix edge case where blue after red car goes through intersection even on red light