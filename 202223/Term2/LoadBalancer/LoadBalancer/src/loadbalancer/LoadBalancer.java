package loadbalancer;

public class LoadBalancer {

    public static void main(String[] args) {
        if (args.length < 1) {
            System.out.println("Usage: java loadbalancer <port>");
            System.exit(0);
        }
        
        int port = Integer.parseInt(args[0]);
        
        
    }
    
}
