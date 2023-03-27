package controller;

import java.net.InetAddress;
import java.net.UnknownHostException;

public class Controller {

    public static void main(String[] args) {
        
        // If less than three (3) arguments have been provided - Exit
        if (args.length < 3) {
            System.err.println("Usage: java controller <port_number> <load_balancer_ip_address> <load_balancer_port_number>");
            System.exit(-1);
        }
        
        // Parse the first parameter "port_number" as an Integer
        int portNumber = -1;
        try {
            portNumber = Integer.parseInt(args[0]);
        } catch (NumberFormatException exception) {
            System.err.println("Controller - ERROR: The \"port_number\" argument must be a valid Integer");
            System.exit(-1);
        }
        
        // Parse the second parameter "load_balancer_ip_address" as an InetAddress
        InetAddress loadBalancerIpAddress = null;
        try {
            loadBalancerIpAddress = InetAddress.getByName(args[1]);
        } catch (UnknownHostException exception) {
            System.err.println("Controller - ERROR: The \"load_balancer_ip_address\" argument must be a valid IP Address");
            System.exit(-1);
        }
        
        // Parse the third parameter "load_balancer_port_number" as an Integer
        int loadBalancerPortNumber = -1;
        try {
            loadBalancerPortNumber = Integer.parseInt(args[2]);
        } catch (NumberFormatException exception) {
            System.err.println("Controller - ERROR: The \"load_balancer_port_number\" argument must be a valid Integer");
            System.exit(-1);
        }
        
        // Get the IP Address of the Controller as an InetAddress object
        InetAddress ipAddress = null;
        try {
            ipAddress = InetAddress.getLocalHost();
        } catch (UnknownHostException exception) {
            System.err.println("Node - ERROR: Failed to resolve the Local-Host IP Address");
            System.exit(-1);
        }
        
        // Create and start the Controller Client
        ControllerClient controllerClient = new ControllerClient(ipAddress, portNumber, loadBalancerIpAddress, loadBalancerPortNumber);
        controllerClient.start();
        
    }
    
}
