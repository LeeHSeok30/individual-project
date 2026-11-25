"""Reproduce the rolling-score experiments with CPython and its standard library."""
import argparse
from collections import deque
import csv
import hashlib
import itertools
import json
from pathlib import Path
import platform
import random
import statistics
import sys
import tempfile
from time import perf_counter_ns

from methods import METHODS, validate

class Meter(int):
    """Count comparisons between data values, separately from timing."""
    count = 0

    def __gt__(self, other):
        Meter.count += 1
        return int.__gt__(self, other)

    def __ge__(self, other):
        Meter.count += 1
        return int.__ge__(self, other)


def trace(x, k, keep_equal=False, snapshot=None):
    """Yield update statistics plus the reported value. Retain indices only."""
    validate(x, k)
    q = deque()
    for i, value in enumerate(x):
        if q and q[0] <= i-k:
            q.popleft()
        comparisons = removed = 0
        while q:
            comparisons += 1
            old = x[q[-1]]
            if old > value or (keep_equal and old == value):
                break
            q.pop()
            removed += 1
        q.append(i)
        if snapshot is not None:
            snapshot.append(list(q))
        yield comparisons, removed, len(q), x[q[0]] if i+1 >= k else None


def cases(n, seed):
    rng = random.Random(seed)
    original = [rng.randrange(41) for _ in range(n)]
    shuffled = original.copy()
    rng.shuffle(shuffled)
    yield 'draw', original
    yield 'shuffle', shuffled
    yield 'asc', sorted(original)
    yield 'desc', sorted(original, reverse=True)
    if seed == 2026:
        yield 'flat', [20] * n


def check():
    total = 0
    for n in range(1, 8):
        for x in itertools.product((-1, 0, 1), repeat=n):
            for k in range(1, n+1):
                oracle = [max(x[j:j+k]) for j in range(n-k+1)]
                for f in METHODS:
                    assert f(x, k) == oracle, (f.__name__, x, k)
                for tie in (False, True):
                    assert [v for _, _, _, v in trace(x,k,tie) if v is not None] == oracle
                total += 1
    for x,k in [([],1),([1],0),([1],2),([1],1.5)]:
        for f in METHODS:
            try:
                f(x,k)
            except ValueError:
                continue
            raise AssertionError((f.__name__, x, k))
    print(f'Exhaustive check: {total:,} input/width pairs passed; three methods and two tie rules.')
    print('Example [28, 14, 20, 17, 12, 16], k=5')
    for f in METHODS:
        print(f'  {f.__name__:9s} {f([28,14,20,17,12,16],5)}')


def benchmark(directory):
    directory.mkdir(parents=True, exist_ok=True)
    fields = ['n','k','seed','pattern','method','data_sha256','comparisons','median_ms','q1_ms','q3_ms'] + [f'round{i}_ns' for i in range(1,10)]
    records, traces = [], []
    configs = [(80,5)] + list(itertools.product([1024,4096,16384],[5,20,80]))
    configs = [(n,k,seed,name,x) for n,k in configs for seed in [2026,2027,2028] for name,x in cases(n,seed)]
    random.Random(2026).shuffle(configs)
    for n,k,seed,name,x in configs:
        digest = hashlib.sha256(bytes(x)).hexdigest()
        reference = [max(x[i:i+k]) for i in range(n-k+1)]
        for f in METHODS:
            assert f(x,k) == reference
        # A balanced schedule: each method occupies each position three times.
        order_rng = random.Random(n*10000+k+seed)
        base = list(METHODS)
        order_rng.shuffle(base)
        orders = [base[i:]+base[:i] for i in range(3)]*3
        order_rng.shuffle(orders)
        samples = {f:[] for f in METHODS}
        for order in orders:
            for f in order:
                start = perf_counter_ns()
                out = f(x,k)
                elapsed = perf_counter_ns()-start
                samples[f].append(elapsed)
                assert out == reference
                del out
        measured = {}
        wrapped = list(map(Meter,x))
        for f in METHODS:
            Meter.count = 0
            assert f(wrapped,k) == reference
            measured[f.__name__] = Meter.count
            times = samples[f]
            q1,med,q3 = statistics.quantiles(times,method='inclusive')
            records.append([n,k,seed,name,f.__name__,digest,Meter.count,med/1e6,q1/1e6,q3/1e6,*times])
        assert measured['scan'] == (n-k+1)*(k-1)
        assert measured['block'] == 2*(n-((n+k-1)//k)) + n-k+1
        for tie in (False,True):
            stats = list(trace(x,k,tie))
            assert [row[3] for row in stats[k-1:]] == reference
            count = sum(row[0] for row in stats)
            if not tie:
                assert count == measured['monotone']
            traces.append([n,k,seed,name,'oldest' if tie else 'newest',count,
                           max(row[1] for row in stats),max(row[2] for row in stats),
                           statistics.mean(row[2] for row in stats)])
    tables = [('runs.csv',fields,records),('trace.csv',['n','k','seed','pattern','tie','value_tests','max_pops','peak_slots','mean_slots'],traces)]
    for name,header,rows in tables:
        with tempfile.NamedTemporaryFile(mode='w',dir=directory,encoding='utf-8',newline='',delete=False) as stream:
            w=csv.writer(stream)
            w.writerow(header)
            w.writerows(sorted(rows))
        Path(stream.name).replace(directory/name)
    env = dict(python=sys.version,system=platform.system(),release=platform.release(),machine=platform.machine(),timer='perf_counter_ns',rounds=9)
    (directory/'environment.json').write_text(json.dumps(env,indent=2)+'\n',encoding='utf-8')
    print(f'{len(configs)} paired-condition inputs, {len(records)} method summaries, {len(records)*9} timed calls.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['check','bench'])
    parser.add_argument('--out',type=Path,default=Path('new-results'))
    args=parser.parse_args()
    if not __debug__:
        parser.error('Run with assertions enabled (without -O).')
    if args.mode=='check':
        check()
    else:
        benchmark(args.out)
