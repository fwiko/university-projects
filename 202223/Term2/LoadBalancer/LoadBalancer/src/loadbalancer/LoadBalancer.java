package loadbalancer;

public class LoadBalancer {

    public static void main(String[] args) {
        // Attempt to retrieve the first input argument (port number)
        if (args.length < 1) {
            System.out.println("Usage: java loadbalancer <port>");
            System.exit(0);
        }
        
        // Process the input port number that Server will listen for Messages on
        int port = 0;
        try {
            port = Integer.parseInt(args[0]);
        } catch (NumberFormatException e) {
            System.out.println("Error: Input \"" + args[0] + "\" is not a valid Integer.");
            System.exit(0);
        }
        
        // Initialise a new Server/Listener instance
        Server listenerServer = new Server(port);
        
        // Start the Server to listen for and handle Messages from Initiator and Node(s)
        try {
            listenerServer.start();
        } catch (IllegalArgumentException e) {
            System.out.println(e.getMessage());
            System.exit(0);
        }
        
    }
    
}
