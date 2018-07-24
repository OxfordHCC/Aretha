import refineJsonData, sys 

import json, os

if len(sys.argv) > 1:
    refineJsonData.compileUsageImpacts(sys.argv[1])
else:
    refineJsonData.compileUsageImpacts()