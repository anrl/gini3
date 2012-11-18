# -*- python -*-
#
# GINI Version 2.0
# (C) Copyright 2009, McGill University
#
# Scons compile script for creating GINI installation
#
import os.path
import sys
from SCons.Node import FS

#import SconsBuilder

try:
  gini_home = os.environ['GINI_HOME']
except KeyError:
  print "ERROR! The GINI_HOME environment variable not set."
  print "Set GINI_HOME and rerun the installation script."
  Exit(1)
Export('gini_home')

#gini_src = os.getcwd()
#Export('gini_src')

###############
# Environment #
###############

env = Environment()

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

backend_dir = gini_home + "/backend/"

###########
# grouter #
###########

grouter_include = gini_home + '/backend/include'
grouter_dir = gini_home + '/backend/src/grouter/'
grouter_build_dir = gini_home + 'build/release/grouter'

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

env.Install(gini_home + '/bin', grouter)
env.Install(gini_home + '/share/grouter', grouter_include + '/helpdefs')

###########
# uswitch #
###########

uswitch_include = gini_home + '/backend/include/uswitch'
uswitch_dir = gini_home + '/backend/src/uswitch/'
uswitch_build_dir = gini_home + '/build/release/uswitch'

VariantDir(uswitch_build_dir, uswitch_dir, duplicate=0)

uswitch_env = Environment(CPPPATH=uswitch_include)

uswitch = uswitch_env.Program("uswitch", Glob(uswitch_build_dir + "/*.c"))

env.Install(gini_home + '/bin', uswitch)

#########
# wgini #
#########

wgini_include = gini_home + '/backend/include/wgini'
wgini_dir = gini_home + '/backend/src/wgini/'
wgini_build_dir = gini_home + '/build/release/wgini'

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


env.Install(gini_home + '/bin', gwcenter)
env.Command(gini_home + '/bin/gwcenter.sh', wgini_dir + 'gwcenter.sh', "cp $SOURCE $TARGET; chmod a+x $TARGET")

###########
# Gloader #
###########

gloader_dir = backend_dir + "src/gloader/" 
gloader_conf = gloader_dir + "gloader.dtd"

env.Install(gini_home + '/etc', gloader_conf)
env.Alias('install', gini_home + '/etc')

env.Install(gini_home + '/share/gloader', Glob(gloader_dir + "*.py"))
env.Alias('install', gini_home + '/share/gloader')

env.SymLink(gini_home + '/bin/gloader', gini_home + '/share/gloader/gloader.py')
env.Command(None, gini_home + '/share/gloader/gloader.py', Chmod("$SOURCE", 0755))

env.SymLink(gini_home + '/bin/gserver', gini_home + '/share/gloader/gserver.py')
env.Command(None, gini_home + '/share/gloader/gserver.py', Chmod("$SOURCE", 0755))

##########
# Kernel #
##########

kernel_dir = backend_dir + "kernel/"
kernel = kernel_dir + "linux-2.6.26.1"
alt_kernel = kernel_dir + "linux-2.6.25.10" 

# Copy kernel and glinux loader into bin and set executable
env.Command(gini_home + '/bin/glinux', kernel_dir + 'glinux', "cp $SOURCE $TARGET; chmod a+x $TARGET")
env.Command(gini_home + '/bin/linux-2.6.26.1', kernel, "cp $SOURCE $TARGET; chmod a+x $TARGET")

env.Alias('install', gini_home + '/bin')

##############
# FileSystem #
##############

filesystem_dir = backend_dir + "fs/"

filesystem_src = filesystem_dir + "GiniLinux-fs-1.0q.gz"

# Unzip the gini UML fs into the root gini directory
# TODO move this somewhere sensical
env.Command(gini_home + '/root_fs_beta2', filesystem_src, "gzip -cd $SOURCE > $TARGET")

############
# Frontend #
############

frontend_dir = "frontend/"

faq = 'doc/FAQ.html'

env.Execute(Mkdir(gini_home + "/tmp"))
env.Execute(Mkdir(gini_home + "/sav"))
env.Execute(Mkdir(gini_home + "/etc"))
if env['PLATFORM'] == 'win32':
    env.Install(gini_home + '/bin', Glob(frontend_dir + "bin/*"))
env.Install(gini_home + '/doc', frontend_dir + faq)
env.Alias('install', gini_home)

############
# GBuilder #
############

gbuilder_dir = frontend_dir + "src/gbuilder/"

gbuilder_folders = Split("""
    Core
    Devices
    Network
    UI""")

gbuilder_images = gbuilder_dir + "images/*"

env.Install(gini_home + '/share/gbuilder', gbuilder_dir + 'gbuilder.py')

# Install each of the gbuilder folders
for x in gbuilder_folders:
  env.Install(gini_home + '/share/gbuilder/' + x, Glob(gbuilder_dir + x + "/*.py"))

# Install images
env.Install(gini_home + '/share/gbuilder/images/', Glob(gbuilder_images))

if env['PLATFORM'] != 'win32':
    env.SymLink(gini_home + '/bin/gbuilder', gini_home + '/share/gbuilder/gbuilder.py')
env.Alias('install', gini_home + '/share/gbuilder')

