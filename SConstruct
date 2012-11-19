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

######################
# Shared Directories #
######################

try:
  gini_home = os.environ['GINI_HOME']
except KeyError:
  print "ERROR! The GINI_HOME environment variable not set."
  print "Set GINI_HOME and rerun the installation script."
  Exit(1)
Export('gini_home')

src_dir = os.getcwd()

prefix = ARGUMENTS.get('PREFIX',src_dir)
try:
  prefix = os.environ['PREFIX']
except KeyError:
  pass

build_dir = src_dir + "/build"

etc_dir = prefix + "/etc"
bin_dir = prefix + "/bin"
share_dir = prefix + "/share"

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

env.Install(bin_dir, grouter)
env.Install(share_dir + '/grouter/helpdefs', Glob(grouter_include + '/helpdefs/*'))

env.Alias('install-grouter',bin_dir + '/grouter')
env.Alias('install-grouter',share_dir + '/grouter/helpdefs')
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

env.Install(bin_dir, uswitch)

env.Alias('install-uswitch',bin_dir + '/uswitch')
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


env.Install(bin_dir, gwcenter)
env.Command(bin_dir + '/gwcenter.sh', wgini_dir + '/gwcenter.sh', "cp $SOURCE $TARGET; chmod a+x $TARGET")

env.Alias('install-wgini',bin_dir + "/gwcenter")
env.Alias('install','install-wgini')

###########
# Gloader #
###########

gloader_dir = backend_dir + "/src/gloader" 
gloader_conf = gloader_dir + "/gloader.dtd"

env.Install(etc_dir, gloader_conf)

result = env.Install(share_dir + '/gloader', Glob(gloader_dir + "/*.py"))
env.AddPostAction(share_dir + "/gloader/gloader.py", Chmod(share_dir + "/gloader/gloader.py", 0755))
env.AddPostAction(share_dir + "/gloader/gserver.py", Chmod(share_dir + "/gloader/gserver.py", 0755))

env.SymLink(bin_dir + '/gloader', share_dir + '/gloader/gloader.py')

env.SymLink(bin_dir + '/gserver', share_dir + '/gloader/gserver.py')

env.Alias('install-gloader', share_dir + '/gloader')
env.Alias('install-gloader', bin_dir + '/gloader')
env.Alias('install-gloader', bin_dir + '/gserver')
env.Alias('install-gloader', etc_dir + '/gloader.dtd')
env.Alias('install','install-gloader')

##########
# Kernel #
##########

kernel_dir = backend_dir + "/kernel"
kernel = kernel_dir + "/linux-2.6.26.1"
alt_kernel = kernel_dir + "/linux-2.6.25.10" 

# Copy kernel and glinux loader into bin and set executable
env.Command(bin_dir + '/glinux', kernel_dir + '/glinux', "cp $SOURCE $TARGET; chmod a+x $TARGET")
env.Command(bin_dir + '/linux-2.6.26.1', kernel, "cp $SOURCE $TARGET; chmod a+x $TARGET")

env.Alias('install-kernel', bin_dir + '/glinux')
env.Alias('install-kernel', bin_dir + '/linux-2.6.26.1')
env.Alias('install','install-kernel')

##############
# FileSystem #
##############

filesystem_dir = backend_dir + "/fs"

filesystem_src = filesystem_dir + "/GiniLinux-fs-1.0q.gz"

# Unzip the gini UML fs into the root gini directory
# TODO move this somewhere sensical
env.Command(prefix + '/root_fs_beta2', filesystem_src, "gzip -cd $SOURCE > $TARGET")

env.Alias('install-filesystem',prefix + '/root_fs_beta2')
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
    dlls = env.Install(bin_dir, Glob(frontend_dir + "/bin/*"))
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

env.Install(share_dir + '/gbuilder', gbuilder_dir + '/gbuilder.py')

# Install each of the gbuilder folders
for x in gbuilder_folders:
  env.Install(share_dir + '/gbuilder/' + x, Glob(gbuilder_dir + "/" + x + "/*.py"))

# Install images
env.Install(share_dir + '/gbuilder/images/', Glob(gbuilder_images))

if env['PLATFORM'] != 'win32':
    env.SymLink(bin_dir + '/gbuilder', share_dir + '/gbuilder/gbuilder.py')
    env.Alias('install-gbuilder', bin_dir + '/gbuilder')
env.Alias('install-gbuilder', share_dir + '/gbuilder')
env.Alias('install', 'install-gbuilder')
