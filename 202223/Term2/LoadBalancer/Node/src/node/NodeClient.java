package node;

import java.io.IOException;
import java.net.InetAddress;
import node.job.Job;
import node.managers.JobManager;
import node.managers.MessageManager;
import node.messages.MessageInbound;
import node.messages.MessageOutbound;
import node.messages.types.MessageOutboundType;

public class NodeClient {
    // Maximum capacity of the Node - communicated with Load-Balancer
    int maximumCapacity = -1;
    
    // Node socket details
    InetAddress ipAddress = null;
    int portNumber = -1;
    
    // Load-Balancer socket details
    InetAddress loadBalancerIpAddress = null;
    int loadBalancerPortNumber = -1;
    
    // ID number of Node - received upon successful registration
    int nodeIdNumber = -1;
    
    // Message and Job Manager class singletons
    MessageManager messageManager = null;
    JobManager jobManager = null;
    
    public NodeClient(int maximumCapacity, InetAddress ipAddress, int portNumber, InetAddress loadBalancerIpAddress, int loadBalancerPortNumber) {
        this.maximumCapacity = maximumCapacity;
        this.ipAddress = ipAddress;
        this.portNumber = portNumber;
        this.loadBalancerIpAddress = loadBalancerIpAddress;
        this.loadBalancerPortNumber = loadBalancerPortNumber;
    }
    
    public void start() {
        // Get the Message and Job Manager singleton instances
        messageManager = MessageManager.getInstance();
        jobManager = JobManager.getInstance();
        
        // Attempt to start the Message Manager, listening on the Node socket
        try {
            messageManager.start(ipAddress, portNumber);
        } catch (IOException exception) { // Handle an IOException if the Datagram Channel failed to bind to the Node socket details
            System.err.printf("NodeClient - ERROR: IOException when opening Datagram Channel on %s:%d\n", ipAddress.getHostAddress(), portNumber);
            System.exit(1);
        }
        
        // Send a REG_NODE (registration) Message to the Load-Balancer socket
        register();
        
        while (!messageManager.isStopped()) {
            // Send FIN_JOB Message(s) to the Load-Balancer socket for every finished Job
            for (Job job : jobManager.getAllFinishedJobs()) {
                System.out.printf("NodeClient - INFO: Job %d with %d second Execution Time has finished\n", job.getIdNumber(), job.getExecutionTime());
                messageManager.sendMessage(new MessageOutbound(MessageOutboundType.FIN_JOB, String.valueOf(job.getIdNumber())), loadBalancerIpAddress, loadBalancerPortNumber);
            }
            
            // Get the next queued Message from the Message Manager (FIFO)
            MessageInbound message = messageManager.getNextQueuedMessage();
            
            // If there is no Message in the queue, jump to the top of the loop
            if (message == null) { continue; }
            
            // Attempt to handle the Message using the Message handler switch statement
            try {
                handleMessage(message);
            } catch (IllegalArgumentException exception) { // Handle an IllegalArgumentException if insufficient or illegal arguments have been provideds
                System.err.printf("NodeClient - ERROR: Could not handle %s Message (%s)\n", message.getType(), exception.getMessage());
            }
        }
        
        System.out.println("NodeClient - INFO: Stopped...");
    }
    
    private void handleMessage(MessageInbound message) throws IllegalArgumentException {
        switch (message.getType()) {
            case IS_ALIVE -> {
                
                // Create a new MessageOutbound object with the ACK_IS_ALIVE Type and send to the Load-Balancer socket with the Node ID Number as an additional argument
                messageManager.sendMessage(new MessageOutbound(MessageOutboundType.ACK_IS_ALIVE, String.valueOf(nodeIdNumber)), loadBalancerIpAddress, loadBalancerPortNumber);
                
                break;
                
            }
            case NEW_JOB -> {
                
                // If an insufficient number of additional arguments have been provided (2 needed for NEW_JOB), throw an IllegalArgumentException
                if (message.getArguments().length < 2) { throw new IllegalArgumentException("Insufficient number of Message arguments"); }
                
                // Parse the two additional arguments (ID Number and Execution Time) as Integers
                int idNumber = parseIntegerArgument(message.getArgument(0));
                int executionTime = parseIntegerArgument(message.getArgument(1));
                
                // If either value is an invalid Integer or is negative, throw an IllegalArgumentException
                if (idNumber * executionTime < 0) { throw new IllegalArgumentException("Illegal Message arguments provided"); }
                
                // Start executing the new Job by sending the Job ID and Execution Time to the Job Manager
                jobManager.startJob(idNumber, executionTime);
                
                // Create a new MessageOutbound object with the NEW_JOB_SUCCESS Type and send to the Load-Balancer socket with the Job ID as an additional argument
                messageManager.sendMessage(new MessageOutbound(MessageOutboundType.NEW_JOB_SUCCESS, String.valueOf(idNumber)), loadBalancerIpAddress, loadBalancerPortNumber);
                
                break;
                
            }
            case REG_FAILURE -> {
                
                // Stop the Message Manager (stops the Message receiving Thread that the system relies upon)
                messageManager.stop();
                
                break;
                
            }
            case REG_SUCCESS -> {
                
                // If an insufficient number of additional arguments have been provided (1 needed for REG_SUCCESS), throw an IllegalArgumentException
                if (message.getArguments().length < 1) { throw new IllegalArgumentException("Insufficient number of Message arguments"); }
                
                // Parse the additional argument (ID Number) as an Integer
                int idNumber = parseIntegerArgument(message.getArgument(0));
                
                // If the provided ID Number argument is invalid or negative, throw an IllegalArgumentException
                if (idNumber < 1) { throw new IllegalArgumentException("Illegal Message arguments provided"); }
                
                // Set the class "nodeIDNumber" value to the given argument
                nodeIdNumber = idNumber;
                
                break;
                
            }
            case STOP_NODE -> {
                
                // Stop the Message Manager (stops the Message receiving Thread that the system relies upon)
                messageManager.stop();
                
                // Tell the Job Manager to stop any running Job Threads (Jobs with status == JobStatus.RUNNING)
                jobManager.stopAllRunningJobs();
                
                break;
                
            } default -> {
                throw new IllegalArgumentException("Unknown Message type");
            }
        }
    }
    
    private void register() {
        // Create a new MessageOutbound object with the REG_NODE Type and send to the Load-Balancer socket
        messageManager.sendMessage(new MessageOutbound(MessageOutboundType.REG_NODE, ipAddress.getHostAddress(), String.valueOf(portNumber), String.valueOf(maximumCapacity)), loadBalancerIpAddress, loadBalancerPortNumber);
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
