from nezha import manager
from nezha.openstack.common.processutils import trycmd

class HandleManager(manager.Manager):
    def __init__(self):
        pass

    def get_all_iptables(self, context):
        out, err = trycmd('iptables-save',
                            run_as_root=True,
                            check_exit_code=[0])

        if not err:
            return out
        else:
            return err
