import simpy
import random
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import defaultdict
from threading import Thread

class Vehicle:
    def __init__(self, id: int, direction: str):
        self.id = id
        self.direction = direction
        self.position = 0.0
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
            if not self.vehicles[direction] or abs(self.vehicles[direction][-1].position) > 0.1:
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
                if abs(vehicle.position) >= 0.5:
                    vehicles.remove(vehicle)
                    continue
                    
                # Stop at red light near intersection
                if not can_move and abs(vehicle.position) > 0.4:
                    continue
                    
                # Move vehicle
                if direction in ["north", "east"]:
                    vehicle.position += vehicle.speed
                else:
                    vehicle.position -= vehicle.speed
        
        self.env.step()

def animate(frame_num, sim, ax):
    sim.update()
    ax.clear()
    
    # Draw roads
    ax.axhline(y=0, color='black', linewidth=2)  # Horizontal road
    ax.axvline(x=0, color='black', linewidth=2)  # Vertical road
    
    # Draw traffic lights
    ns_color = {"green": "green", "yellow": "yellow", "red": "red"}[sim.traffic_light.states["NS"]]
    ew_color = {"green": "green", "yellow": "yellow", "red": "red"}[sim.traffic_light.states["EW"]]
    
    ax.plot(0, 0.5, marker='o', color=ns_color, markersize=10)  # North light
    ax.plot(0, -0.5, marker='o', color=ns_color, markersize=10)  # South light
    ax.plot(0.5, 0, marker='o', color=ew_color, markersize=10)  # East light
    ax.plot(-0.5, 0, marker='o', color=ew_color, markersize=10)  # West light
    
    # Draw vehicles
    for direction, vehicles in sim.vehicles.items():
        for vehicle in vehicles:
            if direction == "north":
                ax.plot(0, vehicle.position, 'bo', markersize=8)
            elif direction == "south":
                ax.plot(0, vehicle.position, 'bo', markersize=8)
            elif direction == "east":
                ax.plot(vehicle.position, 0, 'bo', markersize=8)
            elif direction == "west":
                ax.plot(vehicle.position, 0, 'bo', markersize=8)
    
    ax.set_xlim(-0.6, 0.6)
    ax.set_ylim(-0.6, 0.6)
    ax.set_title(f"Traffic Flow Simulation\nTime: {sim.env.now:.1f}s")
    ax.grid(True)

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