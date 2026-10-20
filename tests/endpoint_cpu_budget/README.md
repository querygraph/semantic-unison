# Endpoint CPU ceiling controls

`run.py --build-result <matching Make RESULT.json> --report <fresh path>`
links current Runtime against the recorded compiler-matched dependency objects.
The public interface must match; the runner permits only the Runtime implementation
to differ from the predecessor production inventory. Eleven fixed controls cover
unchanged/default automatic selection, positive ceilings on auto/explicit targets,
negative preferences, permit settlement and over-budget refusal, pool/helper owner
identity, shutdown, restart refusal and same-effective owner reuse.

At most two idle domains are started. The uncapped automatic case tests metadata
only and does not start a host-sized worker pool. A private ignored-ceiling mutation
must fail the named budget oracle before starting a pool. Original failure001
forgot to evaluate a failed Lwt promise; its closed evidence is preserved.

[Actual qualification](../qualification/endpoint-cpu-budget-actual-20261018.json)
records stock/Ox controls and four full Make/Dune CLI builds/selftests. Use the
standing canonical CPU owner; compiler jobs at most two. These are original
fixtures with no SDK/helper/image payload/EXglobal/transport/performance run.
