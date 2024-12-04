# Traffic Intersection Simulation

A Python-based traffic intersection simulation that models and visualizes vehicle flow through a 4-way intersection with traffic lights.

## Features

- Real-time visualization of traffic flow
- Configurable parameters for traffic patterns
- Multiple lane support
- Right turn capabilities
- Traffic light system with timing cycles
- Vehicle statistics tracking
- Different vehicle types (regular cars and longer vehicles)
- Decorative elements (trees and buildings)

## Requirements

- Python 3.x
- SimPy
- Matplotlib
- NumPy

## Installation

1. Clone this repository
2. Install required packages:

A Python-based traffic intersection simulation that models and visualizes vehicle flow through a 4-way intersection with traffic lights.

## Features

- Real-time visualization of traffic flow
- Configurable parameters for traffic patterns
- Multiple lane support
- Right turn capabilities
- Traffic light system with timing cycles
- Vehicle statistics tracking
- Different vehicle types (regular cars and longer vehicles)
- Decorative elements (trees and buildings)

## Requirements

- Python 3.x
- SimPy
- Matplotlib
- NumPy

## Installation

1. Clone this repository
2. Install required packages:

```
bash

pip install -r requirements.txt
```


## Configuration

The simulation can be customized through various parameters at the top of main.py:

- `NUM_LANES`: Number of lanes in each direction (default: 2)
- `GREEN_DURATION`: Duration of green light (default: 10 seconds)
- `YELLOW_DURATION`: Duration of yellow light (default: 2 seconds)
- `TRAFFIC_VOLUME`: Average number of cars per minute (default: 66)
- `AVERAGE_SPEED`: Vehicle speed in mph (default: 55)
- `TURN_PROBABILITY`: Probability of right turns (default: 0.3)

## Usage

Run the simulation:

```
bash

python main.py
```


## Visualization Features

### Traffic Display
- Gray roads with white lane markings
- Color-coded vehicles:
  - Blue: Regular vehicles
  - Purple: Longer vehicles (e.g., trucks)
  - Red: Vehicles making right turns
- Traffic lights at intersection points
- Decorative trees and buildings in corners

### Statistics Panel
- Real-time simulation clock
- Per-direction statistics:
  - Current vehicle volume
  - Number of vehicles waiting at lights
  - Average wait time
  - Total completed vehicles

## How It Works

The simulation uses SimPy for event-driven simulation and Matplotlib for visualization. Key components:

1. **Vehicle Generation**: Vehicles are generated based on traffic volume settings and lane availability.

2. **Traffic Light System**: Cycles between green, yellow, and red states for north-south and east-west directions.

3. **Vehicle Movement**: 
   - Vehicles follow lane rules
   - Maintain safe following distances
   - React to traffic lights
   - Support right turns on red
   - Variable speeds around the average

4. **Statistics Tracking**:
   - Monitors wait times
   - Tracks completed vehicles
   - Calculates average delays
   - Updates in real-time

## License

MIT License