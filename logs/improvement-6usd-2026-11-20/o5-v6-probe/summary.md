# O5 summary — group-regenerated v6 fixtures, pi-mono, prompt variants V1/V2

Fixtures are GROUP-REGENERATED content; grading on PUBLIC test cases only.
PRIMARY metric: engagement (>=1 tool call reading/editing solution.py or running test_solution.py). Descriptive only; no comparison with the authors' benchmark.

## Variant V1 (cells=32)

### base
- Pass@1: 0/16 (Wilson 95% 0.0–0.1936), INFRA 0
- Engagement (PRIMARY): 13/16 (Wilson 95% 0.5699–0.9341)
- Text-only: 3/16 (Wilson 95% 0.0659–0.4301)
- Read solution.py: 13, edited: 1, ran test cmd: 3, marker seen: 0, solution changed: 1, verifier modified: 0
- Tool totals: {'bash': 3, 'edit': 1, 'read': 13}
- Avg latency (scored): 22.97s, avg steps: 2.06

### realtool
- Pass@1: 0/16 (Wilson 95% 0.0–0.1936), INFRA 0
- Engagement (PRIMARY): 14/16 (Wilson 95% 0.6398–0.965)
- Text-only: 2/16 (Wilson 95% 0.035–0.3602)
- Read solution.py: 14, edited: 6, ran test cmd: 7, marker seen: 0, solution changed: 6, verifier modified: 0
- Tool totals: {'bash': 7, 'edit': 2, 'read': 15, 'write': 6}
- Avg latency (scored): 45.44s, avg steps: 2.5

Paired (within variant V1): realtool gains 0, losses 0, McNemar exact p=1.0

Per-fixture:

| Fixture | Letter | Cases | Base | Realtool |
|---|---|---|---|---|
| livecodebench-v6-000-abc387-b | b | 3 | FAIL (tools 2, engaged=True) | FAIL (tools 1, engaged=True) |
| livecodebench-v6-006-abc388-g | g | 2 | FAIL (tools 2, engaged=True) | FAIL (tools 4, engaged=True) |
| livecodebench-v6-012-abc389-b | b | 2 | FAIL (tools 2, engaged=True) | FAIL (tools 3, engaged=True) |
| livecodebench-v6-018-abc390-g | g | 3 | FAIL (tools 1, engaged=True) | FAIL (tools 5, engaged=True) |
| livecodebench-v6-024-abc391-d | d | 2 | FAIL (tools 0, engaged=False) | FAIL (tools 2, engaged=True) |
| livecodebench-v6-030-abc392-a | a | 2 | FAIL (tools 1, engaged=True) | FAIL (tools 1, engaged=True) |
| livecodebench-v6-037-abc393-f | f | 2 | FAIL (tools 1, engaged=True) | FAIL (tools 1, engaged=True) |
| livecodebench-v6-043-abc394-f | f | 3 | FAIL (tools 2, engaged=True) | FAIL (tools 1, engaged=True) |
| livecodebench-v6-049-abc395-f | f | 4 | FAIL (tools 1, engaged=True) | FAIL (tools 2, engaged=True) |
| livecodebench-v6-055-abc396-f | f | 3 | FAIL (tools 1, engaged=True) | FAIL (tools 2, engaged=True) |
| livecodebench-v6-063-abc397-g | g | 3 | FAIL (tools 0, engaged=False) | FAIL (tools 0, engaged=False) |
| livecodebench-v6-070-abc398-a | a | 2 | FAIL (tools 1, engaged=True) | FAIL (tools 3, engaged=True) |
| livecodebench-v6-076-abc399-c | c | 3 | FAIL (tools 1, engaged=True) | FAIL (tools 1, engaged=True) |
| livecodebench-v6-082-abc400-b | b | 4 | FAIL (tools 1, engaged=True) | FAIL (tools 1, engaged=True) |
| livecodebench-v6-090-arc191-a | a | 3 | FAIL (tools 0, engaged=False) | FAIL (tools 3, engaged=True) |
| livecodebench-v6-096-arc193-a | a | 2 | FAIL (tools 1, engaged=True) | FAIL (tools 0, engaged=False) |

