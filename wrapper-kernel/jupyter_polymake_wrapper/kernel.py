from ipykernel.kernelbase import Kernel
import pexpect
from pexpect import replwrap, EOF, which

from subprocess import check_output
from os import unlink, path

import base64
import imghdr
import re
import signal
import urllib

kernel_object_for_ipython = None  

def _mock_get_ipython():
    global kernel_object_for_ipython
    return kernel_object_for_ipython

try:
    import IPython
    ipython_loaded = True
except ImportError:
    ipython_loaded = False

if ipython_loaded:
    ## Rewrite this incredibly stupid get_ipython method
    get_ipython = _mock_get_ipython
    sys.modules['IPython'].get_ipython = _mock_get_ipython
    sys.modules['IPython'].core.getipython.get_ipython = _mock_get_ipython

try:
    from ipywidgets import *
    ipywidgets_extension_loaded = True
except ImportError:
    ipywidgets_extension_loaded = False

class own_ipython:
    kernel = None
    def __init__(self, kernel = None ):
        self.kernel = kernel

__version__ = '0.3'

version_pat = re.compile(r'version (\d+(\.\d+)+)')

class polymakeKernel(Kernel):
    implementation = 'jupyter_polymake_wrapper'
    implementation_version = __version__

    def _replace_get_ipython(self):
        new_kernel = own_ipython(self)
        global kernel_object_for_ipython
        kernel_object_for_ipython = new_kernel

    @property
    def language_version(self):
        m = version_pat.search(self.banner)
        return m.group(1)

    _banner = None

    @property
    def banner(self):
        if self._banner is None:
            self._banner = "Polymake Jupyter kernel"
        return self._banner

    language_info = {'name': 'polymake',
                     'codemirror_mode': 'polymake', # FIXME: Maybe use pearl?
                     'mimetype': 'text/x-polymake', 
                     'file_extension': '.polymake'} # FIXME: Is this even real?

    def __init__(self, **kwargs):
        Kernel.__init__(self, **kwargs)
        self._replace_get_ipython()
        self.comm_manager = CommManager(shell=None, parent=self,
                                        kernel=self)
        self.shell_handlers['comm_open'] = self.comm_manager.comm_open
        self.shell_handlers['comm_msg'] = self.comm_manager.comm_msg
        self.shell_handlers['comm_close'] = self.comm_manager.comm_close
        if ipywidgets_extension_loaded:
            self.comm_manager.register_target('ipython.widget', Widget.handle_comm_opened)
        self._start_polymake()

    def _start_polymake(self):
        sig = signal.signal(signal.SIGINT, signal.SIG_DFL)
        try:
            polymake_run_command = pexpect.which( "polymake" )
            self.polymakewrapper = pexpect.spawnu( polymake_run_command + " -" )
            self.polymakewrapper.sendline( 'prefer "threejs";' )
            self.polymakewrapper.sendline( '$is_used_in_jupyter = 1;' )
            self.polymakewrapper.sendline( "##polymake_jupyter_start" )
            self.polymakewrapper.expect( "##polymake_jupyter_start")
        finally:
            signal.signal(signal.SIGINT, sig)

    def _process_python( self, code ):
        if code.find( "@python" ) == -1 and code.find( "@widget" ) == -1:
            return False
        exec(code[7:],globals())
        return True

    def do_execute(self, code, silent, store_history=True,
                   user_expressions=None, allow_stdin=False):
        
        default_return = {'status': 'ok', 'execution_count': self.execution_count,
                          'payload': [], 'user_expressions': {}}
        
        if not code.strip():
            return default_return
        
        if self._process_python( code ):
            return default_return
        
        interrupted = False
        code_to_execute=code.rstrip() + '; ' + 'print "===endofoutput===";'
        
        #stream_content = {'execution_count': self.execution_count, 'data': { 'text/plain': "Code:\n" + code_to_execute } }
        #self.send_response( self.iopub_socket, 'execute_result', stream_content )
        
        try:
            self.polymakewrapper.sendline( code_to_execute )
            self.polymakewrapper.expect( 'print "===endofoutput===";' )
            self.polymakewrapper.expect( "===endofoutput===" )
            output = self.polymakewrapper.before.strip().rstrip()
        except KeyboardInterrupt:
            self.polymakewrapper.child.sendintr()
            self.polymakewrapper.sendline( 'print "===endofoutput===";' )
            interrupted = True
            self.polymakewrapper.expect( "===endofoutput===" )
            self.polymakewrapper.expect( "===endofoutput===" )
        except EOF:
            output = self.polymakewrapper.before + 'Restarting polymake'
            self._start_polymake()
        if not silent:
            html_position = output.find( '<!--' )
            if html_position != -1:
                output = output[html_position:]
                output = output.replace( '{ width: 100%; height: 100% }', '{ width: 50%; height: 50% }' )
                stream_content = {'execution_count': self.execution_count, 'data': { 'text/plain': output } }
                self.send_response( self.iopub_socket, 'execute_result', stream_content )
                stream_content = {'execution_count': self.execution_count,
                                  'source' : "polymake",
                                  'data': { 'text/html': output},
                                  'metadata': dict() }
                self.send_response( self.iopub_socket, 'display_data', stream_content )
            elif len(output) != 0:
                stream_content = {'execution_count': self.execution_count, 'data': { 'text/plain': output } }
                self.send_response( self.iopub_socket, 'execute_result', stream_content )
        
        if interrupted:
            return {'status': 'abort', 'execution_count': self.execution_count}

        try:
            exitcode = 0
        except Exception:
            exitcode = 1

        if exitcode:
            return {'status': 'error', 'execution_count': self.execution_count,
                    'ename': '', 'evalue': str(exitcode), 'traceback': []}
        else:
            return {'status': 'ok', 'execution_count': self.execution_count,
                    'payload': [], 'user_expressions': {}}

    def do_shutdown(self, restart):
        
        self.polymakewrapper.terminate(True)
        if restart:
            _start_polymake()


### basic code completion for polymake
### currently known shortcomings: intermediate completion, in particular for files, completion of variable names

    def code_completion (self,code):
        completion = []
        code = re.sub( "\)$", "", code)
        code = repr(code)
        code_line = 'print jupyter_tab_completion(' + code + '); ' + 'print "===endofoutput===";'
        self.polymakewrapper.sendline( code_line )
        self.polymakewrapper.expect( 'print "===endofoutput===";' )
        self.polymakewrapper.expect( "===endofoutput===" )
        output = self.polymakewrapper.before
        completion = output.split("###")
        completion_length = completion.pop(0)
        return (completion_length,completion)

    # This is a rather poor completion at the moment
    def do_complete(self, code, cursor_pos):

        completion_length, completion = self.code_completion(code)
        cur_start = cursor_pos - int(completion_length)
        
        return {'matches':  completion, 'cursor_start': cur_start,
                'cursor_end': cursor_pos, 'metadata': dict(),
                'status': 'ok'}


