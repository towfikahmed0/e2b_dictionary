## 2025-05-22 - [Optimizing Large Dictionary Search]
**Learning:** For a 20,000-entry dictionary, standard array methods like `.filter().slice()` can be ~30x slower than a manual `for` loop with early exit. Additionally, sorting the entire array for random selection is extremely inefficient (O(N log N)) compared to index-based selection (O(k)).
**Action:** Always prefer manual loops with early termination for search-as-you-type features on large datasets, and use index-based random selection for sampling.
