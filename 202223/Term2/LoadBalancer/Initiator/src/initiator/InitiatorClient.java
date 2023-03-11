package initiator;

import initiator.managers.MessageManager;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.InetAddress;

public class InitiatorClient {
    
    InetAddress ipAddress = null;
    int portNumber = -1;
    
    InetAddress loadBalancerIpAddress = null;
    int loadBalancerPortNumber = -1;
    
    Thread messageHandler = null;
    
    BufferedReader inputReader = null;
    
    // Message and Job Manager class singletons
    MessageManager messageManager = null;
    
    public InitiatorClient(InetAddress ipAddress, int portNumber, InetAddress loadBalancerIpAddress, int loadBalancerPortNumber) {
        this.ipAddress = ipAddress;
        this.portNumber = portNumber;
        
        this.loadBalancerIpAddress = loadBalancerIpAddress;
        this.loadBalancerPortNumber = loadBalancerPortNumber;
    }
    
    public void start() {
        messageManager = MessageManager.getInstance();
        
        // Attempt to start the Message Manager, listening on the Initiator socket
        try {
            messageManager.start(ipAddress, portNumber);
        } catch (IOException exception) {
            System.err.printf("InitiatorClient - ERROR: IOException when opening Datagram Channel on %s:%d\n", ipAddress.getHostAddress(), portNumber);
            System.exit(-1);
        }
        
        messageHandler = new Thread() {
            @Override
            public void run() {
                while (!messageManager.isStopped()) {
            
                }
            }
        };
        
        messageHandler.start();
        
        System.out.println("### STARTED INITIATOR CLIENT ###");
        
        showOptions();
        
        inputReader = new BufferedReader(new InputStreamReader(System.in));
        while (!messageManager.isStopped()) {
            String commandString = "";
            while (commandString.length() < 1) {
                System.out.println("Initiator> ");
                try {
                    commandString = inputReader.readLine();
                } catch (IOException exception) {
                    System.err.printf("InitiatorClient - ERROR: Failed to get user-input (%s)\n", exception.getMessage());
                }
            }
            
            try {
                handleCommand(commandString);
            } catch (IllegalArgumentException exception) {
                
            }
        }
    }
    
    private void handleCommand(String commandString) throws IllegalArgumentException {
        throw new IllegalArgumentException(commandString);
    }
    
    private void showOptions() {
        
    }
}
