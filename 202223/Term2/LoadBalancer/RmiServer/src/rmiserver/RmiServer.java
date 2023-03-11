package rmiserver;

import java.rmi.registry.*;

public class RmiServer {

    public static void main(String[] args) {
        System.out.println(System.getProperty("java.security.policy"));
        int port = 4000;
        Registry RmiRegistry = null;
        try {
            // get the port from the arguments list
            if (args.length == 1) {
                port = Integer.parseInt(args[0]);
            } else {
                System.out.println("usage: RMIServer <port number>");
                System.exit(0);
            }

            // start rmi server and bind to port

            System.out.println("Running RMIServer on port " + port);
            RmiRegistry = LocateRegistry.createRegistry(port);
            RmiRegistry.rebind("RMIObject", new RmiObject());

        } catch (Exception error) {
            System.out.println("Error: " + error.getMessage());
            error.printStackTrace();
        }
    }
}
