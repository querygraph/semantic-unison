# Bound remote receiver publication ownership

SemanticRemote's bound producer path now uses the explicit native publication
owner and a preallocated guard inside its receiver transaction reservation.
This follows the qualified local SemanticSync lifecycle. Ordinary Copy and the
unbound legacy remote path remain separate migrations.

The receiver owns loose clone descriptors immediately, lets native adoption
establish identity-bound name ownership before fallible record registration,
and then attaches the candidate. Publication-pending and retained flags prevent
connection/error cleanup from closing descriptors or unlinking ahead of the
native name owner. Once native uncertainty is observed, a linked scope retains
the original cause, native carrier and remaining known descriptors. Suppressed
cleanup errors cannot turn that state into a normal return or reservation release.
The pending operation remains charged; diagnostic access grants no cleanup or
numeric-FD retry authority.

The original tiny composed controls replace only the peer-supported predicate
and request-plan delivery in a private copy of production SemanticRemote. The
actual source planner, SDE encode/decode/binding, worker inspection/materialization,
APFS staging and native publication remain real code. There is no transport,
server process or SDK in these unit controls. They cover exact normal output,
adoption-close uncertainty, disarm-close uncertainty preserving published output,
and callback error followed by abort-close uncertainty. Source/basis bytes,
original cause, callback count, held descriptor/reservation observations, no
retry and connection-cleanup behavior are checked.

Fresh actual transport still requires a separate exact source/build admission and
client/server/pump/group audit. A passing in-process planner unit does not supply
that evidence. Legacy raw/channel close handling, unbound staging, and ordinary
Copy also remain distinct; this migration must not be presented as universal
resource-close qualification or physical IO isolation. No Photo/camera payload,
SDK, production publication or automatic successor grant is implied.
