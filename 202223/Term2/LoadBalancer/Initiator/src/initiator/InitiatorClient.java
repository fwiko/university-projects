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
    
    // Input reader for user Terminal input
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
        // Set the IP Address and Port Number of the Initiator client
        this.initiatorIpAddress = initiatorIpAddress;
        this.initiatorPortNumber = initiatorPortNumber;
        
        // Set the IP Address and Port Number of the LoadBalancer Server
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
        
        // Send a REG_INITIATOR Message to the LoadBalancer
        register();
        
        // Start a new Thread to handle incoming Messages after fetching them from the MessageManager
        messageHandler = new Thread() {
            @Override
            public void run() {
                // While the messageHandler thread has not been interrupted (system stopping)
                while (!interrupted()) {
                    // If the messageManager has stopped - break.
                    if (messageManager.isStopped()) {
                        running = false;
                        break;
                    }

                    // Fetch the next queued Message from the Message Manager
                    MessageInbound nextMessage = messageManager.getNextMessage();

                    // If the next Message exists - handle it
                    if (nextMessage != null) {
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
        
        System.out.println("### STARTED INITIATOR CLIENT ###");
        
        // Output the Terminal input options to the InitiatorClient user
        options();
        
        // Initialise the BufferedReader to get Terminal input
        inputReader = new BufferedReader(new InputStreamReader(System.in));
        while (running) {
            // Get the next line input to the Terminal until a non-empty string is fetched
            String userInputString = "";
            while (userInputString.length() < 1) {
                try {
                    System.out.print("Initiator> ");
                    userInputString = inputReader.readLine();
                } catch (IOException e) { 
                    System.err.printf("InitiatorClient - ERROR: Failed to read User-Input (%s)\n", e.getMessage());
                }
            }
            
            // Handle the user's Terminal input
            try {
                handleInput(userInputString);
            } catch (IllegalArgumentException e) {
                System.err.printf("InitiatorClient - ERROR: Failed to handle User-Input (%s)\n", e.getMessage());
            }
        }
        
        System.out.println("InitiatorClient - INFO: Stopped");
    }
    
    private void handleMessage(MessageInbound message) throws IllegalArgumentException {
        switch (message.getType()) {
            case REG_INITIATOR_SUCCESS -> { // ----------------------------------------------------------------------------------------------------------------------------------------------------- REG_INITIATOR_SUCCESS
                
                System.out.println("InitiatorClient - INFO: Successfully registered with LoadBalancer");
                
                break;
            }
            case REG_INITIATOR_FAILURE -> {

                // Set the running flag to false
                running = false;
                
                // Stop the MessageManager (messageReceiver Thread)
                messageManager.stop();
                
                System.err.println("InitiatorClient - ERROR: Failed to register with LoadBalancer");
                
                break;
            }
            case NEW_JOB_SUCCESS -> { // ----------------------------------------------------------------------------------------------------------------------------------------------------------- NEW_JOB_SUCCESS
                
                // The NEW_JOB_SUCCESS Message must have at least 1 additional parameter
                if (message.getParameters().length < 1) { throw new IllegalArgumentException("Insufficient Message parameters"); }
                
                // Set the Job ID value from the first NEW_JOB_SUCCESS Message parameter
                int jobId = -1;
                try {
                    jobId = Integer.parseInt(message.getParameter(0));
                } catch (NumberFormatException e) {
                    throw new IllegalArgumentException("Job ID must be an Integer");
                }
                
                // Output text indicating that a Job was queued successfully
                System.out.printf("InitiatorClient - INFO: Job %d queued successfully\n", jobId);
                
                break;
            }
            case NEW_JOB_FAILURE -> { // ----------------------------------------------------------------------------------------------------------------------------------------------------------- NEW_JOB_FAILURE
                
                // The NEW_JOB_FAILURE Message must have at least 1 additional parameter
                if (message.getParameters().length < 1) { throw new IllegalArgumentException("Insufficient Message parameters"); }
                
                // Output text indicating that the LoadBalancer failed to queue a Job
                System.err.printf("InitiatorClient - ERROR: Failed to queue Job %s\n", message.getParameter(0));
                
                break;
            }
            case FIN_JOB -> { // ------------------------------------------------------------------------------------------------------------------------------------------------------------------- FIN_JOB
                
                // The FIN_JOB Message must have at least 1 additional parameter
                if (message.getParameters().length < 1) { throw new IllegalArgumentException("Insufficient Message parameters"); }
                
                // Output a Message indicating that a Job has finished
                System.err.printf("InitiatorClient - INFO: Job %s has finished\n", message.getParameter(0));
                
                break;
            }
            case INFORMATION -> {
                
                // The INFORMATION Message must have at least 1 additional parameter
                if (message.getParameters().length < 1) { throw new IllegalArgumentException("Insufficient Message parameters"); }
                
                // Output the received LoadBalancer System information to the terminal
                System.out.println("\n\n" + message.getParameter(0));
                
                break;
            }
            default -> {
                throw new IllegalArgumentException("Unknown instruction");
            }
        }
    }
    
    private void handleInput(String inputString) throws IllegalArgumentException {
        
        // Split given input String into separate arguments
        String[] inputArguments = inputString.split(" ");
        
        switch (InputOptionTypes.valueOf(inputArguments[0].toUpperCase())) {
            case JOB -> { // --------------------------------------------------------------------------------------------------------------------------------------------------------------------- JOB
                
                // The JOB command requires one additional parameter (total length 2)
                if (inputArguments.length < 2) { throw new IllegalArgumentException("Usage: JOB <execution_time>"); } 
                
                // Set the Job Execution Time value to the parameter after the command
                int jobExecutionTime = -1;
                try {
                    jobExecutionTime = Integer.parseInt(inputArguments[1]);
                    if (jobExecutionTime < 1) {
                        throw new IllegalArgumentException("Execution time must be greater than one");
                    }
                } catch (NumberFormatException e) {
                    throw new IllegalArgumentException("Execution time must be an Integer");
                }
                
                // Send a NEW_JOB Message to the LoadBalancer to start a new Job for jobExecutionTime Seconds
                MessageOutbound newJobMessage = new MessageOutbound(MessageOutboundType.NEW_JOB, String.valueOf(jobExecutionTime));
                messageManager.sendMessage(newJobMessage,  loadBalancerIpAddress, loadBalancerPortNumber);
                
                break;
            }
            case STOP -> { // -------------------------------------------------------------------------------------------------------------------------------------------------------------------- STOP
                // Stop the MessageManager Thread
                messageManager.stop();

                // Send a STOP_SYSTEM Message to the LoadBalancer
                MessageOutbound loadBalancerStopMessage = new MessageOutbound(MessageOutboundType.STOP_SYSTEM);
                messageManager.sendMessage(loadBalancerStopMessage, loadBalancerIpAddress, loadBalancerPortNumber);
                
                // Set the running flag to false to stop the User-Input loop
                running = false;
                
                break;
            }
            case HELP -> {
                // Output the Terminal input options to the InitiatorClient user
                options();
                
                break;
            }
            case INFO -> {
                
                MessageOutbound infoRequestMessage = new MessageOutbound(MessageOutboundType.GET_INFORMATION);
                messageManager.sendMessage(infoRequestMessage, loadBalancerIpAddress, loadBalancerPortNumber);
                
                break;
            }
            default -> {
                throw new IllegalArgumentException("Unknown command");
            }
        }
    }
    
    private void register() {
        // Send a registration (REG_INITIATOR) Message to the LoadBalancer
        MessageOutbound registrationMessage = new MessageOutbound(MessageOutboundType.REG_INITIATOR, initiatorIpAddress.getHostAddress(), String.valueOf(initiatorPortNumber));
        messageManager.sendMessage(registrationMessage, loadBalancerIpAddress, loadBalancerPortNumber);
    }
    
    private void options() {
        System.out.println("\nJOB <time>      Add a new Job to the LoadBalancer Queue");
        System.out.println("INFO            Get information about the status of the LoadBalancer System");
        System.out.println("HELP            Get information about the status of the LoadBalancer System");
        System.out.println("STOP            Shutdown the LoadBalnacer System, all Nodes, and the Initiator\n");
    }
}
