#!/usr/bin/env python
# -*- coding: utf-8 -*-

# pylint: disable=missing-docstring,invalid-name
from multiprocessing import cpu_count
from conans import ConanFile, tools
from conans.errors import ConanException
import os


class BotanConan(ConanFile):
    name = 'Botan'
    version = '2.1.0'
    url = "https://github.com/bincrafters/conan-botan"
    license = "https://github.com/randombit/botan/blob/master/license.txt"
    description = "Botan is a cryptography library written in C++11."
    settings = (
        'os',
        'arch',
        'compiler',
        'build_type'
    )
    options = {
        'amalgamation': [True, False],
        'bzip2': [True, False],
        'debug_info': [True, False],
        'openssl': [True, False],
        'quiet':   [True, False],
        'shared': [True, False],
        'single_amalgamation': [True, False],
        'sqlite3': [True, False],
        'zlib': [True, False],
    }
    default_options = (
        'amalgamation=True',
        'bzip2=False',
        'debug_info=False',
        'openssl=False',
        'quiet=True',
        'shared=True',
        'single_amalgamation=False',
        'sqlite3=False',
        'zlib=False',
    )

    def requirements(self):
        if self.options.bzip2:
            self.requires('bzip2/[>=1.0]@conan/stable')
        if self.options.openssl:
            self.requires('OpenSSL/[>=1.0.2m]@conan/stable')
        if self.options.zlib:
            self.requires('zlib/[>=1.2]@conan/stable')
        if self.options.sqlite3:
            self.requires('sqlite3/[>=3.18]@bincrafters/stable')

    def config_options_settings(self):
        if self.settings.os == 'Linux':
            self.check_cxx_abi_settings()

    def source(self):
        source_url = "https://github.com/randombit/botan"
        tools.get("{0}/archive/{1}.tar.gz".format(source_url, self.version))
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir.lower(), "sources")

    def build(self):
        with tools.chdir('sources'):
            configure_cmd = self.create_configure_cmd()
            self.output.info('Running command: ' + configure_cmd)
            self.run(configure_cmd)

            make_cmd = self.create_make_cmd()
            self.output.info('Running command: ' + make_cmd)
            self.run(make_cmd)

    def package(self):
        with tools.chdir("sources"):
            self.copy(pattern="license.txt")
            self.output.info('Files are copied via make/pkg-config')
            make_install_cmd = self.get_make_install_cmd()
            self.output.info('Running command: ' + make_install_cmd)
            self.run(make_install_cmd)

        if self.options.shared and self.settings.os != 'Windows':
            with tools.chdir(self.package_folder + '/lib'):
                self.run('rm libbotan-2.a')

    def package_info(self):
        # Can't use self.collect_libs() because we used
        # pkg-config to populate the package directory.

        if self.settings.os == 'Windows':
            if self.settings.build_type == 'Debug':
                self.cpp_info.libs = ['botand']
            else:
                self.cpp_info.libs = ['botan']
        else:
            self.cpp_info.libs = ['botan-2', 'dl']
            if self.settings.os == 'Linux':
                self.cpp_info.libs.append('rt')
            if self.settings.os == 'Macos':
                self.cpp_info.exelinkflags = ['-framework Security']
            if not self.options.shared:
                self.cpp_info.libs.append('pthread')

        self.cpp_info.bindirs = [
            'lib',
            'bin'
        ]
        self.cpp_info.libdirs = [
            'lib'
        ]
        self.cpp_info.includedirs = [
            'include/botan-2'
        ]

    def create_configure_cmd(self):
        if self.settings.compiler in ('clang', 'apple-clang'):
            botan_compiler = 'clang'
        elif self.settings.compiler == 'gcc':
            botan_compiler = 'gcc'
        else:
            botan_compiler = 'msvc'

        is_linux_clang_libcxx = (
            self.settings.os == 'Linux' and
            self.settings.compiler == 'clang' and
            self.settings.compiler.libcxx == 'libc++'
        )

        botan_abi_flags = []

        if is_linux_clang_libcxx:
            botan_abi_flags.extend(["-stdlib=libc++", "-lc++abi"])

        if botan_compiler in ['clang', 'apple-clang', 'gcc']:
            if self.settings.arch == "x86":
                botan_abi_flags.append('-m32')
            elif self.settings.arch == "x86_64":
                botan_abi_flags.append('-m64')

        botan_abi = ' '.join(botan_abi_flags) if botan_abi_flags else ' '

        if self.options.single_amalgamation:
            self.options.amalgamation = True

        botan_amalgamation = (
            '--amalgamation' if self.options.amalgamation
            else ''
        )
        botan_single_amalgamation = (
            '--single-amalgamation-file' if self.options.single_amalgamation
            else ''
        )
        botan_bzip2 = (
            '--with-bzip2' if self.options.bzip2
            else ''
        )
        botan_debug_info = (
            '--with-debug-info' if self.options.debug_info
            else ''
        )
        botan_debug_mode = (
            '--debug-mode' if str(self.settings.build_type).lower() == 'debug'
            else ''
        )
        botan_openssl = (
            '--with-openssl' if self.options.openssl
            else ''
        )
        botan_quiet = (
            '--quiet' if self.options.quiet
            else ''
        )
        botan_shared = (
            '' if self.options.shared
            else '--disable-shared'
        )
        botan_sqlite3 = (
            '--with-sqlite3' if self.options.sqlite3
            else ''
        )
        botan_zlib = (
            '--with-zlib' if self.options.zlib
            else ''
        )
        call_python = (
            'python' if self.settings.os == 'Windows'
            else ''
        )

        configure_cmd = ('{python_call} ./configure.py'
                         ' --cc-abi-flags="{abi}"'
                         ' --cc={compiler}'
                         ' --cpu={cpu}'
                         ' --distribution-info="Conan"'
                         ' --prefix={prefix}'
                         ' {amalgamation}'
                         ' {single_amalgamation}'
                         ' {bzip2}'
                         ' {debug_info}'
                         ' {debug_mode}'
                         ' {openssl}'
                         ' {quiet}'
                         ' {shared}'
                         ' {sqlite3}'
                         ' {zlib}').format(
                          python_call=call_python,
                          abi=botan_abi,
                          amalgamation=botan_amalgamation,
                          bzip2=botan_bzip2,
                          compiler=botan_compiler,
                          cpu=self.settings.arch,
                          debug_info=botan_debug_info,
                          debug_mode=botan_debug_mode,
                          openssl=botan_openssl,
                          prefix=self.package_folder,
                          quiet=botan_quiet,
                          shared=botan_shared,
                          single_amalgamation=botan_single_amalgamation,
                          sqlite3=botan_sqlite3,
                          zlib=botan_zlib,
                      )

        return configure_cmd

    def create_make_cmd(self):
        if self.settings.os == 'Windows':
            self.patch_makefile_win()
            make_cmd = self.get_nmake_cmd()
        else:
            make_cmd = self.get_make_cmd()
        return make_cmd

    def check_cxx_abi_settings(self):
        compiler = self.settings.compiler
        version = float(self.settings.compiler.version.value)
        libcxx = compiler.libcxx
        if compiler == 'gcc' and version > 5 and libcxx != 'libstdc++11':
            raise ConanException(
                'Using Botan with GCC > 5 on Linux requires '
                '"compiler.libcxx=libstdc++11"')
        elif compiler == 'clang' and libcxx not in ['libstdc++11', 'libcxx']:
            raise ConanException(
                'Using Botan with Clang on Linux requires either '
                '"compiler.libcxx=libstdc++11" '
                'or '
                '"compiler.libcxx=libcxx"')

    def get_make_cmd(self):
        botan_quiet = (
            '--quiet' if self.options.quiet
            else ''
        )

        is_linux_clang_libcxx = (
            self.settings.os == 'Linux' and
            self.settings.compiler == 'clang' and
            self.settings.compiler.libcxx == 'libc++'
        )

        if is_linux_clang_libcxx:
            make_ldflags = 'LDFLAGS=-lc++abi'
        else:
            make_ldflags = ''

        make_cmd = ('{ldflags}'
                    ' make'
                    ' {quiet}'
                    ' -j{cpucount} 1>&1').format(
                        ldflags=make_ldflags,
                        quiet=botan_quiet,
                        cpucount=cpu_count()
                    )
        return make_cmd

    def get_nmake_cmd(self):
        vcvars = tools.vcvars_command(self.settings)
        make_cmd = vcvars + ' && nmake'
        return make_cmd

    def patch_makefile_win(self):
        # Todo: Remove this patch when fixed in trunk, Botan issue #1297
        tools.replace_in_file("Makefile",
                              r"$(SCRIPTS_DIR)\install.py",
                              r"python $(SCRIPTS_DIR)\install.py")

        # Todo: Remove this patch when fixed in trunk, Botan issue #210
        runtime = str(self.settings.compiler.runtime)

        tools.replace_in_file("Makefile"
                              r"/MD ",
                              r"/{runtime} ".format(runtime=runtime))

        tools.replace_in_file("Makefile",
                              r"/MDd ",
                              r"/{runtime} ".format(runtime=runtime))

    def get_make_install_cmd(self):
        if self.settings.os == 'Windows':
            vcvars = tools.vcvars_command(self.settings)
            make_install_cmd = vcvars + ' && nmake install'
        else:
            make_install_cmd = 'make install'
        return make_install_cmd
