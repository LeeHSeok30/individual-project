"""Replay Stephen Curry's 2023-24 regular season and shuffle its scores."""
import argparse
from collections import Counter
import csv
from datetime import date
from pathlib import Path
import random
import statistics

from experiment import Meter, trace
from methods import METHODS
from streaming import RollingMax


DATA = Path(__file__).with_name("data") / "curry_2023_24.csv"
WIDTH = 5
SHUFFLES = 5000
SEED = 2026


def load_games():
    with DATA.open(encoding="utf-8", newline="") as f:
        games = [(date.fromisoformat(r["date"]), int(r["points"])) for r in csv.DictReader(f)]
    dates = [day for day, _ in games]
    assert dates == sorted(set(dates))
    assert len(games) == 74 and sum(points for _, points in games) == 1956
    return games


def replay(scores):
    """Validate each new output, operation count and queue size independently."""
    stream = RollingMax(WIDTH)
    Meter.count = 0
    updates = []
    for i, (points, expected) in enumerate(zip(scores, trace(scores, WIDTH))):
        old_count = Meter.count
        maximum = stream.push(Meter(points))
        comparisons = Meter.count - old_count
        tests, pops, slots, value = expected
        assert (comparisons, stream.candidate_count, maximum) == (tests, slots, value)
        if i + 1 >= WIDTH:
            assert maximum == max(scores[i + 1 - WIDTH:i + 1])
        else:
            assert maximum is None
        updates.append((maximum, comparisons, slots, pops))
    return updates


def write_csv(path, fields, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        writer.writerows(rows)


def run(directory):
    games = load_games()
    scores = [points for _, points in games]
    actual = replay(scores)
    outputs = [r[0] for r in actual if r[0] is not None]
    counts = {}
    for method in METHODS:
        Meter.count = 0
        assert method(list(map(Meter, scores)), WIDTH) == outputs
        counts[method.__name__] = Meter.count
    actual_count = sum(row[1] for row in actual)
    actual_peak = max(row[2] for row in actual)
    assert actual_count == counts["monotone"]

    rng = random.Random(SEED)
    histogram = Counter()
    for _ in range(SHUFFLES):
        order = scores.copy()
        rng.shuffle(order)
        updates = replay(order)
        histogram[sum(r[1] for r in updates), max(r[2] for r in updates)] += 1

    directory.mkdir(parents=True, exist_ok=True)
    write_csv(directory / "curry_windows.csv",
              ["date", "points", "max_last_5", "comparisons", "candidates", "back_pops"],
              [(*g, *u) for g, u in zip(games, actual)])
    write_csv(directory / "curry_shuffles.csv", ["comparisons", "peak_candidates", "frequency"],
              [(*key, freq) for key, freq in sorted(histogram.items())])
    print(f"{len(scores)} appearances, {sum(scores)} points, {len(outputs)} complete windows.")
    print("Actual score comparisons:", counts)
    for col, metric, observed in [(0, "comparisons", actual_count), (1, "peak candidates", actual_peak)]:
        sample = sorted(key[col] for key, freq in histogram.items() for _ in range(freq))
        # Inverse empirical CDF: choose the smallest value with cumulative mass >= p.
        q025, q975 = sample[(25 * SHUFFLES - 1) // 1000], sample[(975 * SHUFFLES - 1) // 1000]
        below = sum(v < observed for v in sample)
        ties = sample.count(observed)
        print(f"{metric}: actual {observed}, shuffled median {statistics.median(sample):g}, "
              f"central 95% [{q025}, {q975}], below/equal/above {below}/{ties}/{SHUFFLES-below-ties}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("new-results"))
    if not __debug__:
        parser.error("Run without -O so that validation is enabled.")
    run(parser.parse_args().out)
