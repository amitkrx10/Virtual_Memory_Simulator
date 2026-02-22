from utils import print_statistics

def lru(pages, capacity, show=True):
    frames = []
    page_faults = 0

    if show:
        print("\n===== LRU Page Replacement =====")

    for i in range(len(pages)):
        if pages[i] not in frames:
            if len(frames) < capacity:
                frames.append(pages[i])
            else:
                lru_page = min(frames, key=lambda x: pages[:i][::-1].index(x))
                frames[frames.index(lru_page)] = pages[i]
            page_faults += 1
            status = "Fault"
        else:
            status = "Hit"

        if show:
            print(f"Step {i+1} -> Page {pages[i]} -> {status} -> Frames: {frames}")

    if show:
        print_statistics(pages, page_faults)

    return page_faults