def print_statistics(pages, page_faults):
    total = len(pages)
    hits = total - page_faults
    hit_ratio = hits / total
    fault_ratio = page_faults / total

    print("\n----- Statistics -----")
    print(f"Total Requests : {total}")
    print(f"Page Faults    : {page_faults}")
    print(f"Page Hits      : {hits}")
    print(f"Hit Ratio      : {hit_ratio:.3f}")
    print(f"Fault Ratio    : {fault_ratio:.3f}")