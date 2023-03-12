@echo off

start java -jar "C:\Users\fwiko\Documents\GitHub\NTU-Projects\202223\Term2\LoadBalancer\LoadBalancer\dist\LoadBalancer.jar" 5000 weighted /c "Load-Balancer"

start java -jar "C:\Users\fwiko\Documents\GitHub\NTU-Projects\202223\Term2\LoadBalancer\Node\dist\Node.jar" 1 6001 192.168.0.12 5000 /c "Node #1"
timeout /t 1
start java -jar "C:\Users\fwiko\Documents\GitHub\NTU-Projects\202223\Term2\LoadBalancer\Node\dist\Node.jar" 2 6002 192.168.0.12 5000 /c "Node #2"
timeout /t 1
start java -jar "C:\Users\fwiko\Documents\GitHub\NTU-Projects\202223\Term2\LoadBalancer\Node\dist\Node.jar" 3 6003 192.168.0.12 5000 /c "Node #3"

start java -jar "C:\Users\fwiko\Documents\GitHub\NTU-Projects\202223\Term2\LoadBalancer\Initiator\dist\Initiator.jar" 7000 192.168.0.12 5000 /c "Initiator"
