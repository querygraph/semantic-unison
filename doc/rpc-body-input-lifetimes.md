# Raw RPC body input ownership

Incoming body payloads now use two process-local, endpoint-controlled service
lanes. Admission never waits on another request, CPU permit or transaction.
Exhaustion fails the incoming operation before payload allocation. It does not
claim that disconnect settles already-active application borrowers.

| Setting | Default | Meaning |
| --- | ---: | --- |
| `rpcrequestinputbudget` | 256MiB | Combined raw body allowance for legacy requests, explicitly bounded requests and stream chunks. |
| `rpcreplyinputbudget` | 256MiB | Independent raw normal-result allowance, including arrived but unconsumed reply promises. |
| `rpcbodyinputslots` | 256 | Maximum slots in **each** lane, including incomplete length prefixes and zero-length bodies. Maximum65536. |

MiB values must be positive and convert without integer overflow. Each receive
creates a fresh ticket, reserves its slot before reading a length prefix, then
reserves exact announced payload bytes before buffer allocation. Byte grants
use current policy; already-owned slots/bytes are not revoked by later settings.
Increasing a command/frame limit does not increase a lane budget. There is no
requirement that the maximum possible frame fit a lane: smaller actual frames
remain admissible. A deliberately larger archive result may require raising
both `rpcpacketmaxbytes` and `rpcreplyinputbudget` on its receiving endpoint.

`rpcboundedinputbudget`/`rpcboundedinputslots` remain additional restrictions on
the bounded-command subset of the request lane; those are overlapping claims,
not extra payload allocations to sum. Header/startup allowances remain separate.
A full request lane cannot consume reply or header service credits. All these
settings are endpoint-local, omitted from outgoing preferences and immune to
incoming peer overrides. No installed binary or user profile is modified.

## Lifetimes

- Requests: ownership transfers to the detached processing promise, covering
  synchronous decoding, the handler, marshaling and actual queued reply output.
  It releases on success or an ordinary settled failure. A connection close does
  not release a still-active handler borrower.
- Streams: ownership covers synchronous handler execution and any queued abort
  output. Ordinary stream failures retain their existing abort behavior.
- Normal results: an owned packet moves into the reply promise and remains
  charged through its scheduling yield and synchronous decoder. A decode error
  also releases a known-settled raw packet. If outgoing request output fails
  after a reply has already arrived, the failed send path awaits the actual
  waiter and abandons that unconsumed packet.
- Reply handoff: the Return state is prepared before removing the receiver and
  installed before observer dispatch. Transfer intent is marked before entering
  that primitive. Errors at/after that point cannot automatically free a
  possibly-live consumer, even if an observer throws. This can conservatively
  retain an uncertain handoff until process exit; no guessed release is used.

Tickets explicitly root received payloads until release, and release is
idempotent. The raw read itself remains borrowed until actual read settlement.
Before-transfer preparation failures release known packet ownership and fail
its waiter. Repeated sizing is invalid. There is no ticket reuse API.

## Unresolved ownership

Core notification-pipe, directory, domain-join and publication uncertainty
carriers pass through `RetainedOwnership.guard`; they cannot trigger ordinary
raw-ticket cleanup. Stream uncertainty must reach that guard instead of being
translated into an ordinary abort. The bounded-command subset guard follows the
same rule, so neither overlapping allowance is prematurely released. Original
causes and the guard's unresolved promise stay rooted; no clear/retry interface
is added.

`Remote.register_body_ownership_classifier` adds pure owner-loop predicates at
initialization for types defined later in the link graph. `SemanticRuntime`
registers its existing semantic-file/component-cache predicate this way. A
classifier failure also retains ownership under the existing retaining guard.
Standalone consumers of other late carrier types must register a predicate or
provide their own qualified retaining scope. This is not automatic recognition
of arbitrary exceptions or a new plugin execution authority.

## Boundaries and controls

The two defaults declare512MiB of combined raw body allowance, separate from
the16MiB header/startup lane. This is not a measured allocation peak, whole-process
memory budget or hard RSS cap. Payload/object headers, ticket/guard/connection/
receiver-map metadata, kernel buffers, garbage awaiting collection, decoded
values outliving their decoder, outbound marshaled replies and native helper
memory are outside these raw charges. Per-decode builtin expansion limits still
apply only to explicitly bounded registrations. Per-process accounting is not
machine/process-tree containment.

Original in-process pipe controls cover active detached work, queued legacy
reply success/failure, reply arrival before send failure, idle-prefix and exact
byte exhaustion, zero bodies, allocation/reserve callback failures, decoding
failure, header/reply service progress while request slots are full, observer
failure after handoff, and ordinary queued stream aborts. Core and registered
synthetic uncertainty fixtures deliberately keep raw/subset charges and reachable
payloads until test process exit. They acquire no directory/FD/native authority
and do **not** prove normal in-process teardown of retained owners. Private
participants omit decoder cleanup, release handed-off ownership, disable the
retaining guard, convert stream uncertainty to abort, or omit registered
classifiers; each must fail its designated assertion. Existing frame/header/
startup/decoder counterexamples remain independent. No actual transport, SDK,
Photo/camera payload, physical-IO work or performance qualification is implied.
