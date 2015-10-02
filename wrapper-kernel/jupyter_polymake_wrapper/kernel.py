from IPython.kernel.zmq.kernelbase import Kernel
import pexpect
from pexpect import replwrap, EOF, which

from subprocess import check_output
from os import unlink, path

import base64
import imghdr
import re
import signal
import urllib

__version__ = '0.3'

version_pat = re.compile(r'version (\d+(\.\d+)+)')

class polymakeKernel(Kernel):
    implementation = 'jupyter_polymake_wrapper'
    implementation_version = __version__
    
    polymake_app_list = [ "common >", "fan >", "fulton >", "graph >", "group >", "ideal >", "matroid >", "polytope >", "topaz >", "tropical >",
                          "common (.*)>", "fan (.*)>", "fulton (.*)>", "graph (.*)>", "group (.*)>", "ideal (.*)>", "matroid (.*)>", "polytope (.*)>", "topaz (.*)>", "tropical (.*)>"  ]
    
    polymake_normal_app_nr = 10

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
                     'codemirror_mode': 'polymake', # note that this does not exist yet
                     'mimetype': 'text/x-polymake',
                     'file_extension': '.polymake'}

    def __init__(self, **kwargs):
        Kernel.__init__(self, **kwargs)
        self._start_polymake()

    def _start_polymake(self):
        sig = signal.signal(signal.SIGINT, signal.SIG_DFL)
        try:
            polymake_run_command = pexpect.which( "polymake" )
            self.polymakewrapper = pexpect.spawnu( polymake_run_command )
            self.polymakewrapper.expect( self.polymake_app_list )
        finally:
            signal.signal(signal.SIGINT, sig)

    def do_execute(self, code, silent, store_history=True,
                   user_expressions=None, allow_stdin=False):
        if not code.strip():
            return {'status': 'ok', 'execution_count': self.execution_count,
                    'payload': [], 'user_expressions': {}}

        interrupted = False
        code_list=code.split("\n")
        len_code_list = len(code_list)
        
        for i in range(0,len_code_list):
            code_list[i] = code_list[i].strip()
        
        if code_list[0] == "@print_as_javascript":
            code_list = code_list[1:]
            len_code_list = len_code_list - 1
            display_as_html = True
        else:
            stream_content_type='text'
            display_as_html = False
        
        for code_nr in range(0,len_code_list):
            try:
                code=code_list[code_nr]
                code_stripped = code.rstrip()
                self.send_response(self.iopub_socket, 'stream', {'name': 'stdout', 'text': "Code: " + code} )
                self.polymakewrapper.sendline( code_stripped + "#polymake_jupyter_comment" )
                self.polymakewrapper.expect( [ "#polymake_jupyter_comment" ] )
                out_nr = self.polymakewrapper.expect( self.polymake_app_list )
                if out_nr >= 10 and code_nr == len_code_list-1:
                    output = "incomplete input"
                    self.polymakewrapper.sendline( "\r\n;" )
                    self.polymakewrapper.expect( self.polymake_app_list )
                else:
                    output_tmp = self.polymakewrapper.before
                    output = re.sub( "\x1b\[.m|\x1b\[C|\x08", "", output_tmp )
                    output = output.strip() 
            except KeyboardInterrupt:
                self.polymakewrapper.child.sendintr()
                interrupted = True
                self.polymakewrapper.expect( self.polymake_app_list )
                output = self.polymakewrapper.before
            except EOF:
                output = self.polymakewrapper.before + 'Restarting polymake'
                self._start_polymake()
            
            if not silent and not display_as_html:
                if output != '':
                    stream_content = {'name': 'stdout', 'text': output}
                    self.send_response(self.iopub_socket, 'stream', stream_content)
            elif not silent and display_as_html:
                self.send_response(self.iopub_socket, 'stream', {'name': 'stdout', 'text': output} )
                stream_content = { 'source': "polymake",
                                   'data': { 'text/html': output },
                                   'metadata': dict() }
                self.send_response(self.iopub_socket, 'display_data', stream_content)
        
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

    # This is a rather poor completion at the moment
    def do_complete(self, code, cursor_pos):

        return {'matches': [ ], 'cursor_start': 0,
                'cursor_end': cursor_pos, 'metadata': dict(),
                'status': 'ok'}


