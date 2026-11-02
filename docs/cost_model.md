# QueryOptX Modular Cost Model

---

### 1. Cost Model Overview

Database cost models estimate resource utilization to rank alternative physical plans. In QueryOptX, the total estimated cost is an explicit linear combination of three fundamental hardware resources:

$$\text{Total Cost} = C_{\text{I/O}} + C_{\text{CPU}} + C_{\text{Memory}}$$

---

### 2. Calibrated Cost Weights

| Parameter | Symbol | Default Value | Meaning |
| :--- | :--- | :--- | :--- |
| `seq_page_cost` | $c_{\text{seq}}$ | `1.0` | Cost of reading a sequential disk page (8 KB). |
| `random_page_cost` | $c_{\text{rand}}$ | `4.0` | Cost of non-sequential random page fetch (B-Tree lookups). |
| `cpu_tuple_cost` | $c_{\text{tuple}}$ | `0.01` | CPU cost of processing/fetching a single tuple. |
| `cpu_index_tuple_cost` | $c_{\text{idx\_tuple}}$ | `0.005` | CPU cost of processing an index leaf entry. |
| `cpu_operator_cost` | $c_{\text{op}}$ | `0.0025` | CPU cost of evaluating a predicate or hash function. |
| `memory_page_cost` | $c_{\text{mem}}$ | `0.05` | In-memory hash buffer allocation and cache pressure cost. |

---

### 3. Base Table Access Paths

#### 3.1 Sequential Scan (SeqScan)
Scans every disk page of the relation and evaluates filter predicates:

$$C_{\text{SeqScan}}(R) = \text{Pages}(R) \cdot c_{\text{seq}} + \text{Rows}(R) \cdot c_{\text{tuple}} + \text{Rows}(R) \cdot c_{\text{op}}$$

#### 3.2 Index Scan (IndexScan)
Traverses a B-Tree index to find matching leaf pointers and fetches matching heap pages:

$$C_{\text{IndexScan}}(R, s) = \Big(\lceil \log_2(\text{Pages}(R)) \rceil + \lceil s \cdot \text{IdxPages} \rceil + s \cdot \text{Rows}(R) \cdot 0.5\Big) \cdot c_{\text{rand}} + s \cdot \text{Rows}(R) \cdot (c_{\text{idx\_tuple}} + c_{\text{tuple}})$$

where $s$ is the selectivity factor ($0 < s \le 1.0$).

---

### 4. Join Algorithm Cost Formulas

#### 4.1 Hash Join
Builds an in-memory hash table on the smaller input relation (build relation) and probes with the larger relation:

$$\begin{aligned}
C_{\text{HashJoin}}(L, R) = & \, C(L) + C(R) \\
& + \min(|L|, |R|) \cdot 2 \cdot c_{\text{op}} \quad \text{(Hash Table Build)} \\
& + \max(|L|, |R|) \cdot 1.5 \cdot c_{\text{op}} \quad \text{(Hash Table Probe)} \\
& + \text{BuildPages} \cdot c_{\text{mem}} \quad \text{(Buffer Allocation)}
\end{aligned}$$

#### 4.2 Sort-Merge Join
Sorts both inputs on the join keys (if not already sorted by an index) and performs a simultaneous linear merge scan:

$$\begin{aligned}
C_{\text{MergeJoin}}(L, R) = & \, C(L) + C(R) + \text{SortCost}(L) + \text{SortCost}(R) \\
& + (|L| + |R|) \cdot c_{\text{op}}
\end{aligned}$$

where $\text{SortCost}(N) = N \log_2(N) \cdot 2 \cdot c_{\text{op}}$.

#### 4.3 Nested Loop Join
Evaluates the inner relation for each tuple in the outer relation:

$$C_{\text{NestedLoop}}(L, R) = C(L) + |L| \cdot C(R) + (|L| \cdot |R|) \cdot c_{\text{op}}$$
