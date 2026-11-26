# Rolling score lab

Compare three exact algorithms for a player's highest score over the last k appearances. In Stephen Curry's 2023–24 regular season, his 60 on February 3 drops out of the five-game window on February 12. The maximum falls to 42 even though the new score is 25. The experiment asks how many comparisons it takes to keep this statistic up to date. It pairs one real season with controlled synthetic inputs.

## Inspect or reproduce

Open **viewer.html** locally, choose **Stephen Curry · 2023–24** and move the slider between appearances 47 and 48 to replay that change. The other three records include a decreasing run followed by a new high. Toggle the tie policy to see which game supplies the maximum. The viewer uses verified Python traces and works offline.

For the experiments, install Python 3.9 or later. The recorded run used CPython 3.13.7 on arm64 Darwin 25.6.0. From the unzipped repository root run:

```sh
python3 experiment.py check
python3 experiment.py bench --out new-results
python3 sensitivity.py --out new-results/sensitivity.csv
python3 season.py --out new-results
python3 demo.py
```

The last command regenerates the viewer. On Windows use `py -3` in place of `python3`. The benchmark and viewer generator use the standard library. Running without flags preserves the reference CSVs under results/. Run without Python optimization flags because checks use assertions.

## What to read

- methods.py implements direct scan, monotone deque, and the one-dimensional prefix/suffix block filter. Each accepts a finite indexed sequence of integers and an integer width from 1 to the sequence length, and returns every complete window maximum.
- streaming.py also exposes `RollingMax(k).push(score)` for a feed with unknown length. Keep a single instance between updates. It returns None for the first k−1 appearances and keeps only (index, score) candidates, with the newest equal score winning. experiment.py check validates warm-up and every emitted score on 21,324 small input/width pairs.
- experiment.py generates inputs, verifies outputs, measures uninstrumented wall time, counts value comparisons separately, and records deque occupancy and removals. The source and example are self-contained.
- sensitivity.py reruns the block experiment with explicit comparison branches and an explicit output loop. This measures the combined implementation difference; it cannot isolate the overhead of a single instruction.
- results/runs.csv contains nine ordered timings per row in nanoseconds, median, Q1/Q3 in milliseconds, and comparison counts. Columns round1..round9 follow acquisition order for each method. data_sha256 hashes the input values encoded as one byte each.
- results/trace.csv compares newest-wins and oldest-wins ties. A value test is one logical comparison of two scores against the policy threshold. Peak slots count live candidates, not bytes. Mean slots include warm-up games. results/sensitivity.csv stores all ten balanced implementation trials in ns. results/check.png is a capture of the verification output.
- Results are grouped by input. Never treat nine timings of the same input as nine independently generated datasets. Use the median of the three seed-level medians when summarizing across seeds. Use a per-seed interquartile range to describe trial noise.
- The 80-game case uses k=5. Stress sizes 1024/4096/16384 each use k=5/20/80. Seeds 2026/2027/2028 create paired original, shuffled, ascending and descending versions of the same score multiset. A constant-20 control has no random seed and runs once per size/width (label 2026). Inputs use values 0..40. Shuffling and sorting are outside timing.
- For each condition the three methods receive the same array; one warm-up precedes nine timed calls per method. The method schedule is shuffled with balanced position frequencies. Timing includes the full block preprocessing, output allocation, and all window queries, and excludes data generation, correctness checks, counting and output disposal.
- Use the independent slice maximum in the test harness as oracle. For counts with n values and window k, scan uses (n-k+1)(k-1); block uses 2(n-ceil(n/k))+n-k+1. Both identities are checked on every condition. The deque's count is checked against a separate update trace.

## Season replay and permutation experiment

`data/curry_2023_24.csv` contains US game dates and points for each regular-season appearance in chronological order. DNPs, preseason, the All-Star Game and the play-in game are excluded. A window is five appearances, irrespective of the number of calendar days between them. The two published logs below agreed on all 74 point values in order, totaling 1,956.

`season.py` feeds one score at a time to the stateful deque. It checks every update against an independent index-based trace and the maximum of the current five-score slice. It also checks the three batch methods against all 70 completed windows. On the real sequence, scan used 280 score comparisons, deque 119 and block 188, including warm-up where applicable.

Each of 5,000 shuffles starts from a fresh copy of the same scores, using one Python Random instance seeded with 2026. The shuffled deque median is 116 comparisons with an empirical central 95% range of 111–120 (inverse empirical CDF). Of those orders, 4,516 used fewer comparisons than the real order, 305 used the same number and 179 used more. The real sequence required five candidates at its peak, as did 1,669 shuffles. These are deterministic cost measurements on one season and sampled orders. The reference distribution describes the effect of reordering this particular set of scores.

The outputs are `results/curry_windows.csv` (one row per appearance, empty maximum during warm-up) and `results/curry_shuffles.csv` (joint frequency of total comparisons and peak candidate count, totaling 5,000). Re-running the season command rebuilds both in new-results/.

```python
from streaming import RollingMax

window = RollingMax(5)
for points in [60, 29, 9, 42, 30, 25]:
    print(window.push(points))  # None, None, None, None, 60, 42
```

## Sources and authorship

The comparison uses the course's performance-analysis framework (topics 02, 04, 05). See [assignment](https://lec-algorithm.github.io/lecture/article/project-2026/) and [performance analysis](https://lec-algorithm.github.io/lecture/course/topic-05-complexity/). The deque is a maximum-only implementation. [Lemire (2006)](https://arxiv.org/abs/cs/0610046) discusses the related streaming maximum/minimum problem. The block method adapts the one-dimensional prefix/suffix idea of [van Herk (1992)](https://doi.org/10.1016/0167-8655(92)90069-C).

Season data came from the [ESPN 2023–24 Stephen Curry game log](https://www.espn.com/nba/player/gamelog/_/id/3975/type/nba/year/2024) and the [bayesRatings game log](https://bayesratings.com/nba/players/stephen-curry-3975/?log=2024), accessed 2026-11-26. Dates use the US schedule shown on bayesRatings. ESPN can display calendar dates in the reader's time zone.

The code was written for this project. The standard library supplies deque, max, random, statistics, CSV I/O and the clock. ChatGPT/Codex assisted with the research question, implementations, experiment execution, verification of public records, interpretation, interactive trace and Korean report. The results CSVs were generated by running the code.
