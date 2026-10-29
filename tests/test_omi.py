"""Runs every area test file in one process: python tests/test_omi.py"""
import helpers  # noqa: F401
import test_upgrade
import test_init
import test_github
import test_worker
import test_creds
import test_tools
import test_hooks
import test_tasks
import test_content
import test_cli
import test_attach
import test_detached
import test_install


if __name__ == "__main__":
    test_upgrade.main()
    test_init.main()
    test_github.main()
    test_worker.main()
    test_creds.main()
    test_tools.main()
    test_hooks.main()
    test_tasks.main()
    test_content.main()
    test_cli.main()
    test_attach.main()
    test_detached.main()
    test_install.main()
    print("ok")
