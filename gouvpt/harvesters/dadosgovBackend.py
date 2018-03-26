from udata.harvest.backends.base import BaseBackend

class DGBaseBackend(BaseBackend):
    def __init__(self, source, job=None, dryrun=False, max_items=None):
        super(DGBaseBackend, self).__init__(source, job, False, None)