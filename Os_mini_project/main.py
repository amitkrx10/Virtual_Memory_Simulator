from fifo import fifo
from lru import lru
from optimal import optimal
from graph import show_graph

def belady_test(pages):
    print("\n===== Belady's Anomaly Test (FIFO) =====")
    frames1 = int(input("Enter smaller frame size: "))
    frames2 = int(input("Enter larger frame size: "))

    faults1 = fifo(pages, frames1, show=False)
    faults2 = fifo(pages, frames2, show=False)

    print(f"\nFrames: {frames1}, Page Faults: {faults1}")
    print(f"Frames: {frames2}, Page Faults: {faults2}")

    if faults2 > faults1:
        print("Belady's Anomaly Detected!")
    else:
        print("No Belady's Anomaly.")

def compare_all(pages, capacity):
    fifo_faults = fifo(pages, capacity, show=False)
    lru_faults = lru(pages, capacity, show=False)
    optimal_faults = optimal(pages, capacity, show=False)

    print("\n===== Comparison Result =====")
    print(f"FIFO Page Faults    : {fifo_faults}")
    print(f"LRU Page Faults     : {lru_faults}")
    print(f"Optimal Page Faults : {optimal_faults}")

    show_graph(fifo_faults, lru_faults, optimal_faults)

def main():
    print("===== Virtual Memory Management Simulator (Modular Version) =====")

    pages = list(map(int, input("Enter page reference string (space separated): ").split()))
    capacity = int(input("Enter number of frames: "))

    while True:
        print("\n----------- MENU -----------")
        print("1. FIFO")
        print("2. LRU")
        print("3. Optimal")
        print("4. Compare All (Graph)")
        print("5. Belady's Anomaly Test")
        print("6. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            fifo(pages, capacity)
        elif choice == '2':
            lru(pages, capacity)
        elif choice == '3':
            optimal(pages, capacity)
        elif choice == '4':
            compare_all(pages, capacity)
        elif choice == '5':
            belady_test(pages)
        elif choice == '6':
            print("Exiting Program...")
            break
        else:
            print("Invalid choice!")

if __name__ == "__main__":
    main()