package node;

import java.io.IOException;
import java.net.InetAddress;
import java.util.List;
import node.job.Job;
import node.managers.JobManager;
import node.managers.MessageManager;
import node.messages.MessageInbound;
import node.messages.MessageOutbound;
import node.messages.types.MessageOutboundType;


public class NodeClient {
    // Singleton instance of NodeClient
    private static NodeClient instance = null;
    
    // Flag used to track whether Node is running
    private boolean running = true;
    
    // Node socket and capacity details
    private int nodeIdNumber = -1;
    private int nodePortNumber = -1;
    private int nodeCapacity = -1;
    private InetAddress nodeIpAddress = null;
    
    // LoadBalancerServer socket details
    private InetAddress loadBalancerIpAddress = null;
    private int loadBalancerPortNumber = -1;
    
    // Singleton MessageManager and JobManager instances
    MessageManager messageManager = null;
    JobManager jobManager = null;
    
    
    public static NodeClient getInstance() {
        // If an instance of the NodeClient already exists
        if (instance != null) {
            return instance;
        }
        // Create a new instance of the NodeClient
        instance = new NodeClient();
        return instance;
    }
    
    public void start(int capacity, InetAddress nodeIpAddress, int nodePortNumber, InetAddress loadBalancerIpAddress, int loadBalancerPortNumber) throws IllegalArgumentException {
        // Set the Node socket and capacity details
        this.nodeIpAddress = nodeIpAddress;
        this.nodePortNumber = nodePortNumber;
        this.nodeCapacity = capacity;
        
        // Set the LoadBalancerServer socket details
        this.loadBalancerIpAddress = loadBalancerIpAddress;
        this.loadBalancerPortNumber = loadBalancerPortNumber;
        
        // Fetch the singleton MessageManager and JobManager instances
        messageManager = MessageManager.getInstance();
        jobManager = JobManager.getInstance();
        
        // Attempt to start the MessageManager
        try {
            messageManager.start(nodeIpAddress, nodePortNumber);
        } catch (IOException e) {
            System.out.println(e);
        }
        
        // Send a registration (REG_NODE) Message to the LoadBalancer
        register();
        
        // While the Node is running
        while (running) {
            // If the MessageManager has stopped - exit
            if (messageManager.isStopped()) {
                break;
            }
            
            // Fetch the next queued Message from the Message Manager
            MessageInbound nextMessage = messageManager.getNextMessage();
            
            // If there is a queued Message available
            if (nextMessage != null) {
                System.out.printf("NodeClient - INFO: Handling %s Message\n", nextMessage.getType().toString());
                
                // Attempt to handle the retreived Message
                try {
                    handleMessage(nextMessage);
                } catch (IllegalArgumentException e) {
                    System.out.printf("NodeClient - ERROR: Failed to handle %s Message (%s)\n", nextMessage.getType().toString(), e.getMessage());
                }
            }
            
            // Retreive a list of completed Jobs (if any)
            List<Job> finishedJobs = jobManager.getFinishedJobs();
            if (!finishedJobs.isEmpty()) {
                // Iterate through the list of completed Jobs
                for(Job job : finishedJobs) {
                    System.out.printf("NodeClient - INFO: Job %d with Execution Time %d has finished\n", job.getIdNumber(), job.getExecutionTime());
                    
                    // Send a finished Job (FIN_JOB) Message to the LoadBalancer for the current Job - specifying the ID
                    MessageOutbound finishedJobMessage = new MessageOutbound(MessageOutboundType.FIN_JOB, String.valueOf(job.getIdNumber()));
                    messageManager.sendMessage(finishedJobMessage, loadBalancerIpAddress, this.loadBalancerPortNumber);
                }
            }
        }

        // If the MessageManager has not stopped but the NodeClient has
        if (!messageManager.isStopped()) {
            // Stop the MessageManager (messageReceiver Thread)
            messageManager.stop();
        }

        System.out.println("NodeClient - INFO: Stopped");
    }
    
