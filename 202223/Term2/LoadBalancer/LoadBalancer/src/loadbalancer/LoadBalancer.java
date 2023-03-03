package loadbalancer;

import java.net.InetAddress;
import java.net.UnknownHostException;

public class LoadBalancer {
    public static void main(String[] args) {
        int portNumber = -1;
        InetAddress ipAddress = null;
        AllocationMethod allocationMethod = null;

        // If an insufficient number of arguments have been passed
        if (args.length < 2) {
            System.out.println("Usage: java loadbalancer <port> <allocation_method>");
            System.exit(0);
        }

        // Set the input Port Number that the Load-Balancer Server will listen for Messages on
        try {
            portNumber = Integer.parseInt(args[0]);
        } catch (NumberFormatException e) {
            System.err.println("LoadBalancer - ERROR: Port must be an Integer");
            System.exit(0);
        }

        // Set the IP Address that the Load-Balancer Server will listen for Messages on
        try {
            ipAddress = InetAddress.getLocalHost();
        } catch (UnknownHostException e) {
            System.err.println("LoadBalancer - ERROR: Failed to fetch Local Host Address");
            System.exit(0);
        }
        
        // Set the allocation algorithm (Weighted Round-Robin / Round-Robin) Based on input parameters ( RR / WRR )
        try {
            allocationMethod = AllocationMethod.valueOf(args[1].toUpperCase());
        } catch (IllegalArgumentException e) {
            System.err.printf("LoadBalancer - ERROR: Allocation Method must be either NORMAL (Round-Robin) or WEIGHTED (Weighted Round-Robin)\n");
            System.exit(0);
        }
        
        // Create a new LoadBalancerServer instance used to process incoming Messages and allocate Jobs
        LoadBalancerServer loadBalancerServer = LoadBalancerServer.getInstance();
        try {
            loadBalancerServer.start(ipAddress, portNumber, allocationMethod);
        } catch (IllegalArgumentException e) {
            System.err.printf("LoadBalancer - ERROR: Failed to start Load-Balancer Server (%s)\n", e.getMessage());
        }
    }
}
