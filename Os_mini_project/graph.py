import matplotlib.pyplot as plt

def show_graph(fifo_faults, lru_faults, optimal_faults):
    algorithms = ['FIFO', 'LRU', 'Optimal']
    faults = [fifo_faults, lru_faults, optimal_faults]

    plt.bar(algorithms, faults)
    plt.title("Page Replacement Algorithm Comparison")
    plt.xlabel("Algorithm")
    plt.ylabel("Page Faults")
    plt.show()