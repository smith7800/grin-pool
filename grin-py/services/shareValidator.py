#!/usr/bin/python

# Copyright 2018 Blade M. Doyle
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# shareValidator.py
#   For each pool_share not yet validated:
#     Verify it against the grin_share (does it exist?)
#       if not, mark it as invalid
#     get the share difficulty from grin_share table
#     Verify that the difficulty meets requirements,
#     If everything is ok, mark pool_shares record validated and valid

# shareValidator.py validates pool_share:
#        Check if a matching grin_share exists.  If not, this share was rejected and is invalid
#        Check grin_share.actual_difficulty >= pool_share.worker_difficulty or mark invalid
#        Check nonce and timestamp against grin_share for added sanity

import sys
import time
from datetime import datetime

from grinlib import lib
from grinbase.model.pool_shares import Pool_shares
from grinbase.model.grin_shares import Grin_shares


PROCESS = "shareValidator"
LOGGER = None
CONFIG = None

def main():
    global LOGGER
    global CONFIG
    CONFIG = lib.get_config()
    LOGGER = lib.get_logger(PROCESS)
    LOGGER.warn("=== Starting {}".format(PROCESS))

    # Connect to DB
    database = lib.get_db()

    new_poolshares = Pool_shares.getUnvalidated()
    for pool_share in new_poolshares:
        grin_share = Grin_shares.get_by_nonce(pool_share.nonce)
        if grin_share == None:
            # No matching validated grin share was found
            # XXX TODO: Only invalidate if its old enough
            pool_share.validated = True
            pool_share.is_valid = False
            pool_share.invalid_reason = "no grin_share"
        else:
            if pool_share.nonce != grin_share.nonce:
                pool_share.validated = True
                pool_share.is_valid = False
                pool_share.invalid_reason = "nonce mismatch"
            if pool_share.worker_difficulty > grin_share.actual_difficulty:
                pool_share.validated = True
                pool_share.is_valid = False
                pool_share.invalid_reason = "low difficulty"
        # Update record
        pool_share.validated = True
        pool_share.is_valid = True
        pool_share.invalid_reason = "None"
        LOGGER.warn("Share {}, {} is {} because {}".format(pool_share.height, pool_share.nonce, pool_share.is_valid, pool_share.invalid_reason))
        database.db.getSession().commit()

    # db.set_last_run(PROCESS, str(time.time()))
    LOGGER.warn("=== Completed {}".format(PROCESS))


if __name__ == "__main__":
    main()
