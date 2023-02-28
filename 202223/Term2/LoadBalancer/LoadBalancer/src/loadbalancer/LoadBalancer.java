package loadbalancer;

import java.net.InetAddress;
import java.net.UnknownHostException;

public class LoadBalancer {
    public static void main(String[] args) {
        int portNumber = -1;
        InetAddress ipAddress = null;

        // If an insufficient number of arguments have been passed
        if (args.length < 1) {
            System.out.println("Usage: java loadbalancer <port>");
            System.exit(0);
        }

        // Parse the input Port Number that the Load-Balancer Server will listen for Messages on
        try {
            portNumber = Integer.parseInt(args[0]);
        } catch (NumberFormatException e) {
            System.err.println("Load-Balancer (Error): Port must be an Integer");
            System.exit(0);
        }

        // Set the IP Address that the Load-Balancer Server will listen for Messages on
        try {
            ipAddress = InetAddress.getLocalHost();
        } catch (UnknownHostException e) {
            System.err.println("Load-Balancer (Error): Failed to fetch Local Host Address");
            System.exit(0);
        }

        // Create a new LoadBalancerServer instance used to process incoming Messages and allocate Jobs
        LoadBalancerServer loadBalancerServer = LoadBalancerServer.getInstance();
        try {
            loadBalancerServer.start(ipAddress, portNumber);
        } catch (IllegalArgumentException e) {
            System.err.printf("Load-Balancer (Error): Failed to start Load-Balancer Server (%s)\n", e.getMessage());
        }
    }
}
