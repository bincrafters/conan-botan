#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from multiprocessing import cpu_count
from conans import ConanFile, tools
from conans.errors import ConanException, ConanInvalidConfiguration
from conans.model.version import Version

class BotanConan(ConanFile):
    name = 'botan'
    version = '2.9.0'
    url = "https://github.com/bincrafters/conan-botan"
    homepage = "https://github.com/randombit/botan"
    author = "Bincrafters <bincrafters@gmail.com>"
    license = "BSD 2-clause"
    exports = ["LICENSE.md"]
    description = "Botan is a cryptography library written in C++11."
    settings = 'os', 'arch', 'compiler', 'build_type'
    options = {
        'amalgamation': [True, False],
        'bzip2': [True, False],
        'debug_info': [True, False],
        'openssl': [True, False],
        'quiet': [True, False],
        'shared': [True, False],
        'fPIC': [True, False],
        'single_amalgamation': [True, False],
        'sqlite3': [True, False],
        'zlib': [True, False],
    }
    default_options = {'amalgamation': True,
                       'bzip2': False,
                       'debug_info': False,
                       'openssl': False,
                       'quiet': True,
                       'shared': True,
                       'fPIC': True,
                       'single_amalgamation': False,
                       'sqlite3': False,
                       'zlib': False}

    def configure(self):
        if self.settings.os == "Windows" and \
           self.settings.compiler == "Visual Studio" and \
           Version(self.settings.compiler.version.value) < "14":
               raise ConanInvalidConfiguration("Botan doesn't support MSVC < 14")
 
    def requirements(self):
        if self.options.bzip2:
            self.requires('bzip2/1.0.6@conan/stable')
        if self.options.openssl:
            self.requires('OpenSSL/1.0.2o@conan/stable')
        if self.options.zlib:
            self.requires('zlib/1.2.11@conan/stable')
        if self.options.sqlite3:
            self.requires('sqlite3/3.25.3@bincrafters/stable')

    def config_options(self):
        if self.settings.compiler != 'Visual Studio':
            self.check_cxx_abi_settings()

        if self.options.single_amalgamation:
            self.options.amalgamation = True

        if self.settings.os == "Windows":
            del self.options.fPIC

    def source(self):
        tools.get("{0}/archive/{1}.tar.gz".format(self.homepage, self.version))
        extracted_dir = "botan-" + self.version
        os.rename(extracted_dir, "sources")

    def build(self):
        with tools.chdir('sources'):
            self.run(self._configure_cmd)
            self.run(self._make_cmd)

    def package(self):
        self.copy(pattern="license.txt", dst="licenses", src="sources")
        with tools.chdir("sources"):
            self.run(self._make_install_cmd)

    def package_info(self):
        if self.settings.compiler == 'Visual Studio':
            self.cpp_info.libs.append('botan')
        else:
            self.cpp_info.libs.extend(['botan-2'])
            if self.settings.os != 'Windows':
                self.cpp_info.libs.append('dl')
            if self.settings.os == 'Linux':
                self.cpp_info.libs.append('rt')
            if self.settings.os == 'Macos':
                self.cpp_info.exelinkflags = ['-framework Security']
            if not self.options.shared:
                self.cpp_info.libs.append('pthread')
        if self.settings.os == "Windows":
            self.cpp_info.libs.append("ws2_32")

        self.cpp_info.libdirs = ['lib']
        self.cpp_info.bindirs = ['lib', 'bin']
        self.cpp_info.includedirs = ['include/botan-2']

    @property
    def _is_mingw_windows(self):
        return self.settings.os == "Windows" and self.settings.compiler == "gcc" and os.name == "nt"

    @property
    def _botan_os(self):
        if self._is_mingw_windows:
            return "mingw"
        return {"Windows": "windows",
                "Linux": "linux",
                "Macos": "darwin",
                "Android": "linux",
                "iOS": "ios"}.get(str(self.settings.os))

    @property
    def _configure_cmd(self):
        if self.settings.compiler in ('clang', 'apple-clang'):
            botan_compiler = 'clang'
        elif self.settings.compiler == 'gcc':
            botan_compiler = 'gcc'
        else:
            botan_compiler = 'msvc'

        botan_abi_flags = []
        botan_extra_cxx_flags = []

        if self._is_linux_clang_libcxx:
            botan_abi_flags.extend(["-stdlib=libc++", "-lc++abi"])

        if botan_compiler in ['clang', 'apple-clang', 'gcc']:
            if self.settings.arch == "x86":
                botan_abi_flags.append('-m32')
            elif self.settings.arch == "x86_64":
                botan_abi_flags.append('-m64')

        if self.settings.os != "Windows" and self.options.fPIC:
            botan_extra_cxx_flags.append('-fPIC')

        # we're piggy-backing this onto the ABI flags as a workaround:
        # botan's configure script *replaces* it's own standard flags with
        # whatever it gets from --cxxflags. Starting with Botan 2.10 there will
        # be an --extra-cxxflags parameter that solves this.
        # See here for more details:
        #   https://github.com/bincrafters/community/issues/631
        #   https://github.com/randombit/botan/issues/1826
        if botan_extra_cxx_flags:
            botan_abi_flags.extend(botan_extra_cxx_flags)

        botan_abi = ' '.join(botan_abi_flags) if botan_abi_flags else ' '

        build_flags = []

        if self.options.amalgamation:
            build_flags.append('--amalgamation')

        if self.options.single_amalgamation:
            build_flags.append('--single-amalgamation-file')

        if self.options.bzip2:
            build_flags.append('--with-bzip2')

        if self.options.openssl:
            build_flags.append('--with-openssl')

        if self.options.quiet:
            build_flags.append('--quiet')

        if self.options.sqlite3:
            build_flags.append('--with-sqlite3')

        if self.options.zlib:
            build_flags.append('--with-zlib')

        if self.options.debug_info:
            build_flags.append('--with-debug-info')

        if str(self.settings.build_type).lower() == 'debug':
            build_flags.append('--debug-mode')

        if not self.options.shared:
            build_flags.append('--disable-shared')
        if self._is_mingw_windows:
            build_flags.append('--without-stack-protector')

        if self.settings.compiler == 'Visual Studio':
            build_flags.append('--msvc-runtime=%s' % str(self.settings.compiler.runtime))

        call_python = 'python' if self.settings.os == 'Windows' else ''

        prefix = tools.unix_path(self.package_folder) if self._is_mingw_windows else self.package_folder

        configure_cmd = ('{python_call} ./configure.py'
                         ' --distribution-info="Conan"'
                         ' --cc-abi-flags="{abi}"'
                         ' --cc={compiler}'
                         ' --cpu={cpu}'
                         ' --prefix={prefix}'
                         ' --os={os}'
                         ' {build_flags}').format(
                             python_call=call_python,
                             abi=botan_abi,
                             compiler=botan_compiler,
                             cpu=self.settings.arch,
                             prefix=prefix,
                             os=self._botan_os,
                             build_flags=' '.join(build_flags))

        return configure_cmd

    @property
    def _make_cmd(self):
        return self._nmake_cmd if self.settings.compiler == 'Visual Studio' else self._gnumake_cmd

    def check_cxx_abi_settings(self):
        compiler = self.settings.compiler
        version = float(self.settings.compiler.version.value)
        libcxx = compiler.libcxx
        if compiler == 'gcc' and version > 5 and libcxx != 'libstdc++11':
            raise ConanException(
                'Using Botan with GCC > 5 on Linux requires '
                '"compiler.libcxx=libstdc++11"')
        elif compiler == 'clang' and libcxx not in ['libstdc++11', 'libc++']:
            raise ConanException(
                'Using Botan with Clang on Linux requires either '
                '"compiler.libcxx=libstdc++11" '
                'or '
                '"compiler.libcxx=libc++"')

    @property
    def _make_program(self):
        return tools.get_env("CONAN_MAKE_PROGRAM", tools.which("make") or tools.which('mingw32-make'))

    @property
    def _gnumake_cmd(self):
        make_ldflags = 'LDFLAGS=-lc++abi' if self._is_linux_clang_libcxx else ''

        botan_quiet = '--quiet' if self.options.quiet else ''

        make_cmd = ('{ldflags}'
                    ' {make}'
                    ' {quiet}'
                    ' -j{cpucount}').format(
                        ldflags=make_ldflags,
                        make=self._make_program,
                        quiet=botan_quiet,
                        cpucount=cpu_count())
        return make_cmd

    @property
    def _nmake_cmd(self):
        vcvars = tools.vcvars_command(self.settings)
        make_cmd = vcvars + ' && nmake'
        return make_cmd

    @property
    def _make_install_cmd(self):
        if self.settings.compiler == 'Visual Studio':
            vcvars = tools.vcvars_command(self.settings)
            make_install_cmd = vcvars + ' && nmake install'
        else:
            make_install_cmd = '{make} install'.format(make=self._make_program)
        return make_install_cmd

    @property
    def _is_linux_clang_libcxx(self):
        return (
            self.settings.os == 'Linux' and
            self.settings.compiler == 'clang' and
            self.settings.compiler.libcxx == 'libc++'
        )
