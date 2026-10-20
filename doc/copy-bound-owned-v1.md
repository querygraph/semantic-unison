# Ordinary bound local clone publication ownership

Copy's bound local clone helper now uses StagePublication.owned. Both source
cloning and local receiver-basis comparison use that helper. Network rsync clone
staging, legacy named-source cloning, and raw/channel close uncertainty remain
separate migrations; this is not a universal Copy cleanup qualification.

Each admitted producer callback creates a preallocated guard. A native uncertainty
carrier marks that guard and retains it with its publication records. The callback
then remains pending inside TargetBinding.with_producer; its existing reservation
and busy ticket cannot be finalized or retired as a known failed prefix. The
first higher-level error is preserved separately from native close evidence.

Publication records own loose raw descriptors immediately after clone creation.
After cloneChannels consumes them, direct channel fields/flags record ownership
without allocating option wrappers. The channel registries and clone cleanup
helpers recognize retained channel objects by physical identity, so connection
cleanup does not close them or a later object that reused a numeric descriptor.
Normal explicit settlement closes channels and clears flags. Once uncertainty
is observed, no further native cleanup or fallback is authorized by that guard.

The native carrier retains its own proof handles and actual filename phase.
An uncertain disarm preserves the published candidate. A writer failure followed
by uncertain abort retains the original writer cause and the remaining channel
pair; filename cleanup already performed by abort is not called rollback or
replayed. Ordinary raw/channel close errors outside native-publication uncertainty
are still legacy behavior and are not covered by this migration.

Original tiny controls exercise real admitted TargetBinding tickets, generated
8KiB files, normal source-clone and local receiver-basis APIs, and composed
adoption/disarm/writer-plus-abort close failures. They check exact bytes,
source/live identity and metadata, actual Guarded_producer completion, held
transaction/payload/descriptor credits, remaining raw/channel handles, and no
cleanup/retry/release under explicit ticket release and connection cleanup.
The complete production Copy implementation is copied without substitutions;
only disposable native C close calls are interposed. There is no actual CLI
transport, SDK, camera/Photo payload, production commit or performance claim.
