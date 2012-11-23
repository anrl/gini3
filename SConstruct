# -*- python -*-
#
# GINI Version 2.0
# (C) Copyright 2009, McGill University
#
# Scons compile script for creating GINI installation
#
import os.path,stat
import sys
from SCons.Node import FS

#import SconsBuilder

######################
# Shared Directories #
######################

# try:
#   gini_home = os.environ['GINI_HOME']
# except KeyError:
#   print "ERROR! The GINI_HOME environment variable not set."
#   print "Set GINI_HOME and rerun the installation script."
#   Exit(1)
# Export('gini_home')

src_dir = os.getcwd()

prefix = ARGUMENTS.get('PREFIX',"")
prefix = os.path.realpath(ARGUMENTS.get('DESTDIR',src_dir)) + prefix

build_dir = src_dir + "/build"

etcdir = prefix + "/etc"
bindir = prefix + "/bin"
sharedir = prefix + "/share"

#gini_src = os.getcwd()
#Export('gini_src')

###############
# Environment #
###############

env = Environment()

##################
# helper methods #
##################

def post_chmod(target):
  env.AddPostAction(target, "chmod +x " + target)

#####################
# Source Generators #
#####################

def gen_environment_file(target,source,env):
  output_file = open(target[0].abspath,'w')
  output_file.write('#!/usr/bin/python2\n')
  output_file.write('import os,subprocess,sys\n\n')
  output_file.write('previous_dir = os.getcwd()\n')
  output_file.write('os.chdir(os.path.dirname(os.path.realpath(__file__)))\n')
  output_file.write('os.environ["GINI_ROOT"] = os.path.realpath("%s")\n' % os.path.relpath(prefix,bindir))
  output_file.write('os.environ["GINI_SHARE"] = os.path.realpath("%s")\n' % os.path.relpath(sharedir,bindir))
  output_file.write('os.environ["GINI_HOME"] = os.environ["HOME"] + "/.gini"\n') #XXX change when it is set up right
  output_file.write('if not os.path.exists(os.environ["GINI_HOME"] + "/etc"): os.makedirs(os.environ["GINI_HOME"] + "/etc")\n')
  output_file.write('if not os.path.exists(os.environ["GINI_HOME"] + "/sav"): os.makedirs(os.environ["GINI_HOME"] + "/sav")\n')
  output_file.write('if not os.path.exists(os.environ["GINI_HOME"] + "/data"): os.makedirs(os.environ["GINI_HOME"] + "/data")\n')
  output_file.write('if not os.path.exists(os.environ["GINI_HOME"] + "/tmp"): os.makedirs(os.environ["GINI_HOME"] + "/tmp")\n')
  output_file.write('params = [os.path.realpath("%s")]\n' % os.path.relpath(source[0].abspath,bindir))
  output_file.write('if len(sys.argv) > 1: params.extend(sys.argv[1:])\n')
  output_file.write('os.chdir(previous_dir)\n')
  output_file.write('os.execv(params[0],params)\n')
  return None

gen_environment_file_builder = Builder(action=gen_environment_file, single_target = True, single_source = True, target_factory = FS.File, source_factory = FS.File)

def gen_python_path_file(target,source,env):
  output_file = open(target[0].abspath,'w')
  output_file.write('import os\n')
  output_file.write('GINI_ROOT = "%s"\n' % prefix)
  #if env['PLATFORM'] != 'win32': 
    #output_file.write('GINI_HOME = os.environ["HOME"] + "/.gini"\n')
  #else:
    #output_file.write('GINI_HOME = os.environ["USERPROFILE"] + "/gini_files"\n')
  output_file.write('GINI_HOME = "%s"\n'% prefix)
  output_file.close()
  return None

gen_python_path_builder = Builder(action=gen_python_path_file,
  single_target=True,
  target_factory = FS.File)

env.Append(BUILDERS = {'PythonPathFile':gen_python_path_builder})
env.Append(BUILDERS = {'PythonEnvFile':gen_environment_file_builder})

################
# Symlink Code #
################

def symlink(target, source, env):
  lnk = target[0].abspath
  src = source[0].abspath
  lnkdir,lnkname = os.path.split(lnk)
  srcrel = os.path.relpath(src,lnkdir)

  if int(env.get('verbose',0)) > 4:
    print 'target:', target
    print 'source:', source
    print 'lnk:', lnk
    print 'src:', src
    print 'lnkdir,lnkname:', lnkdir, lnkname
    print 'srcrel:', srcrel

  if int(env.get('verbose',0)) > 4:
    print 'in directory: %s' % os.path.relpath(lnkdir,env.Dir('#').abspath)
    print '    symlink: %s -> %s' % (lnkname,srcrel)

  try:
    os.symlink(srcrel,lnk)
  except AttributeError:
    # no symlink available, so we make a (deep) copy? (or pass)
    #os.copytree(srcrel,lnk)
    print 'no os.symlink capability on this system?'

  return None

