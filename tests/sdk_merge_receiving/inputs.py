"""Pure retained-state/observed-metadata join; neither reads nor grants payload IO."""
from pathlib import PurePosixPath
import re
from sdk_merge_receiving.plan import CODECS, path, digest, require

STATES = ('base', 'left', 'right', 'target')
FIELDS = ('st_dev','st_ino','st_mode','st_size','st_mtime_ns','st_ctime_ns','st_nlink','st_uid')
# Local qualified-data namespace, not a caller-selected trusted root. Base fixture
# preservation is separate: only exact codec/state successor names are eligible.
PERSISTENT_STATES = PurePosixPath('/Users/alexy/Library/Application Support/FirstPair Unison/retained-sdk-fixtures-v1')


def admitted_state_path(name, codec, state):
    value=PurePosixPath(name)
    if value.is_relative_to('/private/tmp'):return True
    if not value.is_relative_to(PERSISTENT_STATES):return False
    parts=value.relative_to(PERSISTENT_STATES).parts
    return len(parts)==2 and re.fullmatch('[0-9a-f]{32}',parts[0]) is not None and parts[1]==codec+'-'+state+'.dng'



def bind(cases, observed, *, expected_uid):
    """Caller authenticates ancestry and supplies fresh lstat, never followed stat.

    Historical SHA values remain declarations until disposable native clones
    are hashed under owned IO. This cannot establish unchanged source bytes.
    """
    require(type(expected_uid) is int and expected_uid >= 0, 'exact current UID required')
    require(type(cases) is list and len(cases) == 3
            and [c.get('codec') for c in cases if type(c) is dict] == list(CODECS),
            'three ordered generated codecs required')
    require(type(observed) is dict, 'trusted observed source metadata required')
    rows = []; names = set(); identities = set()
    for case in cases:
        require(set(case) == {'codec','xmp_offset','xmp_size','states'},
                'exact retained scalar case fields required')
        offset, size, states = case['xmp_offset'], case['xmp_size'], case['states']
        require(type(offset) is int and offset >= 0 and type(size) is int
                and 0 < size <= 1048576 and type(states) is dict and set(states) == set(STATES),
                'bounded exact scalar geometry and states required')
        lengths = set(); hashes = set()
        for state in STATES:
            reference = states[state]
            require(type(reference) is dict and set(reference) == {'path','sha256','bytes'},
                    'exact historical state reference required')
            name = path(reference['path']); digest(reference['sha256'])
            require(admitted_state_path(name,case['codec'],state) and name not in names,
                    'distinct temporary or exact trusted persistent state path required')
            count = reference['bytes']
            require(type(count) is int and 0 < count <= 128*1048576 and offset+size <= count,
                    'bounded state bytes and in-file XMP extent required')
            epoch = observed.get(name)
            require(type(epoch) is dict and set(epoch) == set(FIELDS)
                    and all(type(v) is int and v >= 0 for v in epoch.values()),
                    'complete typed native source epoch required')
            require(epoch['st_size'] == count and epoch['st_mode'] == 0o100400
                    and epoch['st_uid'] == expected_uid and epoch['st_nlink'] == 1
                    and epoch['st_dev'] > 0 and epoch['st_ino'] > 0,
                    'owned single-link readonly regular source required')
            identity = epoch['st_dev'], epoch['st_ino']
            require(identity not in identities, 'aliased retained source inode')
            names.add(name); identities.add(identity); lengths.add(count); hashes.add(reference['sha256'])
            rows.append(dict(codec=case['codec'], state=state, path=name,
                             sha256=reference['sha256'], bytes=count, identity=dict(epoch)))
        require(len(lengths) == 1 and len(hashes) == 4,
                'four distinct fixed-size scalar states required')
    require(set(observed) == names, 'unexpected or missing source observation')
    return rows
