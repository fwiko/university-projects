package loadbalancer;

import java.net.InetAddress;
import java.net.UnknownHostException;

public class LoadBalancer {

    public static void main(String[] args) {
        // Attempt to retrieve the first input argument (port number)
        if (args.length < 1) {
            System.out.println("Usage: java loadbalancer <port>");
            System.exit(0);
        }
        
        // Process the input port number that Server will listen for Messages on
        int portNumber = 0;
        try {
            portNumber = Integer.parseInt(args[0]);
        } catch (NumberFormatException e) {
            System.err.println("Error: Input \"" + args[0] + "\" is not a valid Integer.");
            System.exit(0);
        }
        
        // Configure the IP address that the server will listen for Messages on
        InetAddress ipAddress = null;
        try {
            ipAddress = InetAddress.getLocalHost();
        } catch (UnknownHostException e) {
            System.err.println("Error: Failed to get LocalHost address.");
            System.exit(0);
        }
        
        // Initialise a new Server/Listener instance
        Server listenerServer = null;
        try {
            listenerServer = new Server(ipAddress.getHostAddress(), portNumber);
        } catch (IllegalArgumentException e) {
            System.err.println(e.getMessage());
            System.exit(0);
        }
        
        // Start the Server to listen for and handle Messages from Initiator and Node(s)
        listenerServer.start();
    }
}
