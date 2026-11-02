# Analysis and Design of Algorithms (AOA) for Query Optimization

## Algorithmic Foundations of QueryOptX

---

### 1. Problem Formulation and Complexity

Given a set of $N$ relations $\mathcal{R} = \{R_1, R_2, \dots, R_N\}$ connected by join predicates $J$, find an execution plan tree $T^*$ over the space of valid execution trees $\mathcal{T}$ that minimizes the estimated execution cost:

$$T^* = \arg\min_{T \in \mathcal{T}} \text{Cost}(T)$$

#### 1.1 Search Space Size (Catalan Numbers)
For $N$ relations:
* Number of join permutations: $N!$
* Number of binary tree shapes with $N$ leaves (Catalan number $C_{N-1}$):
  $$C_{N-1} = \frac{1}{N} \binom{2(N-1)}{N-1} = \frac{(2N-2)!}{N!(N-1)!}$$
* Total number of distinct bushy join trees:
  $$|\mathcal{T}_{\text{bushy}}| = N! \times C_{N-1} = \frac{(2N-2)!}{(N-1)!}$$
* For $N=5$, $|\mathcal{T}| = 1,680$ plans.
* For $N=8$, $|\mathcal{T}| = 17,297,280$ plans.
* For $N=10$, $|\mathcal{T}| = 17,643,225,600$ plans (Join Ordering is NP-Complete).

---

### 2. Algorithm 1: Dynamic Programming (Subset DP)

#### 2.1 Theoretical Foundation
Dynamic Programming operates by bottom-up memoization across the lattice of relation subsets $S \subseteq \mathcal{R}$. It solves optimal substructure subproblems of size $k=1, 2, \dots, N$.

#### 2.2 Recurrence Relation
$$\begin{aligned}
\text{Base Case } (k=1): & \quad DP[\{R_i\}] = \min(\text{Cost}_{\text{SeqScan}}(R_i), \text{Cost}_{\text{IndexScan}}(R_i)) \\
\text{Recurrence } (k \ge 2): & \quad DP[S] = \min_{\substack{S_1 \subset S \\ S_1 \neq \emptyset, S_2 = S \setminus S_1}} \min_{\text{algo} \in \{\text{HJ}, \text{MJ}, \text{NL}\}} \Big( DP[S_1] + DP[S_2] + \text{Cost}_{\text{Join}}(\text{algo}, DP[S_1], DP[S_2]) \Big)
\end{aligned}$$

#### 2.3 Complexity Proof
The number of non-empty disjoint pairs $(S_1, S_2)$ evaluated over all subsets of size $k$ is:
$$\sum_{k=1}^N \binom{N}{k} (2^k - 2) = \sum_{k=0}^N \binom{N}{k} 2^k - 2\sum_{k=0}^N \binom{N}{k} + 1 = (1+2)^N - 2(1+1)^N + 1 = 3^N - 2^{N+1} + 1$$

* **Time Complexity**: $\mathcal{O}(3^N)$
* **Space Complexity**: $\mathcal{O}(2^N)$ memoized entries in hash table
* **Optimality Guarantee**: Provably guarantees the global cost-optimal plan across both bushy and left-deep plan spaces.

---

### 3. Algorithm 2: Greedy Join Enumerator

#### 3.1 Algorithm Description
Greedy optimization is a polynomial heuristic baseline:
1. Evaluate all initial pairs $(R_i, R_j)$ and select the pair with the minimal immediate join cost.
2. At each iteration $i=3 \dots N$, evaluate joining the current accumulator tree with each remaining candidate relation $R_k \in \mathcal{R} \setminus \text{Joined}$.
3. Pick the candidate and join algorithm that produces the local minimal cost.
4. Repeat until all relations are joined.

#### 3.2 Complexity Analysis
* **Time Complexity**: $\mathcal{O}(N^2 \cdot |\text{JoinAlgorithms}|)$
* **Space Complexity**: $\mathcal{O}(N)$
* **Optimality**: Does not guarantee global optimality; prone to local minima because early join choices cannot be reconsidered.

---

### 4. Algorithm 3: Branch and Bound Search

#### 4.1 State-Space Tree Formulation
Branch and Bound explores permutations of relation join sequences via Depth-First Search (DFS) while maintaining:
* `BestCost`: Upper bound on the optimal cost (initially seeded by the Greedy optimizer).
* `CurrentPartialCost`: Cost of currently assembled join prefix.
* `AdmissibleLowerBound`: Minimum possible future cost to complete the plan.

#### 4.2 Bounding and Pruning Rule
For a search node with prefix $P$ and remaining relations $U = \mathcal{R} \setminus P$:
$$\text{LowerBound}(P) = \text{CurrentCost}(P) + \sum_{R \in U} \text{MinScanCost}(R)$$

$$\text{If } \text{LowerBound}(P) \ge \text{BestCost} \implies \text{Prune Subtree}$$

#### 4.3 Proof of Admissibility
Since $\text{MinScanCost}(R) \le \text{ActualExecutionCost}(R \bowtie \dots)$ for any valid relational join (join costs are strictly non-negative), $\text{LowerBound}(P) \le \text{TrueFutureCost}(P)$. Therefore, no sub-tree containing the true global optimum will ever be pruned.

* **Best-Case Complexity**: $\mathcal{O}(N^2)$ with optimal pruning
* **Worst-Case Complexity**: $\mathcal{O}(N!)$ without pruning
* **Pruning Efficiency**: Tracked and displayed in real time in QueryOptX benchmarks.

---

### 5. Algorithmic Complexity Comparison Summary

| Metric | Dynamic Programming | Greedy Algorithm | Branch & Bound |
| :--- | :--- | :--- | :--- |
| **Search Paradigm** | Bottom-up Subset Memoization | Greedy Local Search | State-Space Tree with Pruning |
| **Time Complexity** | $\mathcal{O}(3^N)$ | $\mathcal{O}(N^2)$ | $\mathcal{O}(N!)$ worst, $\mathcal{O}(N^2)$ best |
| **Space Complexity**| $\mathcal{O}(2^N)$ | $\mathcal{O}(N)$ | $\mathcal{O}(N)$ (recursion stack) |
| **Global Optimality**| Guaranteed (Bushy + Left-Deep)| Not guaranteed (Local minima) | Guaranteed (Within search order)|
| **Bushy Join Support**| Yes | Left-deep spine | Left-deep permutation |
| **Best Used For** | $N \le 12$ Relations | $N > 15$ Relations | $N \le 10$ with tight bounds |
