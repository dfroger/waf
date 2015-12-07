import platform
from os.path import join

from waflib import Task
from waflib.TaskGen import after, feature

"""
Modify install name of library, or its dependant library install names

A library <foo> provided by a package manager may not have the correct install
name. When linking <bar> with <foo>, we may want to change the dependent
install name of <foo> in <bar>.
"""

class install_name_change(Task.Task):
    color = 'YELLOW'
    run_str = '${INSTALL_NAME_TOOL} -change ${OLDNAME} ${NEWNAME} ${SRC}'

def options(opt):
    pass

def configure(conf):
    if platform.system() == 'Darwin':
        conf.find_program('install_name_tool')

@after('apply_vnum')
@feature('cxxshlib')
def set_install_name(self):
    if platform.system() == 'Darwin' and hasattr(self,'install_name_dir'):
        install_name = join(self.install_name_dir, self.link_task.outputs[0].name)
        self.env.append_value('LINKFLAGS', ['-install_name', install_name])

@feature('cxxprogram')
@feature('cxxshlib')
@feature('cprogram')
@feature('cshlib')
def changing_install_names(self):
    if platform.system() == 'Darwin' and hasattr(self,'install_name_changes'):
        for oldname, newname in self.install_name_changes.iteritems():
            tsk = self.create_task('install_name_change', self.link_task.outputs[0])
            tsk.env.OLDNAME = oldname
            tsk.env.NEWNAME = newname
