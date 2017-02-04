#!/usr/bin/env python3.5

import json
import os
import sys
from distutils.core import setup
import sys
from jupyter_client.kernelspec import install_kernel_spec
from IPython.utils.tempdir import TemporaryDirectory
from os.path import dirname,abspath
from shutil import copy as file_copy

kernel_json = {"argv":[sys.executable,"-m","jupyter_kernel_polymake", "-f", "{connection_file}"],
 "display_name":"polymake",
 "language":"polymake",
 "codemirror_mode":"perl", # note that this does not exist yet
 "env":{"PS1": "$"}
}

def install_my_kernel_spec(user=True):
    with TemporaryDirectory() as td:
        os.chmod(td, 0o755) # Starts off as 700, not user readable
        with open(os.path.join(td, 'kernel.json'), 'w') as f:
            json.dump(kernel_json, f, sort_keys=True)
        path_of_file = dirname( abspath(__file__) ) + "/jupyter_kernel_polymake/resources/"
        filenames=[ "Detector.js", "three.js", "kernel.js"  ]
        filenames_renderer=[ "CanvasRenderer.js", "Projector.js", "SVGRenderer.js" ]
        filenames_control=[ "TrackballControls.js" ]
        for i in filenames:
            file_copy(path_of_file + i, td )
        os.mkdir( td + "/renderers", mode=755 )
        for i in filenames_renderer:
            file_copy(path_of_file + "renderers/" + i, td + "/renderers" )
        os.mkdir( td + "/controls", mode=755 )
        for i in filenames_control:
            file_copy(path_of_file + "controls/" + i, td + "/controls" )
        file_copy(path_of_file + "logo-32x32.png", td )
        file_copy(path_of_file + "logo-64x64.png", td )
        #print(os.listdir(td))
        #print(os.listdir(td + "/controls"))
        #print(os.listdir(td + "/renderers"))
        print('Installing jupyter kernel spec for poiymake')
        install_kernel_spec(td, 'polymake', user=user, replace=True)

def main(argv=None):
    install_my_kernel_spec()

if __name__ == '__main__':
    main()



setup( name="jupyter_kernel_polymake"
     , version="0.8"
     , description="A Jupyter kernel for polymake"
     , author="Sebastian Gutsche"
     , author_email="sebastian.gutsche@gmail.com"
     , url="https://github.com/sebasguts/jupyter-polymake"
     , packages=["jupyter_kernel_polymake"]
     , package_dir={"jupyter_kernel_polymake": "jupyter_kernel_polymake"}
     , package_data={"jupyter_kernel_polymake": ["resources/logo-32x32.png",
                                                 "resources/logo-64x64.png",
                                                 "resources/kernel.js",
                                                 "resources/Detector.js",
                                                 "resources/three.js",
                                                 "resources/renderers/CanvasRenderer.js",
                                                 "resources/renderers/Projector.js",
                                                 "resources/renderers/SVGRenderer.js",
                                                 "resources/controls/TrackballControls.js" ]}
     ,
     )