def symlink_emitter(target,source,env):
  '''
  This emitter removes the link if the source file name has changed
  since scons does not seem to catch this case.
  '''
  lnk = target[0].abspath
  src = source[0].abspath
  lnkdir,lnkname = os.path.split(lnk)
  srcrel = os.path.relpath(src,lnkdir)

  if int(env.get('verbose',0)) > 3:
    ldir = os.path.relpath(lnkdir,env.Dir('#').abspath)
    if rellnkdir[:2] == '..':
        ldir = os.path.abspath(ldir)
    print '  symbolic link in directory: %s' % ldir
    print '      %s -> %s' % (lnkname,srcrel)

  try:
    if os.path.exists(lnk):
      if os.readlink(lnk) != srcrel:
          os.remove(lnk)
  except AttributeError:
    # no symlink available, so we remove the whole tree? (or pass)
    #os.rmtree(lnk)
    print 'no os.symlink capability on this system?'

  return (target, source)

symlink_builder = Builder(action = symlink,
    target_factory = FS.File,
    source_factory = FS.Entry,
    single_target = True,
    single_source = True,
    emitter = symlink_emitter)

env.Append(BUILDERS = {'SymLink':symlink_builder})

##################
# Library checks #
##################

conf = Configure(env)
if not conf.CheckLib('slack'):
  print 'Did not find libslack.a or slack.lib, exiting!'
  Exit(1)
if not conf.CheckLib('readline'):
  print 'Did not find libreadline.so or readline.lib, exiting!'
  Exit(1)
if not conf.CheckLib('pthread'):
  print 'Did not find libpthread.so or pthread.lib, exiting!'
  Exit(1)
env = conf.Finish()

Export('env')

###########
# Backend #
###########

backend_dir = src_dir + "/backend"

###########
# grouter #
###########

grouter_include = backend_dir + '/include'
grouter_dir = backend_dir + '/src/grouter'
grouter_build_dir = src_dir + '/build/release/grouter'

VariantDir(grouter_build_dir,grouter_dir, duplicate=0)

grouter_env = Environment(CPPPATH=grouter_include)
grouter_env.Append(CFLAGS='-g')
grouter_env.Append(CFLAGS='-DHAVE_PTHREAD_RWLOCK=1')
grouter_env.Append(CFLAGS='-DHAVE_GETOPT_LONG')

# some of the following library dependencies can be removed?
# may be the termcap is not needed anymore..?
# TODO: libslack should be removed.. required routines should be custom compiled

grouter_libs = Split ("""readline
                         termcap
                         slack
                         pthread
                         util
                         m""")

grouter = grouter_env.Program("grouter", Glob(grouter_build_dir + "/*.c"), LIBS=grouter_libs)

env.Install(sharedir + "/grouter/", grouter)
post_chmod(sharedir + "/grouter/grouter")
env.PythonEnvFile(bindir + "/grouter" ,sharedir + "/grouter/grouter")
post_chmod(bindir + "/grouter")

env.Install(sharedir + '/grouter/helpdefs', Glob(grouter_include + '/helpdefs/*'))

env.Alias('install-grouter',bindir + '/grouter')
env.Alias('install-grouter',sharedir + '/grouter/helpdefs')
env.Alias('install','install-grouter')

###########
# uswitch #
###########

uswitch_include = backend_dir + '/include/uswitch'
uswitch_dir = backend_dir + '/src/uswitch'
uswitch_build_dir = src_dir + '/build/release/uswitch'

VariantDir(uswitch_build_dir, uswitch_dir, duplicate=0)

uswitch_env = Environment(CPPPATH=uswitch_include)

uswitch = uswitch_env.Program("uswitch", Glob(uswitch_build_dir + "/*.c"))

env.Install(sharedir + "/uswitch/", uswitch)
post_chmod(sharedir + "/uswitch/uswitch")
env.PythonEnvFile(bindir + "/uswitch" ,sharedir + "/uswitch/uswitch")
post_chmod(bindir + "/uswitch")

env.Alias('install-uswitch',bindir + '/uswitch')
env.Alias('install','install-uswitch')

#########
# wgini #
#########

wgini_include = backend_dir + '/include/wgini'
wgini_dir = backend_dir + '/src/wgini'
wgini_build_dir = src_dir + '/build/release/wgini'

VariantDir(wgini_build_dir,wgini_dir, duplicate=0)

wgini_env = Environment(CPPPATH=wgini_include)
wgini_env.Append(CFLAGS='-DHAVE_PTHREAD_RWLOCK=1')
wgini_env.Append(CFLAGS='-DHAVE_GETOPT_LONG')

# some of the following library dependencies can be removed?
# may be the termcap is not needed anymore..?
# TODO: libslack should be removed.. required routines should be custom compiled
wgini_libs = Split ("""readline
    termcap
    slack
    pthread
    util
    m""")

gwcenter = wgini_env.Program("gwcenter",Glob(wgini_build_dir + "/*.c"), LIBS=wgini_libs)

env.Install(sharedir + "/wgini/", gwcenter)
post_chmod(sharedir + "/wgini/gwcenter")
env.PythonEnvFile(bindir + "/gwcenter" ,sharedir + "/wgini/gwcenter")
post_chmod(bindir + "/gwcenter")

