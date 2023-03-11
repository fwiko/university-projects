package initiator;

import initiator.managers.MessageManager;
import initiator.messages.MessageInbound;
import initiator.messages.MessageOutbound;
import initiator.messages.types.MessageOutboundType;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.InetAddress;

public class InitiatorClient {
    
    // Initiator socket details
    InetAddress ipAddress = null;
    int portNumber = -1;
    
    // Load-Balancer socket details
    InetAddress loadBalancerIpAddress = null;
    int loadBalancerPortNumber = -1;
    
    boolean registered = false;
    
    // Thread for handling incoming Messages without blocking terminal User-input
    Thread messageHandler = null;
    
    // BufferedReader used in conjunction with an InputStreamReader to accept terminal User-input
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
        
        // Handle incoming Messages on a different Thread to prevent blocking user-input
        messageHandler = new Thread() {
            @Override
            public void run() {
                while (!interrupted() && !messageManager.isStopped()) {
                    //
                    MessageInbound message = messageManager.getNextQueuedMessage();
                    
                    //
                    if (message == null) { continue; }
                    
                    //
                    try {
                        handleMessage(message);
                    } catch (IllegalArgumentException exception) {
                        System.err.printf("InitiatorClient - ERROR: Could not handle %s Message (%s)", message.getType(), exception.getMessage());
                    }
                }
            }
        };
        
        //
        messageHandler.start();
        
        //
        register();
        
        System.out.println("### STARTED INITIATOR CLIENT ###");
        
        //
        showOptions();
        
        //
        inputReader = new BufferedReader(new InputStreamReader(System.in));
        
        //
        while (!messageManager.isStopped()) {
            String commandString = "";
            while (commandString.length() < 1) {
                System.out.print("Initiator> ");
                
                //
                try {
                    commandString = inputReader.readLine();
                } catch (IOException exception) {
                    System.err.printf("InitiatorClient - ERROR: Failed to get user-input (%s)\n", exception.getMessage());
                }
            }
            
            //
            try {
                handleCommand(commandString);
            } catch (IllegalArgumentException exception) {
                
            }
        }
        
