import unittest
import os
import tempfile
from contextlib import contextmanager
import sys
from io import StringIO

from deploymentutils import render_template, StateConnection, get_dir_of_this_file, argparser
from ipydex import IPS

"""
These tests can only cover a fraction of the actual features, because the tests do not have access to a remote machine
"""

TEMPLATEDIR = "_test_templates"


@contextmanager
def captured_output():
    """
    use out.getvalue().strip() and err.getvalue().strip()
    """
    # source: https://stackoverflow.com/a/17981937/333403
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


class TC1(unittest.TestCase):
    def setUp(self):
        pass

    def test_get_dir_of_this_file(self):
        test_path = get_dir_of_this_file()

        expected_path = os.path.join("deploymentutils", "test")
        self.assertTrue(test_path.endswith(expected_path))

    def test_render_remplate(self):
        test_path = get_dir_of_this_file()
        tmpl_path = os.path.join(test_path, TEMPLATEDIR, "template_1.txt")

        # test creation of target file next to the template
        target_path = os.path.join(test_path, TEMPLATEDIR, "1.txt")
        self.assertFalse(os.path.isfile(target_path))

        res = render_template(tmpl_path, context=dict(abc="test1", xyz=123))
        self.assertTrue(os.path.isfile(target_path))

        # after asserting that the file was created it can be removed
        os.remove(target_path)

        self.assertTrue("test1" in res)
        self.assertTrue("123" in res)

        # - - - -

        # test creation of target file at custom path
        target_path = tempfile.mktemp()

        self.assertFalse(os.path.isfile(target_path))
        res = render_template(tmpl_path, context=dict(abc="test1", xyz=123), target_path=target_path)
        self.assertTrue(os.path.isfile(target_path))
        # after asserting that the file was created it can be removed
        os.remove(target_path)

    def test_argparser(self):

        args = argparser.parse_args(["-u", "local"])

        self.assertEqual(args.target, "local")
        self.assertEqual(args.unsafe, True)

        args = argparser.parse_args(["local"])
        self.assertEqual(args.unsafe, False)

        with captured_output() as (out, err):
            self.assertRaises(SystemExit, argparser.parse_args, [])

        self.assertTrue("usage:" in err.getvalue().strip())


if __name__ == "__main__":
    if __name__ == '__main__':
        unittest.main()