    private void handleMessage(MessageInbound message) throws IllegalArgumentException {
        switch (message.getType()) {
            case NEW_JOB -> {
                if (message.getParameters().length < 2) { throw new IllegalArgumentException("Insufficient Message parameters"); }
                
                // Attempt to parse the Job ID Number parameter from the NEW_JOB Message
                int jobIdNumber = -1;
                try {
                    jobIdNumber = Integer.parseInt(message.getParameter(0));
                } catch (NumberFormatException e) {
                    //
                    MessageOutbound newJobFailureMessage = new MessageOutbound(MessageOutboundType.NEW_JOB_FAILURE, "Job ID Number is not an Integer");
                    messageManager.sendMessage(newJobFailureMessage, loadBalancerIpAddress, loadBalancerPortNumber);
                    
                    throw new IllegalArgumentException("Job ID Number is not an Integer");
                }
                
                // Attempt to parse the Job Execution Time parameter from the NEW_JOB Message
                int jobExecutionTime = -1;
                try {
                    jobExecutionTime = Integer.parseInt(message.getParameter(1));
                } catch (NumberFormatException e) {
                    //
                    MessageOutbound newJobFailureMessage = new MessageOutbound(MessageOutboundType.NEW_JOB_FAILURE, "Job Execution Time is not an Integer");
                    messageManager.sendMessage(newJobFailureMessage, loadBalancerIpAddress, loadBalancerPortNumber);
                    
                    throw new IllegalArgumentException("Job Execution Time is not an Integer");
                }
                
                // Tell the JobManager to start a new Job with the specified ID Number for the specified time
                jobManager.startJob(jobIdNumber, jobExecutionTime);
                
                // Send a new job received success (NEW_JOB_SUCCESS) Message to the LoadBalancer
                MessageOutbound newJobSuccessMessage = new MessageOutbound(MessageOutboundType.NEW_JOB_SUCCESS);
                messageManager.sendMessage(newJobSuccessMessage, loadBalancerIpAddress, loadBalancerPortNumber);
                
                break;
            }
            case REG_NODE_SUCCESS -> {
                if (message.getParameters().length < 1) { throw new IllegalArgumentException("Insufficient Message parameters"); }
                
                // Attempt to parse the Node ID Number parameter of the REG_NODE_SUCCESS Message
                try {
                    nodeIdNumber = Integer.parseInt(message.getParameter(0));
                } catch (NumberFormatException e) {
                    throw new IllegalArgumentException("Node ID Number is not an Integer");
                }
                
                System.out.printf("NodeClient - INFO: Node ID Number set to %d\n", nodeIdNumber);
                
                break;
            }
            case REG_NODE_FAILURE -> {
                // Set the running flag to false
                running = false;
                
                // Stop the MessageManager (messageReceiver Thread)
                messageManager.stop();
                
                System.err.println("NodeClient - ERROR: Failed to register with Load-Balancer");
                
                break;
            }
            case NOT_REGISTERED -> {
                // Tell the JobManager to stop all running Jobs
                jobManager.stopAllJobs();
                
                // Send a registration (REG_NODE) Message to the LoadBalancer
                register();
                
                break;
            }
            case IS_ALIVE -> {
                // Send a alive acknowledgement (ACK_IS_ALIVE) Message to the LoadBalancer
                MessageOutbound isAliveConfirmationMessage = new MessageOutbound(MessageOutboundType.ACK_IS_ALIVE);
                messageManager.sendMessage(isAliveConfirmationMessage, loadBalancerIpAddress, loadBalancerPortNumber);
                
                break;
            }
            case STOP_NODE -> {
                
                // Set the running flag to false
                running = false;
                
                // Stop the MessageManager (messageReceiver Thread)
                messageManager.stop();
                
                // Tell the JobManager to stop all running Jobs
                jobManager.stopAllJobs();
                
                break;
            }
            default -> throw new IllegalArgumentException(String.format("Unknown instruction"));
        }
    }
    
    private void register() {
        // Send a registration (REG_NODE) Message to the LoadBalancer
        MessageOutbound registrationMessage = new MessageOutbound(MessageOutboundType.REG_NODE, nodeIpAddress.getHostAddress(), String.valueOf(nodePortNumber), String.valueOf(nodeCapacity));
        messageManager.sendMessage(registrationMessage, loadBalancerIpAddress, loadBalancerPortNumber);
    }
}