        System.out.println("InitiatorClient - INFO: Stopped...");
    }
    
    private void handleCommand(String commandString) throws IllegalArgumentException {
        
        // Split given input String into separate arguments
        String[] args = commandString.split(" ");
        
        switch(args[0].toUpperCase()) {
            case "JOB" -> {

                // Check if registered
                if (!registered) {
                    System.out.println("InitiatorClient - INFO: Unable to create a new Job (not registered)");
                    register();
                }
                
                // If an insufficient number of additional arguments have been provided (1 needed for JOB command), throw an IllegalArgumentException
                if (args.length - 1 < 1) { throw new IllegalArgumentException("Usage: JOB <execution_time>"); } 
                
                //
                int executionTime = parseIntegerArgument(args[1]);
                
                // If the input Exeuction Time value is not an Integer or is negative, throw an IllegalArgumentException
                if (executionTime < 1) { throw new IllegalArgumentException("Illegal command arguments provided"); }
                
                // Send a NEW_JOB Message to the Load-Balancer socket with the given Execution Time value as an additional argument
                messageManager.sendMessage(new MessageOutbound(MessageOutboundType.NEW_JOB, String.valueOf(executionTime)), loadBalancerIpAddress, loadBalancerPortNumber);
                
                break;
                
            }
            case "STOP" -> {
                
                // Check if registered
                if (!registered) {
                    System.out.println("InitiatorClient - INFO: Unable to stop the Load-Balancer (not registered)");
                    register();
                }
                
                // Stop the Message Manager's Message receiver Thread
                messageManager.stop();
                
                // Send a STOP_SYSTEM Message to the Load-Balancer socket
                messageManager.sendMessage(new MessageOutbound(MessageOutboundType.STOP_SYSTEM), loadBalancerIpAddress, loadBalancerPortNumber);
                
                break;
                
            }
            case "INFO" -> {
                
                // Send a GET_INFO Message to the Load-Balancer socket
                messageManager.sendMessage(new MessageOutbound(MessageOutboundType.GET_INFO), loadBalancerIpAddress, loadBalancerPortNumber);
                
                break;
                
            }
            case "HELP" -> {
                
                // Display a list of command options for the User
                showOptions();
                
                break;
                
            }
            default -> {
                throw new IllegalArgumentException("Unknown Command");
            }
        }
        
    }
    
    private void handleMessage(MessageInbound message) throws IllegalArgumentException {
        switch (message.getType()) {
            case NEW_JOB_SUCCESS -> {
                
                // If an insufficient number of additional arguments have been provided (1 needed for NEW_JOB_SUCCESS), throw an IllegalArgumentException
                if (message.getArguments().length < 1) { throw new IllegalArgumentException("Insufficient number of Message arguments"); } 
                
                System.out.printf("\rInitiatorClient - INFO: The Load-Balancer has successfully queued Job %s\n", message.getArgument(0));
                
                break;
                
            }
            case NEW_JOB_FAILURE -> {
                
                // If an insufficient number of additional arguments have been provided (1 needed for NEW_JOB_FAILURE), throw an IllegalArgumentException
                if (message.getArguments().length < 1) { throw new IllegalArgumentException("Insufficient number of Message arguments"); } 
                
                System.err.printf("\rInitiatorClient - ERROR: The Load-Balancer failed to queue Job %s\n", message.getArgument(0));
                
                break;
                
            }
            case REG_SUCCESS -> {
                
                registered = true;
                
                System.out.printf("\rInitiatorClient - INFO: Successfully registered with the Load-Balancer on socket %s:%d\n", loadBalancerIpAddress.getHostAddress(), loadBalancerPortNumber);
                
                break;
                
            }
            case REG_FAILURE -> {
                
                System.err.printf("\rInitiatorClient - ERROR: Failed to register with the Load-Balancer on socket %s:%d\n", loadBalancerIpAddress.getHostAddress(), loadBalancerPortNumber);
                
                break;
                
            }
            case FIN_JOB -> {
                
                // If an insufficient number of additional arguments have been provided (1 needed for FIN_JOB), throw an IllegalArgumentException
                if (message.getArguments().length < 1) { throw new IllegalArgumentException("Insufficient number of Message arguments"); } 
                
                System.out.printf("\rInitiatorClient - INFO: The execution of Job %s has finished\n", message.getArgument(0));
                
                break;
                
            }
            case INFO -> {
                
                // If an insufficient number of additional arguments have been provided (minimum 3 needed for INFO), throw an IllegalArgumentException
                if (message.getArguments().length < 1) { throw new IllegalArgumentException("Insufficient number of Message arguments"); } 
                
                String informationString = String.format("""
                                                         Registered Nodes: %s
                                                         Queued Jobs: %s
                                                         Allocated Jobs: %s
                                                         """, message.getArgument(0), message.getArgument(1), message.getArgument(2));
                
                if (message.getArguments().length > 3) {
                    for (int i = 5; i < message.getArguments().length; i+=3) {
                        informationString += String.format("\nNode #%s [%s Jobs, %s Usage]", message.getArgument(i-2), message.getArgument(i-1), message.getArgument(i));
                    }
                }
                
                System.out.printf("\rInitiatorClient - INFO: Received information from the Load-Balancer \n\n%s\n", informationString);
                
                break;
                
            }
            default -> {
                
                throw new IllegalArgumentException("Unknown Message type");
                
            }
        }
    }
    
    private void showOptions() {
        System.out.println(
                """
                \n
                JOB <execution_time>    Add a new Job to the LoadBalancer Queue
                INFO                    Get information about the status of the Load-Balancer System
                HELP                    Output the list (this) of available commands
                STOP                    Shutdown the LoadBalnacer System, all Nodes, and the Initiator
                """
        );
    }
    
    private void register() {
        // Create a new MessageOutbound object with the REG_INITIATOR Type and send to the Load-Balancer socket
        messageManager.sendMessage(new MessageOutbound(MessageOutboundType.REG_INITIATOR, ipAddress.getHostAddress(), String.valueOf(portNumber)), loadBalancerIpAddress, loadBalancerPortNumber);
    }
    
    private int parseIntegerArgument(String value) {
        // Attempt to parse the provided "value" String to an Integer
        try {
            return Integer.parseInt(value);
        } catch (NumberFormatException exception) { // Handle a NumberFormatException and return -1 (invalid integer)
            return -1;
        }
    }
    
}
