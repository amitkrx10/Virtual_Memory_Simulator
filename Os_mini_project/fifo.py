from utils import print_statistics

def fifo(pages, capacity, show=True):
    frames = []
    page_faults = 0

    if show:
        print("\n===== FIFO Page Replacement =====")

    for i, page in enumerate(pages):
        if page not in frames:
            if len(frames) < capacity:
                frames.append(page)
            else:
                frames.pop(0)
                frames.append(page)
            page_faults += 1
            status = "Fault"
        else:
            status = "Hit"

        if show:
            print(f"Step {i+1} -> Page {page} -> {status} -> Frames: {frames}")

    if show:
        print_statistics(pages, page_faults)

    return page_faults