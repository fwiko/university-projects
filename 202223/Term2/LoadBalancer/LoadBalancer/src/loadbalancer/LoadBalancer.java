package loadbalancer;

import java.net.InetAddress;
import java.net.UnknownHostException;

public class LoadBalancer {
    public static void main(String[] args) {
        // If less than two (2) arguments have been provided - Exit
        if (args.length < 2) {
            System.err.println("Usage: java loadbalancer <port_number> <rmi_port_number> <allocation_algorithm>");
            System.exit(1);
        }
        
        // Parse the first parameter "port_number" as an Integer
        int portNumber = -1;
        try {
            portNumber = Integer.parseInt(args[0]);
        } catch (NumberFormatException exception) {
            System.err.println("LoadBalancer - ERROR: The \"port_number\" argument must be a valid Integer");
            System.exit(1);
        }
        
        // Parse the second parameter "port_number" as an Integer
        int rmiPortNumber = -1;
        try {
            rmiPortNumber = Integer.parseInt(args[1]);
        } catch (NumberFormatException exception) {
            System.err.println("LoadBalancer - ERROR: The \"rmi_port_number\" argument must be a valid Integer");
            System.exit(1);
        }
        
        // Parse the thid parameter "allocation_algorithm" as an AlgorithmAlgorithm
        AllocationAlgorithm allocationAlgorithm = null;
        try {
            allocationAlgorithm = AllocationAlgorithm.valueOf(args[2]);
        } catch (IllegalAccessError exception) {
            System.err.printf("LoadBalancer - ERROR: The \"allocation_algorithm\" argument must be either NORMAL (Round-Robin) or WEIGHTED (Weighted Round-Robin)");
            System.exit(1);
        }
        
        // Get the IP Address of the LoadBalancer as an InetAddress object
        InetAddress ipAddress = null;
        try {
            ipAddress = InetAddress.getLocalHost();
        } catch (UnknownHostException exception) {
            System.err.println("LoadBalancer - ERROR: Could not to resolve the LocalHost IP Address");
            System.exit(1);
        }
        
        LoadBalancerServer loadBalancerServer = new LoadBalancerServer(ipAddress, portNumber, allocationAlgorithm);
        loadBalancerServer.start();
        
    }
}