## Variant V2 (cells=32)

### base
- Pass@1: 0/16 (Wilson 95% 0.0–0.1936), INFRA 0
- Engagement (PRIMARY): 1/16 (Wilson 95% 0.0111–0.2833)
- Text-only: 15/16 (Wilson 95% 0.7167–0.9889)
- Read solution.py: 1, edited: 0, ran test cmd: 0, marker seen: 0, solution changed: 0, verifier modified: 0
- Tool totals: {'read': 1}
- Avg latency (scored): 7.16s, avg steps: 1.06

### realtool
- Pass@1: 0/16 (Wilson 95% 0.0–0.1936), INFRA 0
- Engagement (PRIMARY): 2/16 (Wilson 95% 0.035–0.3602)
- Text-only: 12/16 (Wilson 95% 0.505–0.8982)
- Read solution.py: 2, edited: 0, ran test cmd: 2, marker seen: 0, solution changed: 0, verifier modified: 0
- Tool totals: {'bash': 5, 'read': 2}
- Avg latency (scored): 14.34s, avg steps: 1.38

Paired (within variant V2): realtool gains 0, losses 0, McNemar exact p=1.0

Per-fixture:

| Fixture | Letter | Cases | Base | Realtool |
|---|---|---|---|---|
| livecodebench-v6-000-abc387-b | b | 3 | FAIL (tools 0, engaged=False) | FAIL (tools 0, engaged=False) |
| livecodebench-v6-006-abc388-g | g | 2 | FAIL (tools 0, engaged=False) | FAIL (tools 0, engaged=False) |
| livecodebench-v6-012-abc389-b | b | 2 | FAIL (tools 0, engaged=False) | FAIL (tools 0, engaged=False) |
| livecodebench-v6-018-abc390-g | g | 3 | FAIL (tools 1, engaged=True) | FAIL (tools 0, engaged=False) |
| livecodebench-v6-024-abc391-d | d | 2 | FAIL (tools 0, engaged=False) | FAIL (tools 0, engaged=False) |
| livecodebench-v6-030-abc392-a | a | 2 | FAIL (tools 0, engaged=False) | FAIL (tools 2, engaged=True) |
| livecodebench-v6-037-abc393-f | f | 2 | FAIL (tools 0, engaged=False) | FAIL (tools 0, engaged=False) |
| livecodebench-v6-043-abc394-f | f | 3 | FAIL (tools 0, engaged=False) | FAIL (tools 2, engaged=False) |
| livecodebench-v6-049-abc395-f | f | 4 | FAIL (tools 0, engaged=False) | FAIL (tools 0, engaged=False) |
| livecodebench-v6-055-abc396-f | f | 3 | FAIL (tools 0, engaged=False) | FAIL (tools 0, engaged=False) |
| livecodebench-v6-063-abc397-g | g | 3 | FAIL (tools 0, engaged=False) | FAIL (tools 0, engaged=False) |
| livecodebench-v6-070-abc398-a | a | 2 | FAIL (tools 0, engaged=False) | FAIL (tools 0, engaged=False) |
| livecodebench-v6-076-abc399-c | c | 3 | FAIL (tools 0, engaged=False) | FAIL (tools 2, engaged=True) |
| livecodebench-v6-082-abc400-b | b | 4 | FAIL (tools 0, engaged=False) | FAIL (tools 1, engaged=False) |
| livecodebench-v6-090-arc191-a | a | 3 | FAIL (tools 0, engaged=False) | FAIL (tools 0, engaged=False) |
| livecodebench-v6-096-arc193-a | a | 2 | FAIL (tools 0, engaged=False) | FAIL (tools 0, engaged=False) |
