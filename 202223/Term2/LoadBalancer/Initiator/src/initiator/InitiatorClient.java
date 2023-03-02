package initiator;

import initiator.managers.MessageManager;
import initiator.messages.MessageInbound;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.InetAddress;

public class InitiatorClient {
    // Singleton instance of InitiatorClient
    private static InitiatorClient instance = null;
    
    // Flag used to track whether Initiator is running
    private boolean running = true;
    
    // Initiator socket details
    private InetAddress initiatorIpAddress = null;
    private int initiatorPortNumber = -1;
    
    // LoadBalancerServer socket details
    private InetAddress loadBalancerIpAddress = null;
    private int loadBalancerPortNumber = -1;
    
    // Singleton MessageManager instance
    private MessageManager messageManager = null;
    
    // Thread for handling Messages in the background
    private Thread messageHandler = null;
    
    // 
    private BufferedReader inputReader = null;
    
    public static InitiatorClient getInstance() {
        // If an instance of the NodeClient already exists
        if (instance != null) {
            return instance;
        }
        // Create a new instance of the NodeClient
        instance = new InitiatorClient();
        return instance;
    }
    
    public void start(InetAddress initiatorIpAddress, int initiatorPortNumber, InetAddress loadBalancerIpAddress, int loadBalancerPortNumber) {
        //
        this.initiatorIpAddress = initiatorIpAddress;
        this.initiatorPortNumber = initiatorPortNumber;
        
        // 
        this.loadBalancerIpAddress = loadBalancerIpAddress;
        this.loadBalancerPortNumber = loadBalancerPortNumber;
        
        // Fetch the singleton MessageManager instance
        messageManager = MessageManager.getInstance();
        
        // Start the MessageManager to listen for Messages from the LoadBalancer
        try {
            messageManager.start(initiatorIpAddress, initiatorPortNumber);
        } catch (IOException e) {
            System.out.println(e);
        }
        
        // 
        register();
        
        //
        messageHandler = new Thread() {
            @Override
            public void run() {
                while (!interrupted()) {
                    if (messageManager.isStopped()) {
                        running = false;
                        break;
                    }

                    // Fetch the next queued Message from the Message Manager
                    MessageInbound nextMessage = messageManager.getNextMessage();

                    if (nextMessage != null) {
                        System.out.printf("NodeClient - INFO: Handling %s Message\n", nextMessage.getType().toString());
                        
                        try {
                            handleMessage(nextMessage);
                        } catch (IllegalArgumentException e) {
                            System.out.printf("InitiatorClient - ERROR: Failed to handle %s Message (%s)\n", nextMessage.getType().toString(), e.getMessage());
                        }
                    }
                }
            }
        };
        
        // Start the message handler on a different Thread so not to block User-Input
        messageHandler.start();

        
        inputReader = new BufferedReader(new InputStreamReader(System.in));
        while (running) {
            // Get the next line input to the Terminal
            String userInputString = "";
            while (userInputString.length() < 1) {
                try {
                    userInputString = inputReader.readLine();
                } catch (IOException e) {
                    System.err.printf("InitiatorClient - ERROR: Failed to read User-Input (%s)\n", e.getMessage());
                }
            }
            
            // Handle the user's input
            handleInput(userInputString);
        }
        
        System.out.println("InitiatorClient - INFO: Stopped");
    }
    
    private void handleMessage(MessageInbound message) throws IllegalArgumentException {
        
    }
    
    private void handleInput(String inputString) {
        System.out.println(inputString);
    }
    
    private void register() {
        
    }
}
