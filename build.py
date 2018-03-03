# -*- coding: utf-8 -*-

from bincrafters import build_template_default

if __name__ == "__main__":

    builder = build_template_default.get_builder(pure_c=False)

    filtered_builds = []
    for settings, options, env_vars, build_requires, reference in builder.items:
        if settings['compiler'] == 'gcc' or settings['compiler'] == 'clang':
            if settings['compiler.libcxx'] == 'libstdc++11' or settings['compiler.libcxx'] == 'libc++':
                filtered_builds.append([settings, options, env_vars, build_requires])
        else:
            filtered_builds.append([settings, options, env_vars, build_requires])
    builder.builds = filtered_builds

    builder.run()

