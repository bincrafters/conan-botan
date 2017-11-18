import os
import re
import platform

from conan.packager import ConanMultiPackager


def get_value_from_recipe(search_string):
    with open("conanfile.py", "r") as conanfile:
        contents = conanfile.read()
        result = re.search(search_string, contents)
    return result


def get_name_from_recipe():
    return get_value_from_recipe(r'''name\s*=\s*["'](\S*)["']''').groups()[0]


def get_version_from_recipe():
    return get_value_from_recipe(r'''version\s*=\s*["'](\S*)["']''').groups()[0]


def get_default_vars():
    username = os.getenv("CONAN_USERNAME", "bincrafters")
    channel = os.getenv("CONAN_CHANNEL", "testing")
    version = get_version_from_recipe()
    return username, channel, version


def is_ci_running():
    return os.getenv("APPVEYOR_REPO_NAME", "") or os.getenv("TRAVIS_REPO_SLUG", "")


def get_ci_vars():
    reponame_a = os.getenv("APPVEYOR_REPO_NAME", "")
    repobranch_a = os.getenv("APPVEYOR_REPO_BRANCH", "")

    reponame_t = os.getenv("TRAVIS_REPO_SLUG", "")
    repobranch_t = os.getenv("TRAVIS_BRANCH", "")

    username, _ = reponame_a.split("/") if reponame_a else reponame_t.split("/")
    channel, version = repobranch_a.split("/") if repobranch_a else repobranch_t.split("/")
    return username, channel, version


def get_env_vars():
    return get_ci_vars() if is_ci_running() else get_default_vars()


def get_os():
    return platform.system().replace("Darwin", "Macos")


def _is_valid_abi(build):
    compiler = build.settings['compiler']
    version = build.settings['compiler.version']
    libcxx = build.settings['compiler.libcxx']
    if compiler == 'gcc' and float(version) > 5:
        return libcxx == 'libstdc++11'
    return True


def _fix_clang_abi(build):
    compiler = build.settings['compiler']
    libcxx = build.settings['compiler.libcxx']
    if compiler == 'clang' and libcxx == 'libstdc++':
        build.settings['compiler.libcxx'] = 'libstdc++11'
    return build


def _filtered_builds(builder):
    builds = filter(_is_valid_abi, builder.builds)
    builds = map(_fix_clang_abi, builds)
    return builds


if __name__ == "__main__":
    name = get_name_from_recipe()
    username, channel, version = get_env_vars()
    reference = "{0}/{1}".format(name, version)
    upload = "https://api.bintray.com/conan/{0}/public-conan".format(username)

    builder = ConanMultiPackager(
        username=username,
        channel=channel,
        reference=reference,
        upload=upload,
        remotes=upload,  # while redundant, this moves bincrafters remote to position 0
        upload_only_when_stable=True,
        stable_branch_pattern="stable/*")

    builder.add_common_builds(shared_option_name=name + ":shared", pure_c=False)

    if get_os() == "Linux":
        builder.builds = _filtered_builds(builder)

    builder.run()
