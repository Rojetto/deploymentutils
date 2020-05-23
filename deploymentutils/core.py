import os
import inspect
import subprocess
from fabric import Connection
from invoke import UnexpectedExit
from jinja2 import Environment, PackageLoader, FileSystemLoader
from colorama import Style, Fore

from ipydex import IPS


class Container(object):

    def __init__(self, **kwargs):
        self.__dict__.update(**kwargs)


def render_template(tmpl_path, context):

    path, fname = os.path.split(tmpl_path)
    assert path != ""

    jin_env = Environment(loader=FileSystemLoader(path))

    special_str = "template_"
    assert fname.startswith(special_str) and (fname.count(special_str) == 1) and len(fname) > len(special_str)
    res_fname = fname.replace(special_str, "")

    template = jin_env.get_template(fname)
    context["warning"] = "This file was autogenerated from the template: {}".format(fname)
    result = template.render(context=context)

    target_path = os.path.join(path, res_fname)

    if 1:
        with open(target_path, "w") as resfile:
            resfile.write(result)


class StateConnection(object):
    """
    Wrapper class for fabric connection which remembers the working directory. Also has a target attribute to
    distinquis between remote and local operation.
    """

    def __init__(self, remote, user, target="remote"):
        self.dir = None
        self.last_result = None
        self.last_command = None
        self.remote = remote
        self.user = user

        assert target in ("remote", "local")
        self.target = target
        self._c = {"remote": Connection(remote, user), "local": None}[target]

    def chdir(self, path, target_spec="both"):
        """
        The following works on uberspace:

        c.chdir("etc")
        c.chdir("~")
        c.chdir("$HOME")

        :param path:
        :param target_spec:
        :return:
        """

        if path is None:
            self.dir = None
            return

        self.dir = path

        cmd = "pwd"
        res = self.run(cmd, hide=True, warn=True, target_spec=target_spec)

        if res.exited != 0:
            print(bred(f"Could not change directory. Error message: {res.stderr}"))

        # assure they have the last component in common
        # the rest might differ due to symlinks and relative paths
        assert res.stdout.strip().endswith(os.path.split(path)[1])

        # store the result of pwd in the variable

        return res

    def run(self, cmd, use_dir=True, hide=False, warn="smart", printonly=False, target_spec="remote"):
        """

        :param cmd:
        :param use_dir:
        :param hide:            see docs of invoke
        :param warn:            see docs of invoke and handling of "smart" bewlow
        :param printonly:       flag for debugging
        :param target_spec:     str \in {"remote", "local", "both"}; default: "remote"
        :return:
        """

        if use_dir and self.dir is not None:
            execution_dir = self.dir
        else:
            execution_dir = "./"

        self.last_command = f"cd {execution_dir}; {cmd}"

        if warn == "smart":
            # -> get a result object (which would not be the case for warn=False)
            warn = True

            # safe the result self.last_result
            smart_error_handling = True
        else:
            smart_error_handling = False

        if not printonly:
            try:
                res = self.run_target_command(cmd, execution_dir, hide=hide, warn=warn, target_spec=target_spec)
            except UnexpectedExit as ex:
                # ! This message should be displayed
                msg = f"The command {cmd} failed. You can run it again with `warn=smart` (recommendend) or" \
                    f"`warn=True` and inspect `result.stderr` to get more information.\n" \
                    f"Original exception follows:\n"

                raise ValueError(msg+str(ex))
            else:
                if smart_error_handling and res.exited != 0:
                    self.last_result = res
                    msg = f"The command {cmd} failed with code {res.exited}. This is res.stderr:\n\n" \
                          f"{res.stderr}\n\n" \
                          "You can also investigate c.last_result and c.last_command"
                    raise ValueError(msg)
        else:
            print("->:", cmd)
            res = None
        return res

    def run_target_command(self, cmd, execution_dir, hide, warn, target_spec):
        """
        Actually run the command (or not), depending on self.target and target_spec.

        :param cmd:
        :param execution_dir:
        :param hide:
        :param warn:
        :param target_spec:
        :return:
        """

        assert self.target in ("local", "remote"), f"Invald target: {self.target}"
        if self.target == "remote":
            cmd = f"cd {execution_dir}; {cmd}"

            if target_spec in ("remote", "both"):
                res = self._c.run(cmd, hide=hide, warn=warn)
            else:
                print(dim(f"> Omitting command `{cmd}`\n> due to target_spec: {target_spec}."))
                res = None
        else:
            # TODO : handle warn flag
            if target_spec in ("local", "both"):
                orig_dir = os.getcwd()
                os.chdir(execution_dir)

                cmd_as_list = cmd.split(" ")
                try:
                    res0 = subprocess.check_output(cmd_as_list).decode("utf8")
                except subprocess.CalledProcessError as err:
                    res = Container(stdout="", stderr=err.stderr, exited=err.returncode)
                else:
                    res = Container(stdout=res0, stderr="", exited=0)
                finally:
                    os.chdir(orig_dir)

            else:
                print(dim(f"> Omitting command `{cmd}` in dir {execution_dir}\n> due to target_spec: {target_spec}."))
                res = Container(exited=0)
                res = None

        return res

    def rsync_upload(self, source, dest, target_spec, filters="", printonly=False):
        """
        Perform the appropriate rsync command (or not), depending on self.target and target_spec.

        :param source:
        :param dest:
        :param target_spec:
        :param filters:
        :param printonly:
        :return:
        """

        # construct the destionation
        if self.target == "remote":
            full_dest = f"{self.user}@{self.remote}:{dest}"
            cmd_start = "rsync -pthrvz --rsh='ssh  -p 22'"
        else:
            full_dest = dest
            cmd_start = "rsync -pthrvz"

        cmd = f"{cmd_start} {filters} {source} {full_dest}"

        if printonly:
            print("->:", cmd)
        elif target_spec != "both" and self.target != target_spec:
            print(dim(f"> Omitting rsync command `{cmd}`\n> due to target_spec: {target_spec}."))
        else:
            # TODO: instead of locally calling rsync, find a more elegant (plattform-independent) way to do this
            os.system(cmd)


def get_dir_of_this_file():
    """
    Assumes that this function is called from a script. Return the path of that script (excluding the script itself).
    """
    return os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe().f_back)))


def dim(txt):
    return f"{Style.DIM}{txt}{Style.RESET_ALL}"


def bright(txt):
    return f"{Style.BRIGHT}{txt}{Style.RESET_ALL}"


def bgreen(txt):
    return f"{Fore.GREEN}{Style.BRIGHT}{txt}{Style.RESET_ALL}"


def bred(txt):
    return f"{Fore.RED}{Style.BRIGHT}{txt}{Style.RESET_ALL}"


def yellow(txt):
    return f"{Fore.YELLOW}{txt}{Style.RESET_ALL}"
