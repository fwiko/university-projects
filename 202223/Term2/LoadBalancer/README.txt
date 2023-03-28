How to run this Load-Balancer system project

Option 1 - 
	
	1. Unzip all included project folders
	2. Start the Load-Balancer by running the .jar file with "java -jar loadbalancer.jar <port_number> <weighted or normal>"
	3. Start any number of Nodes by running the .jar file with "java -jar node.jar <capacity> <port> <load_balancer_ip> <load_balancer_port>" (make sure Nodes have unique ports)
	4. Start the Controller by running the .jar file with "java -jar controller <port> <load_balancer_ip> <load_balancer_port>"


Option 2 -

	1. Unzip all included project folders
	2. Run the test.bat script in the same directory as the folders with ".\test.bat <number_of_nodes> <load_balancer_ip> <load_balancer_port>"