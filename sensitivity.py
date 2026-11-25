"""Paired implementation experiment. Same block boundaries and comparisons."""
import argparse
import csv
import random
import statistics
from pathlib import Path
from time import perf_counter_ns
from experiment import Meter, cases
from methods import block,validate


def block_inline(x,k):
    validate(x,k)
    left=list(x)
    right=list(x)
    for i in range(1,len(x)):
        if i%k:
            before, current = left[i-1], x[i]
            left[i] = current if current > before else before
    for i in range(len(x)-2,-1,-1):
        if (i+1)%k:
            after, current = right[i+1], x[i]
            right[i] = current if current > after else after
    out=[]
    for s in range(len(x)-k+1):
        suffix,prefix = right[s],left[s+k-1]
        out.append(prefix if prefix > suffix else suffix)
    return out


def run(path):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='') as stream:
        writer=csv.writer(stream)
        writer.writerow(['seed','pattern','method','comparisons','median_ms','raw_ns'])
        for seed in [2026,2027,2028]:
            for name,x in cases(4096,seed):
                k=20
                gold=[max(x[i:i+k]) for i in range(len(x)-k+1)]
                routines=[block,block_inline]
                for f in routines:
                    assert f(x,k)==gold
                order_rng=random.Random(seed)
                orders=[routines,routines[::-1]]*5
                order_rng.shuffle(orders)
                samples={f:[] for f in routines}
                for order in orders:
                    for f in order:
                        t=perf_counter_ns()
                        result=f(x,k)
                        dt=perf_counter_ns()-t
                        assert result==gold
                        samples[f].append(dt)
                        del result
                for f in routines:
                    Meter.count=0
                    assert f(list(map(Meter,x)),k)==gold
                    assert Meter.count==11859
                    writer.writerow([seed,name,f.__name__,Meter.count,statistics.median(samples[f])/1e6,' '.join(map(str,samples[f]))])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=Path('new-results/sensitivity.csv'))
    args=parser.parse_args()
    if not __debug__:
        parser.error('Assertions must be enabled.')
    run(args.out)
