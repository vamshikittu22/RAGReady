# Data Structures and Algorithms

## Arrays and Linked Lists

An array stores elements in contiguous memory locations, providing O(1) random access time using index-based lookup. Array insertion at the end takes O(1) amortized time, but insertion at an arbitrary position requires O(n) time due to shifting elements. A linked list stores elements in nodes where each node contains data and a pointer to the next node. Linked list insertion and deletion at the head take O(1) time, but accessing an element by index requires O(n) time since traversal from the head is necessary. A doubly linked list adds a pointer to the previous node, enabling O(1) deletion when given a reference to the node. Arrays use less memory per element than linked lists because linked lists require extra storage for pointers.

## Hash Tables

A hash table maps keys to values using a hash function that converts keys into array indices. Hash tables provide O(1) average-case time complexity for insertion, lookup, and deletion operations. Hash collisions occur when two different keys map to the same index. Common collision resolution strategies include chaining (using linked lists at each bucket) and open addressing (probing for the next available slot). The load factor of a hash table is the ratio of stored elements to the number of buckets. When the load factor exceeds a threshold (typically 0.75), the hash table resizes by doubling its capacity and rehashing all existing entries. Python dictionaries and sets are implemented using hash tables.

## Trees

A binary tree is a hierarchical data structure where each node has at most two children, called the left child and right child. A Binary Search Tree (BST) maintains the invariant that all values in the left subtree are less than the parent node, and all values in the right subtree are greater. BST search, insertion, and deletion take O(log n) time in the average case but degrade to O(n) in the worst case when the tree becomes unbalanced. An AVL tree is a self-balancing BST that maintains a balance factor (height difference between left and right subtrees) of at most 1, guaranteeing O(log n) operations. A Red-Black tree is another self-balancing BST used in many standard library implementations, including Java's TreeMap and C++'s std::map. A B-tree is a self-balancing tree optimized for disk-based storage, commonly used in database indexes and file systems.

## Heaps and Priority Queues

A binary heap is a complete binary tree that satisfies the heap property: in a min-heap, each parent node is smaller than or equal to its children. Heaps support insertion and extraction of the minimum (or maximum) element in O(log n) time. The heapify operation builds a heap from an unsorted array in O(n) time. Priority queues are commonly implemented using binary heaps and are used in algorithms like Dijkstra's shortest path and Huffman coding. Python provides the heapq module for min-heap operations on regular lists.

## Graphs

A graph consists of vertices (nodes) and edges connecting pairs of vertices. Graphs can be directed (edges have direction) or undirected (edges are bidirectional). An adjacency list represents a graph by storing each vertex's neighbors in a list, using O(V + E) space. An adjacency matrix represents a graph using a V×V matrix, using O(V²) space but providing O(1) edge lookup. Breadth-First Search (BFS) explores vertices level by level using a queue, running in O(V + E) time. Depth-First Search (DFS) explores as far as possible along each branch before backtracking, also running in O(V + E) time. Dijkstra's algorithm finds the shortest path from a source vertex to all other vertices in O((V + E) log V) time using a priority queue.

## Sorting Algorithms

Comparison-based sorting algorithms have a lower bound of O(n log n) time complexity. Merge sort divides the array in half recursively and merges sorted halves in O(n log n) time with O(n) extra space. Quick sort selects a pivot element and partitions the array around it, achieving O(n log n) average time but O(n²) worst-case time. Heap sort uses a binary heap to sort elements in O(n log n) time with O(1) extra space. Non-comparison sorts like counting sort and radix sort can achieve O(n) time complexity for integers within a bounded range.
