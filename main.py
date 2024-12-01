import simpy
import random
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import defaultdict, deque

NUM_LANES = 2
GREEN_DURATION = 30  # ✅
YELLOW_DURATION = 5  # ✅
OBSERVATION_ZONE_LENGTH = 0.5 # ✅
AVERAGE_SPEED = 30 # ✅
AVERAGE_ARRIVAL_RATE = 0.5  # ✅
TRAFFIC_VOLUME = 10 # Average cars per observation zone per minute
MINIMUM_FOLLOW_DISTANCE = 0.05

class Vehicle:
    def __init__(self, id: int, direction: str):
        self.id = id
        self.direction = direction
        self.lane_offset = 0.02  # Offset for passing
        self.wait_start = None
        
        # Set initial position and offset based on direction
        if direction == "north":
            self.position = OBSERVATION_ZONE_LENGTH  # Start at top
            self.x = self.lane_offset  # Slightly right lane
        elif direction == "south":
            self.position = -OBSERVATION_ZONE_LENGTH  # Start at bottom
            self.x = -self.lane_offset  # Slightly left lane
        elif direction == "east":
            self.position = OBSERVATION_ZONE_LENGTH  # Start at right
            self.y = self.lane_offset  # Slightly upper lane
        else:  # west
            self.position = -OBSERVATION_ZONE_LENGTH  # Start at left
            self.y = -self.lane_offset  # Slightly lower lane
        
        self.speed = 0.01
        self.crossed_intersection = False
        self.completed = False

class TrafficStats:
    def __init__(self):
        self.completed_count = 0
        self.wait_times = deque(maxlen=50)  # Rolling window of recent wait times
        self.waiting_count = 0

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
        self.vehicles = {
            "north": [],
            "south": [],
            "east": [],
            "west": []
        }
        self.stats = {
            "north": TrafficStats(),
            "south": TrafficStats(),
            "east": TrafficStats(),
            "west": TrafficStats()
        }
        self.traffic_light = TrafficLight(self.env)
        
        # Start vehicle generators
        for direction in self.vehicles.keys():
            self.env.process(self.generate_vehicles(direction))

    def update_stats(self):
        # Update waiting counts
        for direction, vehicles in self.vehicles.items():
            stats = self.stats[direction]
            stats.waiting_count = sum(1 for v in vehicles 
                                    if not v.crossed_intersection 
                                    and abs(v.position) < MINIMUM_FOLLOW_DISTANCE)

    def generate_vehicles(self, direction):
        id_counter = 0
        while True:
            # Add new vehicle if there's space
            if not self.vehicles[direction]:
                vehicle = Vehicle(id_counter, direction)
                self.vehicles[direction].append(vehicle)
                id_counter += 1
            else:
                # Check if there's enough space from the last vehicle
                last_vehicle = self.vehicles[direction][-1]
                if abs(abs(last_vehicle.position) - OBSERVATION_ZONE_LENGTH) > MINIMUM_FOLLOW_DISTANCE:
                    vehicle = Vehicle(id_counter, direction)
                    self.vehicles[direction].append(vehicle)
                    id_counter += 1
            
            # Random interval between vehicles based on average arrival rate
            yield self.env.timeout(random.expovariate(AVERAGE_ARRIVAL_RATE))
    
    def update(self):
        # Move vehicles based on traffic light state
        # Convert speed from mph to miles per timestep
        base_movement = AVERAGE_SPEED / 3600  # Convert from miles/hour to miles/second
        
        for direction, vehicles in self.vehicles.items():
            if not vehicles:
                continue
                
            light_group = "NS" if direction in ["north", "south"] else "EW"
            can_move = self.traffic_light.states[light_group] != "red" and self.traffic_light.states[light_group] != "yellow"
            
            # Update each vehicle
            for i, vehicle in enumerate(vehicles[:]):
                # Vary movement speed randomly around average
                movement_per_step = base_movement * (0.8 + 0.4 * random.random())  # Varies from 80% to 120% of average
                
                # Start wait time tracking
                if not can_move and not vehicle.crossed_intersection and abs(vehicle.position) < MINIMUM_FOLLOW_DISTANCE:
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
                if abs(vehicle.position) <= 0.1 and not vehicle.crossed_intersection:
                    if can_move:
                        vehicle.crossed_intersection = True
                    if vehicle.wait_start is not None:
                        vehicle.wait_start = None
                    if not can_move:
                        continue
                
                # Check for vehicle ahead
                if i > 0:
                    vehicle_ahead = vehicles[i-1]
                    if abs(abs(vehicle.position) - abs(vehicle_ahead.position)) < MINIMUM_FOLLOW_DISTANCE:
                        continue
                
                # Stop at red light near intersection
                if not vehicle.crossed_intersection and not can_move and abs(vehicle.position) < 0.1:
                    continue
                
                # Move vehicle using varied speed
                if direction == "north":
                    vehicle.position -= movement_per_step
                elif direction == "south":
                    vehicle.position += movement_per_step
                elif direction == "east":
                    vehicle.position -= movement_per_step
                elif direction == "west":
                    vehicle.position += movement_per_step
        
        self.update_stats()
        self.env.step()

def animate(frame_num, sim, ax, stats_ax):
    sim.update()
    ax.clear()
    stats_ax.clear()
    
    # Draw roads with lane markings
    road_width = 0.04
    ax.add_patch(plt.Rectangle((-0.6, -road_width), 1.2, 2*road_width, color='gray'))
    ax.add_patch(plt.Rectangle((-road_width, -0.6), 2*road_width, 1.2, color='gray'))
    
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
    
    # Draw vehicles
    for direction, vehicles in sim.vehicles.items():
        for vehicle in vehicles:
            if direction == "north":
                ax.plot(vehicle.lane_offset, vehicle.position, 'bo', markersize=8)
            elif direction == "south":
                ax.plot(-vehicle.lane_offset, vehicle.position, 'bo', markersize=8)
            elif direction == "east":
                ax.plot(vehicle.position, vehicle.lane_offset, 'bo', markersize=8)
            else:  # west
                ax.plot(vehicle.position, -vehicle.lane_offset, 'bo', markersize=8)
    
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
        avg_wait = np.mean(stats.wait_times) if stats.wait_times else 0
        
        text = (
            f"{direction}:\n"
            f"  Current Volume: {len(sim.vehicles[dir_lower])}\n"
            f"  Waiting at Light: {stats.waiting_count}\n"
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

# @todo set global variables