from IPython.kernel.zmq.kernelapp import IPKernelApp
from .kernel import polymakeKernel
IPKernelApp.launch_instance(kernel_class=polymakeKernel)
