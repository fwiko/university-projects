package node;

import java.net.InetAddress;
import java.net.UnknownHostException;

public class Node {
    public static void main(String[] args) {
        
        // Node details
        int portNumber = -1;
        InetAddress ipAddress = null;
        int capacity = -1;
        
        // Load-Balancer details
        int loadBalancerPortNumber = -1;
        InetAddress loadBalancerIpAddress = null;

        // If an insufficient number of arguments have been passed
        if (args.length < 4) {
            System.out.println("Usage: java node <capacity> <port> <load_balancer_address> <load_balancer_port>");
            System.exit(0);
        }
        
        // Set the input Capacity of the Node
        try {
            capacity = Integer.parseInt(args[0]);
        } catch (NumberFormatException e) { 
            System.err.printf("Node (Error): Invalid Node Capacity %s\n", args[0]);
            System.exit(0);
        }
        
        // Set the Port Number that the Node Client will listen for Messages on
        try {
            portNumber = Integer.parseInt(args[0]);
        } catch (NumberFormatException e) {
            System.err.printf("Node (Error): Invalid Node Port Number %s\n", args[1]);
            System.exit(0);
        }

        // Set the IP Address that the Node Client will listen for Messages on
        try {
            ipAddress = InetAddress.getLocalHost();
        } catch (UnknownHostException e) {
            System.err.println("Node (Error): Failed to get Local-Host Address");
            System.exit(0);
        }

        // Set the IP Address of the Load-Balancer Server to send Messages to
        try {
            loadBalancerIpAddress = InetAddress.getByName(args[2]);
        } catch (UnknownHostException e) {
            System.err.printf("Node (Error): Invalid Load-Balancer IP Address \"%s\"\n", args[2]);
            System.exit(0);
        }
        
        // Set the Port Number of the Load-Balancer Server to send Messages to
        try {
            loadBalancerPortNumber = Integer.parseInt(args[3]);
        } catch (NumberFormatException e) {
            System.err.printf("Node (Error): Invalid Load-Balancer Port Number %s\n", args[3]);
            System.exit(0);
        }
        
        // Start the Node Client to register with the Load-Balancer and exchange Messages
        NodeClient nodeClient = NodeClient.getInstance();
        try {
            nodeClient.start(capacity, ipAddress, portNumber, loadBalancerIpAddress, loadBalancerPortNumber);
        } catch (IllegalArgumentException e) {
            System.err.printf("Node (Error): Failed to start Node Client (%s)\n", e.getMessage());
        }
    }
}
