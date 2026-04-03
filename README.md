Project: Host Discovery Service in SDN

Description:
This project implements a host discovery mechanism using POX controller 

Files:
- host_discovery.py -> Controller logic
- topology.py -> Mininet topology

Execution Process:
1. Run POX Controller:
	python3 pox.py log.levl --DEBUG host_discovery 
2. Run topology: 
	sudo python3 topology.py
3. Use Mininet CLI:
	pingall

Output:
- Hosts detected dynamically
- Host database updated with MAC,IP,DPID,Port

Note:
Detailed execution screenshots and explanations are provided in the submission 

