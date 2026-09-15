from pathlib import Path
import os
import shutil
import subprocess
import tempfile

OUTPUT = Path(__file__).resolve().parents[1]
SOURCE = Path('/Users/morpheous/APPLICATIONS_2/Firefox/mozilla-unified')
PATCH = OUTPUT / 'patches/native-lookup.patch'
CANDIDATE = OUTPUT / 'scripts/firefoxNightlyUpdate'


def run(args, cwd, *, check=True, env=None):
    return subprocess.run(args, cwd=cwd, check=check, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)


def git(cwd, *args):
    return run(['git', *args], cwd).stdout


with tempfile.TemporaryDirectory(prefix='firefox-updater-test-') as temporary:
    root = Path(temporary)
    origin = root / 'origin.git'
    seed = root / 'seed'
    checkout = root / 'checkout'
    git(root, 'init', '--bare', str(origin))
    git(root, 'init', '-b', 'bookmarks/central', str(seed))
    git(seed, 'config', 'user.name', 'Updater Test')
    git(seed, 'config', 'user.email', 'updater-test@example.invalid')
    patch_paths = [line.split(' b/', 1)[1] for line in PATCH.read_text().splitlines()
                   if line.startswith('diff --git ')]
    for relative in patch_paths:
        fixture = OUTPUT / 'tests/fixtures/base' / relative
        if fixture.exists():
            path = seed / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(fixture.read_bytes())
    (seed / 'mach').write_text('#!/bin/bash\necho build >> build-count\nexit "${TEST_BUILD_EXIT:-0}"\n')
    (seed / 'mach').chmod(0o755)
    git(seed, 'add', '.')
    git(seed, 'commit', '-m', 'Upstream fixture')
    git(seed, 'remote', 'add', 'origin', str(origin))
    git(seed, 'push', '-u', 'origin', 'bookmarks/central')
    git(root, 'clone', '--branch', 'bookmarks/central', str(origin), str(checkout))
    script = root / 'updater'
    text = CANDIDATE.read_text().replace(str(SOURCE), str(checkout)).replace(
        '$PACKAGE_DIR/patches/native-lookup.patch', str(PATCH))
    script.write_text(text)
    helper_dir = checkout / 'obj-test/dist/Nightly.app/Contents/MacOS/gpu-helper.app/Contents/MacOS'
    helper_dir.mkdir(parents=True)
    (helper_dir / 'Nightly GPU Helper').write_text('fixture helper')
    helper_alias = helper_dir / 'Firefox Nightly GPU Helper'

    for iteration in range(2):
        result = run(['bash', str(script)], root)
        git(checkout, 'apply', '--reverse', '--check', str(PATCH))
        assert (checkout / 'build-count').read_text().count('build') == iteration + 1
        assert helper_alias.read_text() == 'fixture helper'
        assert 'Native macOS Look Up patch applied' in result.stdout
        print(f'PASS: update {iteration + 1} reapplies the complete patch and retains the GPU fix')

    missing = root / 'missing-patch-updater'
    missing.write_text(text.replace(str(PATCH), str(root / 'missing.patch')))
    before = git(checkout, 'rev-parse', 'HEAD')
    result = run(['bash', str(missing)], root, check=False)
    assert result.returncode != 0 and 'patch is missing' in result.stdout
    assert git(checkout, 'rev-parse', 'HEAD') == before
    assert (checkout / 'build-count').read_text().count('build') == 2
    print('PASS: missing patch stops before resetting or building')

    helper_alias.unlink()
    result = run(['bash', str(script)], root, check=False,
                 env={**os.environ, 'TEST_BUILD_EXIT': '7'})
    assert result.returncode == 7 and '==> Done.' not in result.stdout
    assert not helper_alias.exists()
    git(checkout, 'apply', '--reverse', '--check', str(PATCH))
    print('PASS: build failure stops without running helper fixes or reporting success')

    changed = seed / 'browser/actors/ContextMenuChild.sys.mjs'
    changed.write_text('// Incompatible upstream rewrite\n')
    git(seed, 'add', str(changed))
    git(seed, 'commit', '-m', 'Upstream conflict fixture')
    git(seed, 'push')
    before_files = {path: (checkout / path).read_bytes() for path in patch_paths}
    before_head = git(checkout, 'rev-parse', 'HEAD')
    before_builds = (checkout / 'build-count').read_bytes()
    result = run(['bash', str(script)], root, check=False)
    assert result.returncode != 0 and 'Stopped before resetting' in result.stdout
    assert git(checkout, 'rev-parse', 'HEAD') == before_head
    assert (checkout / 'build-count').read_bytes() == before_builds
    assert all((checkout / path).read_bytes() == value for path, value in before_files.items())
    print('PASS: upstream conflict leaves the existing source, patch, and build untouched')

    git(checkout, 'remote', 'set-url', 'origin', str(root / 'unavailable.git'))
    result = run(['bash', str(script)], root, check=False)
    assert result.returncode != 0
    assert git(checkout, 'rev-parse', 'HEAD') == before_head
    assert (checkout / 'build-count').read_bytes() == before_builds
    print('PASS: fetch failure stops before resetting or building')

    build_checkout = root / 'build-checkout'
    shutil.copytree(OUTPUT / 'tests/fixtures/base', build_checkout)
    git(build_checkout, 'init')
    (build_checkout / 'mach').write_text('#!/bin/bash\necho build >> build-count\n')
    (build_checkout / 'mach').chmod(0o755)
    build_env = dict(os.environ)
    build_env.pop('MOZCONFIG', None)
    command = ['bash', str(OUTPUT / 'scripts/build-patched-nightly.sh'), str(build_checkout)]
    for iteration in range(2):
        run(command, root, env=build_env)
        git(build_checkout, 'apply', '--reverse', '--check', str(PATCH))
        assert (build_checkout / 'build-count').read_text().count('build') == iteration + 1
        assert (build_checkout / 'mozconfig').read_bytes() == (OUTPUT / 'config/mozconfig').read_bytes()
    print('PASS: packaged build script applies the patch, configures artifact mode, and supports repeat builds')
    (build_checkout / 'mozconfig').write_text('ac_add_options --enable-artifact-builds\n# existing config\n')
    run(command, root, env=build_env)
    assert '# existing config' in (build_checkout / 'mozconfig').read_text()
    print('PASS: packaged build script preserves an existing build configuration')
    (build_checkout / 'browser/actors/ContextMenuChild.sys.mjs').write_text('// conflict\n')
    before_builds = (build_checkout / 'build-count').read_bytes()
    result = run(command, root, check=False, env=build_env)
    assert result.returncode != 0
    assert (build_checkout / 'build-count').read_bytes() == before_builds
    print('PASS: packaged build script stops on a conflicting source change')

print('All updater and build integration checks passed. No live source checkout was accessed.')
