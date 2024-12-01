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
        # Start at the edges
        if direction == "north":
            self.position = 0.5  # Start at top
        elif direction == "south":
            self.position = -0.5  # Start at bottom
        elif direction == "east":
            self.position = 0.5  # Start at right
        else:  # west
            self.position = -0.5  # Start at left
        self.speed = 0.01

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
                if direction in ["north", "south"]:
                    if abs(abs(last_vehicle.position) - 0.5) > 0.1:
                        vehicle = Vehicle(id_counter, direction)
                        self.vehicles[direction].append(vehicle)
                        id_counter += 1
                else:  # east, west
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
                if abs(vehicle.position) <= 0.05:  # Remove vehicles that reach intersection
                    vehicles.remove(vehicle)
                    continue
                    
                # Stop at red light near intersection
                if not can_move and abs(vehicle.position) < 0.15:
                    continue
                    
                # Move vehicle towards intersection (0,0)
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
    
    # Draw roads
    ax.axhline(y=0, color='black', linewidth=2)  # Horizontal road
    ax.axvline(x=0, color='black', linewidth=2)  # Vertical road
    
    # Draw traffic lights near intersection
    ns_color = {"green": "green", "yellow": "yellow", "red": "red"}[sim.traffic_light.states["NS"]]
    ew_color = {"green": "green", "yellow": "yellow", "red": "red"}[sim.traffic_light.states["EW"]]
    
    # Traffic lights closer to intersection
    light_offset = 0.12  # Distance from center
    
    # Draw traffic light boxes (black rectangles)
    ax.add_patch(plt.Rectangle((-0.02, light_offset-0.02), 0.04, 0.04, color='black'))  # North
    ax.add_patch(plt.Rectangle((-0.02, -light_offset-0.02), 0.04, 0.04, color='black'))  # South
    ax.add_patch(plt.Rectangle((light_offset-0.02, -0.02), 0.04, 0.04, color='black'))  # East
    ax.add_patch(plt.Rectangle((-light_offset-0.02, -0.02), 0.04, 0.04, color='black'))  # West
    
    # Draw traffic light colors
    ax.plot(0, light_offset, marker='o', color=ns_color, markersize=6)  # North
    ax.plot(0, -light_offset, marker='o', color=ns_color, markersize=6)  # South
    ax.plot(light_offset, 0, marker='o', color=ew_color, markersize=6)  # East
    ax.plot(-light_offset, 0, marker='o', color=ew_color, markersize=6)  # West
    
    # Draw vehicles
    for direction, vehicles in sim.vehicles.items():
        for vehicle in vehicles:
            if direction in ["north", "south"]:
                ax.plot(0, vehicle.position, 'bo', markersize=8)
            else:  # east, west
                ax.plot(vehicle.position, 0, 'bo', markersize=8)
    
    ax.set_xlim(-0.6, 0.6)
    ax.set_ylim(-0.6, 0.6)
    ax.set_title(f"Traffic Flow Simulation\nTime: {sim.env.now:.1f}s")
    ax.grid(True)
    ax.set_aspect('equal')

def main():
    # Create simulation
    sim = TrafficSimulation()
    
    # Set up the animation
    fig, ax = plt.subplots(figsize=(8, 8))
    ani = FuncAnimation(
        fig,
        animate,
        fargs=(sim, ax),
        interval=50,  # 50ms between frames
        frames=None,  # Run indefinitely
        repeat=False
    )
    
    plt.show()

if __name__ == "__main__":
    main()