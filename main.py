import simpy
import random
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import defaultdict

class Vehicle:
    def __init__(self, id: int, direction: str):
        self.id = id
        self.direction = direction
        self.lane_offset = 0.02  # Offset for passing
        
        # Set initial position and offset based on direction
        if direction == "north":
            self.position = 0.5  # Start at top
            self.x = self.lane_offset  # Slightly right lane
        elif direction == "south":
            self.position = -0.5  # Start at bottom
            self.x = -self.lane_offset  # Slightly left lane
        elif direction == "east":
            self.position = 0.5  # Start at right
            self.y = self.lane_offset  # Slightly upper lane
        else:  # west
            self.position = -0.5  # Start at left
            self.y = -self.lane_offset  # Slightly lower lane
        
        self.speed = 0.01
        self.crossed_intersection = False
        self.completed = False

class TrafficLight:
    def __init__(self, env):
        self.env = env
        self.states = {"NS": "red", "EW": "green"}
        self.env.process(self.run())
    
    def run(self):
        while True:
            # EW green, NS red
            self.states = {"NS": "red", "EW": "green"}
            yield self.env.timeout(30)
            
            # EW yellow
            self.states["EW"] = "yellow"
            yield self.env.timeout(5)
            
            # NS green, EW red
            self.states = {"NS": "green", "EW": "red"}
            yield self.env.timeout(30)
            
            # NS yellow
            self.states["NS"] = "yellow"
            yield self.env.timeout(5)

class TrafficSimulation:
    def __init__(self):
        self.env = simpy.Environment()
        self.vehicles = {
            "north": [],
            "south": [],
            "east": [],
            "west": []
        }
        self.traffic_light = TrafficLight(self.env)
        
        # Start vehicle generators
        for direction in self.vehicles.keys():
            self.env.process(self.generate_vehicles(direction))
    
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
                if abs(abs(last_vehicle.position) - 0.5) > 0.1:
                    vehicle = Vehicle(id_counter, direction)
                    self.vehicles[direction].append(vehicle)
                    id_counter += 1
            
            # Random interval between vehicles
            yield self.env.timeout(random.expovariate(0.1))
    
    def update(self):
        # Move vehicles based on traffic light state
        for direction, vehicles in self.vehicles.items():
            if not vehicles:
                continue
                
            light_group = "NS" if direction in ["north", "south"] else "EW"
            can_move = self.traffic_light.states[light_group] != "red"
            
            # Update each vehicle
            for vehicle in vehicles[:]:
                # Remove completed vehicles
                if abs(vehicle.position) >= 0.5 and vehicle.crossed_intersection:
                    vehicles.remove(vehicle)
                    continue
                
                # Handle intersection crossing
                if abs(vehicle.position) <= 0.05 and not vehicle.crossed_intersection:
                    if can_move:
                        vehicle.crossed_intersection = True
                        # Continue in same direction but opposite side
                        vehicle.position = -0.05 if vehicle.position > 0 else 0.05
                    continue
                
                # Stop at red light near intersection
                if not vehicle.crossed_intersection and not can_move and abs(vehicle.position) < 0.15:
                    continue
                
                # Move vehicle
                if direction == "north":
                    vehicle.position -= vehicle.speed
                elif direction == "south":
                    vehicle.position += vehicle.speed
                elif direction == "east":
                    vehicle.position -= vehicle.speed
                elif direction == "west":
                    vehicle.position += vehicle.speed
        
        self.env.step()

def animate(frame_num, sim, ax):
    sim.update()
    ax.clear()
    
    # Draw roads with lane markings
    road_width = 0.04
    # Horizontal road
    ax.add_patch(plt.Rectangle((-0.6, -road_width), 1.2, 2*road_width, color='gray'))
    # Vertical road
    ax.add_patch(plt.Rectangle((-road_width, -0.6), 2*road_width, 1.2, color='gray'))
    
    # Draw lane markers
    marker_style = dict(color='white', linestyle='--', linewidth=1)
    ax.axhline(y=0, **marker_style)  # Horizontal center line
    ax.axvline(x=0, **marker_style)  # Vertical center line
    
    # Draw traffic lights
    ns_color = {"green": "green", "yellow": "yellow", "red": "red"}[sim.traffic_light.states["NS"]]
    ew_color = {"green": "green", "yellow": "yellow", "red": "red"}[sim.traffic_light.states["EW"]]
    
    # Reduced light offset for more inner placement
    light_offset = 0.06  # Reduced from 0.12
    
    # Traffic light boxes
    ax.add_patch(plt.Rectangle((-0.01, light_offset-0.01), 0.02, 0.02, color='black'))  # North
    ax.add_patch(plt.Rectangle((-0.01, -light_offset-0.01), 0.02, 0.02, color='black'))  # South
    ax.add_patch(plt.Rectangle((light_offset-0.01, -0.01), 0.02, 0.02, color='black'))  # East
    ax.add_patch(plt.Rectangle((-light_offset-0.01, -0.01), 0.02, 0.02, color='black'))  # West
    
    # Traffic light colors - smaller markers for more compact appearance
    ax.plot(0, light_offset, marker='o', color=ns_color, markersize=4)  # North
    ax.plot(0, -light_offset, marker='o', color=ns_color, markersize=4)  # South
    ax.plot(light_offset, 0, marker='o', color=ew_color, markersize=4)  # East
    ax.plot(-light_offset, 0, marker='o', color=ew_color, markersize=4)  # West
    
    # Draw vehicles with offset lanes
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
    ax.set_title(f"Traffic Flow Simulation\nTime: {sim.env.now:.1f}s")
    ax.grid(True)
    ax.set_aspect('equal')

def main():
    sim = TrafficSimulation()
    fig, ax = plt.subplots(figsize=(8, 8))
    ani = FuncAnimation(
        fig,
        animate,
        fargs=(sim, ax),
        interval=50,
        frames=None,
        repeat=False
    )
    
    plt.show()

if __name__ == "__main__":
    main()