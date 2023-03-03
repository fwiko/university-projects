package initiator;

import java.net.InetAddress;
import java.net.UnknownHostException;

public class Initiator {
    public static void main(String[] args) {
        
        // Initiator details
        InetAddress ipAddress = null;
        int portNumber = -1;
        
        // Load-Balancer details
        InetAddress loadBalancerIpAddress = null;
        int loadBalancerPortNumber = -1;

        // If an insufficient number of arguments have been passed
        if (args.length < 4) {
            System.out.println("Usage: java initiator <ip_address> <port_number> <load_balancer_ip_address> <load_balancer_port_number>");
            System.exit(0);
        }
        
        // Set the Port Number that the Initiator Client will listen for Messages on
        try {
            portNumber = Integer.parseInt(args[1]);
        } catch (NumberFormatException e) {
            System.err.printf("Node (Error): Invalid Initiator Port Number %s\n", args[1]);
            System.exit(0);
        }

        // Set the IP Address that the Initiator Client will listen for Messages on
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
        

        InitiatorClient initiatorClient = new InitiatorClient();
        initiatorClient.start(ipAddress, portNumber, loadBalancerIpAddress, loadBalancerPortNumber);
        
    }
    
}
