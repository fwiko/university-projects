package node;

import java.net.InetAddress;
import java.net.UnknownHostException;

public class Node {
    public static void main(String[] args) {
        
        // If less than four (4) arguments have been provided - Exit
        if (args.length < 4) {
            System.err.println("Usage: java node <maximum_capacity> <port_number> <lb_ip_address> <lb_port_number>");
            System.exit(1);
        }
        
        // Parse the first parameter "maximum_capacity" as an Integer
        int maximumCapacity = -1;
        try {
            maximumCapacity = Integer.parseInt(args[0]);
        } catch (NumberFormatException exception) {
            System.err.println("Node - ERROR: The \"maximum_capacity\" argument must be a valid Integer");
            System.exit(1);
        }
        
        // Parse the second parameter "port_number" as an Integer
        int portNumber = -1;
        try {
            portNumber = Integer.parseInt(args[1]);
        } catch (NumberFormatException exception) {
            System.err.println("Node - ERROR: The \"port_number\" argument must be a valid Integer");
            System.exit(1);
        }
        
        // Parse the third parameter "lb_ip_address" as an InetAddress
        InetAddress loadBalancerIpAddress = null;
        try {
            loadBalancerIpAddress = InetAddress.getByName(args[2]);
        } catch (UnknownHostException exception) {
            System.err.println("Node - ERROR: The \"lb_ip_address\" argument must be a valid IP Address");
            System.exit(1);
        }
        
        // Parse the fourth parameter "lb_port_number" as an Integer
        int loadBalancerPortNumber = -1;
        try {
            loadBalancerPortNumber = Integer.parseInt(args[3]);
        } catch (NumberFormatException exception) {
            System.err.println("Node - ERROR: The \"lb_port_number\" argument must be a valid Integer");
            System.exit(1);
        }
        
        // Get the IP Address of the Node as an InetAddress object
        InetAddress ipAddress = null;
        try {
            ipAddress = InetAddress.getLocalHost();
        } catch (UnknownHostException exception) {
            System.err.println("Node - ERROR: Could not to resolve the LocalHost IP Address");
            System.exit(1);
        }
        
        // Create and Start the Node Client
        NodeClient nodeClient = new NodeClient(maximumCapacity, ipAddress, portNumber, loadBalancerIpAddress, loadBalancerPortNumber);
        
    }
}