env.Install(sharedir + "/wgini/",wgini_dir + '/gwcenter.sh')
post_chmod(sharedir + "/wgini/")
env.PythonEnvFile(bindir + "/gwcenter.sh", sharedir + "/wgini/gwcenter.sh")
post_chmod(sharedir + "/wgini/gwcenter.sh")

env.Alias('install-wgini',bindir + "/gwcenter")
env.Alias('install','install-wgini')

###########
# Gloader #
###########

gloader_dir = backend_dir + "/src/gloader" 
gloader_conf = gloader_dir + "/gloader.dtd"

env.Install(sharedir + "/gloader/", gloader_conf)

result = env.Install(sharedir + '/gloader', Glob(gloader_dir + "/*.py"))
post_chmod(sharedir + "/gloader/gloader.py")
post_chmod(sharedir + "/gloader/gserver.py")

env.PythonEnvFile(bindir + '/gserver',sharedir + '/gloader/gserver.py')
post_chmod(bindir + '/gserver')
env.PythonEnvFile(bindir + '/gloader',sharedir + "/gloader/gloader.py")
post_chmod(bindir + '/gloader')

env.Alias('install-gloader', sharedir + '/gloader')
env.Alias('install-gloader', bindir + '/gloader')
env.Alias('install-gloader', bindir + '/gserver')
env.Alias('install-gloader', etcdir + '/gloader.dtd')
env.Alias('install','install-gloader')

##########
# Kernel #
##########

kernel_dir = backend_dir + "/kernel"
kernel = kernel_dir + "/linux-2.6.26.1"
alt_kernel = kernel_dir + "/linux-2.6.25.10" 

# Copy kernel and glinux loader into bin and set executable
env.Install(sharedir + '/kernel/',kernel_dir + '/glinux')
post_chmod(sharedir + '/kernel/glinux')
env.PythonEnvFile(bindir + '/glinux',sharedir + '/kernel/glinux')
post_chmod(bindir + '/glinux')

env.Install(sharedir + '/kernel/', kernel_dir + '/linux-2.6.26.1')
post_chmod(sharedir + '/kernel/linux-2.6.26.1')
env.PythonEnvFile(bindir + '/linux-2.6.26.1',sharedir + '/kernel/linux-2.6.26.1')
post_chmod(bindir + '/linux-2.6.26.1')

env.Alias('install-kernel', bindir + '/glinux')
env.Alias('install-kernel', bindir + '/linux-2.6.26.1')
env.Alias('install','install-kernel')

##############
# FileSystem #
##############

filesystem_dir = backend_dir + "/fs"

filesystem_src = filesystem_dir + "/GiniLinux-fs-1.0q.gz"

# Unzip the gini UML fs into the root gini directory
# TODO move this somewhere sensical
env.Command(sharedir + '/filesystem/root_fs_beta2', filesystem_src, "gzip -cd $SOURCE > $TARGET")

env.Alias('install-filesystem',sharedir + '/filesystem/root_fs_beta2')
env.Alias('install','install-filesystem')

############
# Frontend #
############

frontend_dir = src_dir + "/frontend"

faq = '/doc/FAQ.html'

env.Execute(Mkdir(prefix + "/tmp"))
env.Execute(Mkdir(prefix + "/sav"))
env.Execute(Mkdir(prefix + "/etc"))
if env['PLATFORM'] == 'win32':
    dlls = env.Install(bindir, Glob(frontend_dir + "/bin/*"))
    env.Alias('install-windows', dlls)
    env.Alias('install','install-windows')
env.Install(prefix + '/doc', frontend_dir + faq)
env.Alias('install-doc', prefix + '/doc')
env.Alias('install','install-doc')

############
# GBuilder #
############

gbuilder_dir = frontend_dir + "/src/gbuilder"

gbuilder_folders = Split("""
    Core
    Devices
    Network
    UI""")

gbuilder_images = gbuilder_dir + "/images/*"

env.Install(sharedir + '/gbuilder', gbuilder_dir + '/gbuilder.py')

# Install each of the gbuilder folders
for x in gbuilder_folders:
  env.Install(sharedir + '/gbuilder/' + x, Glob(gbuilder_dir + "/" + x + "/*.py"))
post_chmod(sharedir + '/gbuilder/gbuilder.py')
# Install images
env.Install(sharedir + '/gbuilder/images/', Glob(gbuilder_images))

if env['PLATFORM'] != 'win32':
    #env.SymLink(bindir + '/gbuilder', sharedir + '/gbuilder/gbuilder.py')
    env.PythonEnvFile(bindir + '/gbuilder', sharedir + '/gbuilder/gbuilder.py')
    env.AddPostAction(bindir + '/gbuilder', "chmod +x " + bindir + '/gbuilder')
    env.Alias('install-gbuilder', bindir + '/gbuilder')
    # Adding Path info to gbuilder
env.Alias('install-gbuilder', sharedir + '/gbuilder')
env.Alias('install', 'install-gbuilder')
