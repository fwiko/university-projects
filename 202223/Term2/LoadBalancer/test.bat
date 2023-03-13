@echo off

set nodes=%1
set ip_address=%2
set allocation_algorithm=%3

start java -jar "C:\Users\fwiko\Documents\GitHub\NTU-Projects\202223\Term2\LoadBalancer\LoadBalancer\dist\LoadBalancer.jar" 5000 %allocation_algorithm% /c "Load-Balancer"

FOR /L %%A IN (1,1,%nodes%) DO (
    start java -jar "C:\Users\fwiko\Documents\GitHub\NTU-Projects\202223\Term2\LoadBalancer\Node\dist\Node.jar" %%A 600%%A %ip_address% 5000
    timeout 1
)

start java -jar "C:\Users\fwiko\Documents\GitHub\NTU-Projects\202223\Term2\LoadBalancer\Initiator\dist\Initiator.jar" 7000 %ip_address% 5000 /c "Initiator"
