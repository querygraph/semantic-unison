# Prepared component RPC probe

`tests/report/remote_probe.ml` links to the production modules through the remote
and owner layers. It installs generated roots, negotiates features, propagates
preferences and calls `SemanticRemote.observe_components` directly. It does not
replace the server or simulate a SIC/0 response. This is an API/RPC probe, not an
interactive GUI test or permission to read existing media.

The [build-only driver](../tests/report/build_remote_probe.py) rechecks current
production source/compiler pins, links each stock/Ox probe against its respective
Make objects, and preserves the binaries and linked-artifact hashes. It executes
only missing-argument, relative-path and unknown-mode refusals plus an offline
preference parse. Offline `preflight` exits before installing roots or attempting
any connection. Compiling and passing these controls does not qualify transport.

For an admitted runtime call, exact argv is:

```
component-probe ABSOLUTE_LEFT ABSOLUTE_RIGHT PINNED_SERVER PINNED_LAUNCHER MODE
```

Both roots contain an owner-generated `components.dng`; the private UNISON state
directory comes from the outer environment. CPU configuration is2 for the probe
and must be2 for the server in the pinned launcher flags. Both endpoints plus
owner/proxy overhead must fit Unison00..07. The external owner must acquire the
existing EXglobal barrier before CPU, bind fresh admission/source/artifact pins,
hold the complete bundle through actual worker/client/server/group settlement,
and retain unknown outcomes. There is no standalone IO admission in this probe.

Proposed finite runtime cases (not yet scheduled or executed):

| Client probe | Server | Mode and expected outcome |
|---|---|---|
| Stock | Current stock | supported |
| Stock | Current Ox | supported |
| Ox | Current stock | supported |
| Ox | Current Ox | supported |
| Stock | Pinned pre-SIC stock | no-capability |
| Ox | Pinned pre-SIC stock | no-capability |
| Stock | Current stock | unsupported |
| Ox | Current Ox | disabled |

Supported fixtures are original8192-byte DNG parser inputs with equal encoded
units and different opaque bytes. The external audit must independently bind
printed full SHA256 values to the two generated files, retain before/after
identities/hashes, and verify no writes. Unsupported uses a non-TIFF first header
and requires the exact `not TIFF` parser refusal; a transport or admission failure
cannot count as unsupported. No-capability requires the specific negotiation
refusal from an older modified peer that still supports DNG profiles. Disabled
requires the explicit profile-selection refusal. These cases do not establish
camera validity, rendered pixels or persistent reuse.

The probe attempts every known root close and worker shutdown on success/failure;
cleanup failures retain the original failure plus all cleanup errors. Its final
local-resources marker is not parent/server wait evidence. An external strict
loopback supervisor and pre-dispatch intent/outcome journal must separately prove
each client, launcher/supervisor, native server, joined pump, worker and group
closure. Failed prefixes must remain failures; missing evidence retains ownership.
No extra SDK/Adobe/native-UI, camera, receiving or successor scope is implied.

## Prepared coordinator and source review

`tests/component_remote/coordinator.py` now owns the one-use workspace, existing
EXglobal/Unison00..07 bundle and worker with nine inherited descriptions. The
worker independently checks those identities against both canonical manifests
and the standing policy. Artifact hashes are checked after acquisition and before
each case; the exact plan bytes bind the admission. It observes the worker for300s,
stops starting calls40s earlier, and retains ownership on unresolved expiry rather
than killing an aggregate with separate-session owners.

The new call kernel uses the qualified direct-child capture helper and retains
the separate proxy object with any uncertain descriptor/capture outcome. It does
not route close uncertainty through the older benchmark wrapper. Intent precedes
the call; raw outcomes precede functional checks. Known failed calls stop successor
cases. Explicit pre-call failure records differ from pending intents. The parent
reparses every raw proxy/client/supervisor/server/group/pump proof before worker
reap and bundle close. Functional pass additionally requires eight exact cases,
actual generated-file identities/hashes and the expected probe output. The audit
alone cannot authenticate parent terminal or release descriptors.

[Disposable controls](../tests/qualification/component-remote-coordinator-controls-actual-20261017.json)
passed18 methods, with343 source pins before/after. They use fabricated owners and
tiny original files: no canonical locks, RPC, SDK or media. They cover failed-prefix
versus success, no-creation evidence, pending/raw-substituted receipts, original
read/write plus close uncertainty without numeric retries, exact carrier/proxy
retention, noncanonical identities, known pre-child rollback and observation
expiry without aggregate kill. They are not a live transport qualification.

Frozen [plan](component-remote-plan-v1.json) and
[source-review request](component-remote-request-v1.json) contain342 runtime source
pins, six prerequisites and exact proposed argv. The request explicitly asks for
source review only, not an expiring admission or Photo scheduling hold. Review
and fresh readiness/finite Root IO admission remain required before runtime.
Do not execute probe runtime modes merely because these controls passed.
