#!/usr/bin/env python
# -*- coding: utf-8 -*-

# pylint: disable=missing-docstring,invalid-name
from multiprocessing import cpu_count
from conans import ConanFile, tools
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

    def source(self):
        source_url = "https://github.com/randombit/botan"
        tools.get("{0}/archive/{1}.tar.gz".format(source_url, self.version))
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, "sources")
        
    # pylint: disable=too-many-locals
    def build(self):
        conan_arch = self.settings.arch
        conan_compiler = self.settings.compiler
        conan_os = self.settings.os
        if conan_os != 'Windows':
            conan_libcxx = conan_compiler.libcxx
        conan_build_type = self.settings.build_type

        if conan_compiler in ('clang', 'apple-clang'):
            botan_compiler = 'clang'
        elif conan_compiler == 'gcc':
            botan_compiler = 'gcc'
        else:
            botan_compiler = 'msvc'

        if conan_arch == 'x86':
            botan_cpu = 'x86'
        else:
            botan_cpu = 'x86_64'

        is_linux_clang_libcxx = (
            conan_os == 'Linux' and
            conan_compiler == 'clang' and
            conan_libcxx == 'libc++'
        )

        if is_linux_clang_libcxx:
            make_ldflags = 'LDFLAGS=-lc++abi'
        else:
            make_ldflags = ''

        if self.options.single_amalgamation:
            self.options.amalgamation = True

        botan_abi = (
            '-stdlib=libc++ -lc++abi' if is_linux_clang_libcxx
            else ''
        )
        botan_amalgamation = (
            '--amalgamation' if self.options.amalgamation
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
            '--debug-mode' if str(conan_build_type).lower() == 'debug'
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
        botan_single_amalgamation = (
            '--single-amalgamation-file' if self.options.single_amalgamation
            else ''
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
            'python' if conan_os == 'Windows'
            else ''
        )
        self.run(('cd sources &&'
                  '{python_call} ./configure.py'
                  ' --cc-abi-flags="{abi}"'
                  ' --cc={compiler}'
                  ' --cpu={cpu}'
                  ' --distribution-info="Conan"'
                  ' --prefix={prefix}'
                  ' {amalgamation}'
                  ' {bzip2}'
                  ' {debug_info}'
                  ' {debug_mode}'
                  ' {openssl}'
                  ' {quiet}'
                  ' {shared}'
                  ' {sqlite3}'
                  ' {zlib}').format(**{
                      'python_call': call_python,
                      'abi': botan_abi,
                      'amalgamation': botan_amalgamation,
                      'bzip2': botan_bzip2,
                      'compiler': botan_compiler,
                      'cpu': botan_cpu,
                      'debug_info': botan_debug_info,
                      'debug_mode': botan_debug_mode,
                      'openssl': botan_openssl,
                      'prefix': self.package_folder,
                      'quiet': botan_quiet,
                      'shared': botan_shared,
                      'single_amalgamation': botan_single_amalgamation,
                      'sqlite3': botan_sqlite3,
                      'zlib': botan_zlib,
                  }))

        if conan_os != 'Windows':
            self.run(('cd sources &&'
                      ' {ldflags}'
                      ' make'
                      ' {quiet}'
                      ' -j{cpucount} 1>&1').format(**{
                        'cpucount': cpu_count(),
                        'ldflags': make_ldflags,
                        'quiet': botan_quiet,
                    }))
            self.run(('cd sources &&'
                  ' make install'))
        else:
            self.run(('cd sources &&'
                      ' nmake'))
            self.run(('cd sources &&'
                  ' nmake install'))

    def package(self):
        self.copy(pattern="LICENSE")
        self.copy(pattern="*", dst="include", src="include")
        self.copy(pattern="*.dll", dst="bin", src="bin", keep_path=False)
        self.copy(pattern="*.lib", dst="lib", src="lib", keep_path=False)
        self.copy(pattern="*.a", dst="lib", src="lib", keep_path=False)
        self.copy(pattern="*.so*", dst="lib", src="lib", keep_path=False)
        self.copy(pattern="*.dylib", dst="lib", src="lib", keep_path=False)

    def package_info(self):
        if self.settings.os != 'Windows':
            self.cpp_info.libs = ['botan-2', 'dl']
        else:
            self.cpp_info.libs = ['botan']
        if self.settings.os == 'Linux':
            self.cpp_info.libs.append('rt')
        if not self.options.shared:
            self.cpp_info.libs.append('pthread')
        self.cpp_info.libdirs = [
            'lib'
        ]
        self.cpp_info.includedirs = [
            'include/botan-2'
        ]

