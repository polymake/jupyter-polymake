#!/usr/bin/env python3.5

import sys
from distutils.core import setup

setup( name="jupyter_polymake_wrapper"
     , version="0.1"
     , description="A Jupyter wrapper kernel for polymake"
     , author="Sebastian Gutsche"
     , url="https://github.com/sebasguts/jupyter-polymake"
     , packages=["jupyter_polymake_wrapper"]
     , package_dir={"jupyter_polymake_wrapper": "jupyter_polymake_wrapper"}
     , package_data={ "jupyter_polymake_wrapper": [ "js" ]}
     ,
     )
