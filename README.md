# jupyter-polymake
Jupyter kernels for polymake 

This is an alpha version of a jupyter kernel for polymake. All of this is non-finished and might not work,
depending on your OS, libs, etc.

## wrapper-kernel

The `wrapper-kernel' is a Jupyter kernel based on the [bash wrapper kernel](https://github.com/takluyver/bash_kernel),
to install

```shell
    python setup.py install
    python -m jupyter_polymake_wrapper.install
```

To use it, use one of the following:

```shell
    ipython notebook
    ipython qtconsole --kernel polymake
    ipython console --kernel polymake
```

Note that this kernel assumes that `polymake' is in the `PATH'.
