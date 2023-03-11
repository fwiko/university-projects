package initiator;

import java.net.InetAddress;
import java.net.UnknownHostException;

public class Initiator {

    public static void main(String[] args) {
        
        // If less than X (X) arguments have been provided - Exit
        if (args.length < 3) {
            System.err.println("Usage: java initiator <port_number> <lb_ip_address> <lb_port_number>");
            System.exit(-1);
        }
        
        //
        int portNumber = -1;
        try {
            portNumber = Integer.parseInt(args[0]);
        } catch (NumberFormatException exception) {
            System.err.println("Initiator - ERROR: The \"port_number\" argument must be a valid Integer");
            System.exit(-1);
        }
        
        //
        InetAddress loadBalancerIpAddress = null;
        try {
            loadBalancerIpAddress = InetAddress.getByName(args[1]);
        } catch (UnknownHostException exception) {
            System.err.println("Initiator - ERROR: The \"lb_ip_address\" argument must be a valid IP Address");
            System.exit(-1);
        }
        
        //
        int loadBalancerPortNumber = -1;
        try {
            loadBalancerPortNumber = Integer.parseInt(args[2]);
        } catch (NumberFormatException exception) {
            System.err.println("Initiator - ERROR: The \"lb_port_number\" argument must be a valid Integer");
            System.exit(-1);
        }
        
        //
        InetAddress ipAddress = null;
        try {
            ipAddress = InetAddress.getLocalHost();
        } catch (UnknownHostException exception) {
            System.err.println("Node - ERROR: Failed to resolve the Local-Host IP Address");
            System.exit(-1);
        }
        
        InitiatorClient initiatorClient = new InitiatorClient(ipAddress, portNumber, loadBalancerIpAddress, loadBalancerPortNumber);
        initiatorClient.start();
    }
    
}
