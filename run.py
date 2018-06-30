import sys

from cbsapi.cbsapi import CBSAPI

config = 'config.yaml'
if len(sys.argv) >= 2:
    config = sys.argv[1]
cbsapi = CBSAPI(config)

cbsapi.run()
