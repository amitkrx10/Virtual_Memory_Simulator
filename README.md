# VirtualMemorySimulator

**Virtual Memory Management Simulator with Page Replacement Visualization**

---

## **Description**

This project simulates **Virtual Memory Management** in Operating Systems.  
It demonstrates **page replacement algorithms** including:

- FIFO (First-In-First-Out)  
- LRU (Least Recently Used)  
- Optimal Page Replacement  

The simulator calculates **page faults**, **hits**, and **hit ratio** for a given page reference string, and provides a **graphical comparison** of the algorithms.

---

## **Features**

- Interactive **terminal-based input** for:
  - Number of memory frames
  - Page reference string
- Choice of **algorithm to simulate**:
  - FIFO, LRU, Optimal, or Compare All
- **Graphical visualization** of page faults for all algorithms
- **Belady’s Anomaly test** to demonstrate FIFO anomaly
- Works on **local Python environment** or **Google Cloud Shell**

---

## **How to Run**

1. Clone the repository:

```bash
git clone https://github.com/<your-username>/VirtualMemorySimulator.git
cd VirtualMemorySimulator

Install dependencies:

pip3 install --user matplotlib

Run the simulator:

python3 main.py

Follow the prompts to:

Enter number of frames

Enter page reference string

Choose an algorithm from the menu

If you choose the “Compare All” option, a graph image (graph.png) will be generated showing the page faults for each algorithm.

Files in the Project

main.py — Main program that runs the simulator

fifo.py — FIFO algorithm implementation

lru.py — LRU algorithm implementation

optimal.py — Optimal page replacement algorithm

utils.py — Utility functions used by algorithms

graph.py — Graph generation for algorithm comparison
