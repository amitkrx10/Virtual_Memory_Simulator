from utils import print_statistics

def optimal(pages, capacity, show=True):
    frames = []
    page_faults = 0

    if show:
        print("\n===== Optimal Page Replacement =====")

    for i in range(len(pages)):
        if pages[i] not in frames:
            if len(frames) < capacity:
                frames.append(pages[i])
            else:
                future = pages[i+1:]
                replace_index = -1
                farthest = -1

                for frame in frames:
                    if frame not in future:
                        replace_index = frames.index(frame)
                        break
                    else:
                        index = future.index(frame)
                        if index > farthest:
                            farthest = index
                            replace_index = frames.index(frame)

                frames[replace_index] = pages[i]

            page_faults += 1
            status = "Fault"
        else:
            status = "Hit"

        if show:
            print(f"Step {i+1} -> Page {pages[i]} -> {status} -> Frames: {frames}")

    if show:
        print_statistics(pages, page_faults)

    return page_faults