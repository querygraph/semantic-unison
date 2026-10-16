These are original synthetic lifecycle controls, not fuzzing or SDK tests.
They preserve all private logs and use no photographic inputs.

```sh
python3 tests/adobe_native_deadline/run.py
python3 tests/adobe_native_deadline/phase_test.py --report /private/tmp/phase-result.json
python3 tests/adobe_native_deadline/core_phase.py \
  --target /absolute/contained-pilot/validation-bench \
  --report /private/tmp/core-phase-result.json
python3 tests/adobe_native_deadline/mock_pilot.py \
  --ocamlopt /absolute/compiler \
  --production-build /absolute/current/qualified/Make/snapshot \
  --report /private/tmp/mock-pilot-result.json
```

The mock pilot runs the actual runner and current core with fake protocol tools.
Its writer copies an original CFA file and changes a TIFF compression tag; it
never compresses JPEG/JXL. The fake validator independently hashes the original
bytes and checks their MD5. Mock `decode success` is a protocol exercise and
**does not qualify decoding, SDK behavior, or valid compressed DNGs**.

The outer phase retains its unreaped leader PID through group cleanup. It stops
work before the aggregate wall limit, permits cooperative cleanup, escalates to
KILL, then requires every other group member (including zombies) to disappear
before reaping its leader. Both real per-call timeouts and abrupt Python worker
exit are covered. A missing observation or persistent descendant retains an
unresolved marker; it cannot become successful or release ownership by timeout.

This is trusted-tool process-group containment. Deliberate group/session escape,
SIGKILL of the outer ownership supervisor, kernel hangs and hostile executables
are outside its guarantee. The pilot C backend is separately compiled to keep
all helpers in the outer group, and targets individual helper PIDs for normal
cancellation. Production builds keep separate helper groups. The SDK pilot is
not an exact production-C-backend timing comparison; its full ML validation,
workers, hashing, admission and receipt path are the checked production objects.
No native SDK admission follows from these tests.
