#!python
import os
import re

def unitTestAction(target, source, env):
        '''
        Action for a 'UnitTest' builder object.
        Runs the supplied executable, reporting failure to scons via the test exit
        status.
        When the test succeeds, the file target.passed is created to indicate that
        the test was successful and doesn't need running again unless dependencies
        change.
        '''
        app = str(source[0].abspath)
        if os.spawnle(os.P_WAIT, app, env['ENV'])==0:
                open(str(target[0]),'w').write("PASSED\n")
        else:
                return 1

def unitTestActionString(target, source, env):
        '''
        Return output string which will be seen when running unit tests.
        '''
        return 'Running tests in ' + str(source[0])

def addUnitTest(env, target, source, *args, **kwargs):
        '''
        Add a unit test
        Parameters:
                target - If the target parameter is present, it is the name of the test
                                executable
                source - list of source files to create the test executable.
                any additional parameters are passed along directly to env.Program().
        Returns:
                The scons node for the unit test.
        Any additional files listed in the env['UTEST_MAIN_SRC'] build variable are
        also included in the source list.
        All tests added with addUnitTest can be run with the test alias:
                "scons test"
        Any test can be run in isolation from other tests, using the name of the
        test executable provided in the target parameter:
                "scons target"
        '''
        program = env.Program(target, source, *args, **kwargs)
        utest = env.UnitTest(program)
        # add alias to run all unit tests.
        env.Alias('test', utest)
        # make an alias to run the test in isolation from the rest of the tests.
        env.Alias(str(program[0]), utest)
        return utest

def addAllTests(env, test_dir, under_test_dir, ignore=[], *args, **kwargs):
    test_files = env.Glob(test_dir + "/*_t.c")
    under_test = filter(lambda f: os.path.basename(f.path) not in ignore, env.Glob(under_test_dir + "/*.c"))
    for t in test_files:
        target = re.sub('\_t.c', '_test', t.path)
        src = under_test + [t]
        env.addUnitTest(target, src, *args, **kwargs)

#-------------------------------------------------------------------------------
# Functions used to initialize the unit test tool.
def generate(env, LIBS=[]):
        env['BUILDERS']['UnitTest'] = env.Builder(
                        action = env.Action(unitTestAction, unitTestActionString),
                        suffix='.passed')
        env.AppendUnique(LIBS=LIBS)
        env.AddMethod(addUnitTest, "addUnitTest")
        env.AddMethod(addAllTests, "addAllTests")
        env.AlwaysBuild('test')

def exists(env):
        return 1
