import unittest
import os
import shutil
from subprocess import check_call, check_output, Popen, PIPE, STDOUT, CalledProcessError

class TestInstallName(unittest.TestCase):

    def workdir(self, path=None):
        if path:
            return os.path.join('workdir', self._testMethodName, path)
        else:
            return os.path.join('workdir', self._testMethodName)

    def simulate_system_library(self):
        """
        Simulate a 'libfoo.dylib' system library.

        We do not really put the library in a system directory, but instead in the
        directory from where we run executable, so it will be loaded by default by
        the executable, as if it was a system library.
        """

        self.run_log(['clang++', '-o', 'libfoo.dylib', '-shared', 'foo-system.cxx'])

    def simulate_pkg_manager_library(self):
        """
        Simulate a 'libfoo.dylib' library installed by a package manager.

        The directory ./pkg-manager simulate where the package manager install
        library.

        Install name is 'libfoo.dylib', so when running the 'demo'
        executable, the system library is used instead of this one.

        There are 3 ways to fix the problem:
          - modify the install name in the libfoo.dylib file.
          - set DYLD_LIBRARY_PATH when running 'demo' executable.
          - modify the dependant install name of foo in the 'demo' file.

        The want to use the last solution.
        """

        self.run_log(['clang++', '-o', 'libfoo.dylib', '-shared', 'foo-pkg-manager.cxx'],
                      cwd=self.workdir('pkg-manager'))

    def run_log(self, args, cwd=None):
        if cwd == None:
            cwd = self.workdir()
        p = Popen(args, stdout=PIPE, stderr=STDOUT, cwd=cwd)
        output = p.communicate()[0]
        with open(self.workdir('log'), 'a') as f:
            f.write('='*80+'\n')
            f.write(' '.join(args)+'\n')
            f.write('='*80+'\n')
            f.write('\n\n')
            f.write(output)
            f.write('\n\n')
        if p.returncode != 0:
            raise RuntimeError('Command failed: %s' % ' '.join(args))
        return output

    def waf(self, cmd):
        args = ['waf',] + cmd.split() + ['--prefix=install', '--out=build']
        self.run_log(args)

    def run_demo(self):
        return self.run_log(['./install/bin/demo',])

    def setUp(self):
        os.mkdir(self.workdir())
        for f in ['demo.cxx', 'wscript', 'foo-system.cxx', 'install_name.py']:
            shutil.copy(f, self.workdir())
        for t in ['foo', 'pkg-manager']:
            shutil.copytree(t, self.workdir(t))
        self.simulate_system_library()
        self.simulate_pkg_manager_library()

    @classmethod
    def setUpClass(cls):
        if os.path.isdir('workdir'):
            shutil.rmtree('workdir')
        os.mkdir('workdir')

    @classmethod
    def tearDownClass(cls):
        if os.path.isfile('libfoo.dylib'):
            os.remove('libfoo.dylib')
        if os.path.isfile('pkg-manager/libfoo.dylib'):
            os.remove('pkg-manager/libfoo.dylib')

    def test_system_lib(self):
        self.waf('configure build install --which-foo=system')
        self.waf('clean')
        output = self.run_demo()
        self.assertEqual(output, 'foo system\n')

    def test_pkg_manager_lib(self):
        self.waf('configure build install --which-foo=pkg-manager --use-install-name')
        self.waf('clean')
        output = self.run_demo()
        self.assertEqual(output, 'foo pkg-manager\n')

    def test_pkg_manager_but_system(self):
        self.waf('configure build install --which-foo=pkg-manager')
        self.waf('clean')
        output = self.run_demo()
        self.assertEqual(output, 'foo system\n')

    def test_build_lib(self):
        self.waf('configure build install --which-foo=build --use-install-name')
        self.waf('clean')
        output = self.run_demo()
        self.assertEqual(output, 'foo build\n')

    def test_build_lib_not_found(self):
        self.waf('configure build install --which-foo=build')
        self.waf('clean')
        #TODO: assertRaisesRegexp
        with self.assertRaises(RuntimeError):
            output = self.run_demo()

    def test_build_lib_rebuild(self):
        self.waf('configure build --which-foo=build --use-install-name')
        os.remove(self.workdir('build/foo/libfoo.dylib'))
        self.waf('configure build install --which-foo=build --use-install-name')
        self.waf('clean')
        output = self.run_demo()
        self.assertEqual(output, 'foo build\n')

if __name__ == '__main__':
    unittest.main()
