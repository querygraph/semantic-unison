# Bound local semantic publication ownership

The bound producer path in SemanticSync now uses StagePublication.owned.
Copy and remote semantic receiving still use the legacy native API. Unbound
legacy local materialization also retains its older cleanup behavior.

A preallocated scope and unresolved promise live inside the already-admitted
local transaction. Every owned native call records close uncertainty in that
scope. A linked owner retains the native carrier, original higher-level cause,
and remaining raw transaction descriptors. Ordinary error and connection cleanup
may suppress an exception, but the scope prevents that suppression from turning
unknown ownership into successful or known-failed reservation release.

The publication record owns loose basis/output/parent descriptors immediately
after clone creation, before native adoption or fallible record registration.
Native adoption still establishes name ownership before transaction allocation:
allocation failure can use the identity-bound native owner to remove its stage.
If adoption is uncertain, the loose pair remains retained without numeric retry.
After transaction attachment, a publication-pending flag prevents connection
cleanup from closing the borrowed pair ahead of the native name owner. Successful
native settlement permits ordinary raw transaction closure; uncertainty freezes
it. The scope remains pending despite cancellation/connection cleanup.

The composed original tiny controls cover exact normal materialization and one
producer callback, adoption-close uncertainty, disarm-close uncertainty retaining
the already-published output, and producer failure followed by abort-close
uncertainty. They check first cause, descriptor retention, unchanged source/basis,
transaction/payload/descriptor charges and no retry under connection cleanup.
Fault interposition exists only in copied disposable native C. Unknown owners
intentionally persist until those test processes exit; independent external
child/group closure is distinct from normal application close settlement.

This is native-publication uncertainty integration for one production family,
not a complete raw/channel close-uncertainty migration. Legacy transaction pair
close and allocation-error cleanup still require their own qualified owner work.
Copy, SemanticRemote and actual transport remain separately scoped. No SDK,
Photo file, bulk IO, production deployment or new runtime admission is implied.
