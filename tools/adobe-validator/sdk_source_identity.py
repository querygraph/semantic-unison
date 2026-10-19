"""Strict reviewed DNG SDK release selection; no IO, build or SDK execution.

Historical release notes are not the current package identity. This is a source
preflight, not authentication of arbitrary SDK files or a runtime qualification.
"""
import re


def require_release(readme, expected=2724):
    if type(readme) is not str or type(expected) is not int or expected not in (2724,2768):
        raise ValueError('typed explicitly reviewed SDK release required')
    heading='Release Notes / Changelog:'
    if readme.count(heading)!=1:raise ValueError('one SDK release-notes heading required')
    lines=[line.strip() for line in readme.split(heading,1)[1].splitlines() if line.strip()]
    if not lines:raise ValueError('SDK current release entry missing')
    match=re.fullmatch(r'(\d+\.\d+\.\d+) ([0-9]+) ([A-Za-z]+ [0-9]{1,2}, [0-9]{4})',lines[0])
    if match is None:raise ValueError('SDK first release entry has unreviewed syntax')
    version,build,date=match.groups()
    if version!='1.7.1' or build!=str(expected):
        raise ValueError('requires current Adobe SDK 1.7.1 build '+str(expected)+'; observed '+version+' '+build)
    return dict(version=version,build=expected,release_date=date)
