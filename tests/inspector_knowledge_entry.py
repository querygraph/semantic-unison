"""Versioned advisory component+MakerNote entry; exact Root IO admission required."""
import os
from pathlib import Path
import sys
from shared_dispatch import run

ROOT = Path(__file__).resolve().parents[1]

def main():
    required = ('INSPECTOR_RECEIPT', 'INSPECT_INPUT', 'EXIFTOOL_BUILD',
                'OUTPUT_DIR', 'SHARED_IO_ADMISSION', 'SHARED_IO_ADMISSION_SHA256')
    if any(not os.environ.get(k) for k in required) or os.environ.get('SHARED_CPU_CREDITS') != '8':
        raise ValueError('explicit shared8 knowledge observation environment required')
    for key in required[:-1]:
        if not Path(os.environ[key]).is_absolute():
            raise ValueError('absolute paths required')
    argv = [sys.executable, str(ROOT/'tools/semantic-inspect/run.py'),
            '--use-build', os.environ['INSPECTOR_RECEIPT'],
            '--exiftool-build', os.environ['EXIFTOOL_BUILD'],
            '--', '--components', os.environ['INSPECT_INPUT']]
    output = Path(os.environ['OUTPUT_DIR'])
    # The shared dispatcher owns grants/children, but its caller creates the
    # one-use private receipt directory (as manual.py does). Never reuse it.
    output.mkdir(mode=0o700)
    return run('inspect-file', argv, output, 8,
               io_admission={'path': os.environ['SHARED_IO_ADMISSION'],
                             'sha256': os.environ['SHARED_IO_ADMISSION_SHA256']})

if __name__ == '__main__':
    raise SystemExit(main())
