from pathlib import Path
import sys,math
sys.path.insert(0,'/private/tmp')
import root61_parser_and_formal_review_v1 as m61
m60=m61.m60;strict=m61.strict
ROLE='STOP_KKT_EXACT_CYCLE_AND_ZERO_SLACK_FULL_ENDPOINT_ORIGINAL_DOMAIN_V4'
def parse(path, actual_rows=20000, events=None):
    b = strict.read_artifact_bytes(path)
    assert len(b) <= 46232
    r = m60.R(b, ROLE)
    cycle, trial, available, stop, policy, count = r.take('<6Q')
    assert count <= 512 and all((x in [0, 1] for x in [available, stop, policy])) and (policy <= stop) and (policy <= available)
    ranks = []
    last = -1
    for _ in range(count):
        it, rank, dim, res = r.take('<3Qd')
        assert last < it < 512 and 0 < rank <= dim <= 288 and math.isfinite(res) and (0 <= res <= 1e-10)
        if events is not None:
            assert it < len(events) and dim == 144 + events[it][1]
        ranks.append((it, rank, dim, res))
        last = it
    count = r.take('<Q')[0]
    assert count <= 512
    chosen = []
    last = -1
    for _ in range(count):
        it, row, side, pos, selected, minimum = r.take('<4q2d')
        assert last < it < 512 and 0 <= row < actual_rows and (side in [-1, 1]) and (0 <= pos < 144) and all((math.isfinite(x) for x in [selected, minimum])) and (minimum <= selected < -1e-12)
        if events is not None:
            assert it < len(events) and events[it][0] == it and (events[it][2] == -1) and (pos < events[it][1]) and (minimum == events[it][4])
        chosen.append((it, row, side, pos, selected, minimum))
        last = it
    exact, n, count = r.take('<3Q')
    assert exact in [0, 1] and exact <= policy and (n <= 144) and (count <= n)
    indices = list(r.take('<' + str(count) + 'Q')) if count else []
    assert indices == sorted(set(indices))
    rows = []
    for index in indices:
        assert index < len(chosen)
        e = chosen[index]
        assert any((q[0] + 2 == e[0] and q[1:4] == e[1:4] for q in chosen[:index]))
        rows.append(e[1])
    assert len(set(rows)) == len(rows) and (not indices or exact) and (available or not (ranks or chosen or exact or indices))
    roundoff, admissions, endpoint_cap = r.take('<3Q')
    assert roundoff in [0,1] and roundoff<=policy and admissions<=16384 and endpoint_cap==16384 and (roundoff or not admissions)
    scope = r.text()
    r.end()
    return dict(cycle=cycle, trial=trial, available=available, stop=stop, policy=policy, ranks=ranks, chosen=chosen, exact=exact, n=n, indices=indices, raw_bytes=len(b), scope=scope, roundoff=roundoff, admissions=admissions, endpoint_cap=endpoint_cap)
