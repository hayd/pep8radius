import os

try:
    from subprocess import STDOUT, check_output, CalledProcessError
except ImportError:  # pragma: no cover
    # python 2.6 doesn't include check_output
    # monkey patch it in!
    import subprocess
    STDOUT = subprocess.STDOUT

    def check_output(*popenargs, **kwargs):
        if 'stdout' in kwargs:  # pragma: no cover
            raise ValueError('stdout argument not allowed, '
                             'it will be overridden.')
        process = subprocess.Popen(stdout=subprocess.PIPE,
                                   *popenargs, **kwargs)
        output, _ = process.communicate()
        retcode = process.poll()
        if retcode:
            cmd = kwargs.get("args")
            if cmd is None:
                cmd = popenargs[0]
            raise subprocess.CalledProcessError(retcode, cmd,
                                                output=output)
        return output
    subprocess.check_output = check_output

    # overwrite CalledProcessError due to `output`
    # keyword not being available (in 2.6)
    class CalledProcessError(Exception):

        def __init__(self, returncode, cmd, output=None):
            self.returncode = returncode
            self.cmd = cmd
            self.output = output

        def __str__(self):
            return "Command '%s' returned non-zero exit status %d" % (
                self.cmd, self.returncode)
    subprocess.CalledProcessError = CalledProcessError


def shell_out(cmd, stderr=STDOUT, cwd=None):
    if cwd is None:
        cwd = os.getcwd() # TODO do I need to normalize this on Windows

    out = check_output(cmd, cwd=cwd, stderr=stderr, universal_newlines=True)
    return _clean_output(out)


def shell_out_ignore_exitcode(cmd, stderr=STDOUT, cwd=None):
    try:
        return shell_out(cmd, stderr=stderr, cwd=cwd)
    except CalledProcessError as c:
        return _clean_output(c.output)

def _clean_output(out):
    try:
        out = out.decode('utf-8')
    except AttributeError:  # python3, pragma: no cover
        pass
    return out.strip()
