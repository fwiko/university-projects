package loadbalancer;

import java.io.IOException;
import java.net.InetAddress;
import java.net.UnknownHostException;
import loadbalancer.job.Job;
import loadbalancer.managers.JobManager;
import loadbalancer.managers.MessageManager;
import loadbalancer.managers.NodeManager;
import loadbalancer.messages.MessageInbound;
import loadbalancer.messages.MessageOutbound;
import loadbalancer.messages.types.MessageOutboundType;
import loadbalancer.node.Node;

public class LoadBalancerServer {
    
    private InetAddress ipAddress = null;
    private int portNumber = 0;
    private AllocationAlgorithm allocationAlgorithm = null;
    
    // Message, Job, and Node Manager class singletons
    private MessageManager messageManager = null;
    private JobManager jobManager = null;
    private NodeManager nodeManager = null;
        
    public LoadBalancerServer(InetAddress ipAddress, int portNumber, AllocationAlgorithm allocationAlgorithm) {
        this.ipAddress = ipAddress;
        this.portNumber = portNumber;
        this.allocationAlgorithm = allocationAlgorithm;
    }
    
    public void start() {
        messageManager = MessageManager.getInstance();
        
        // Attempt to start the Message Manager, listening on the LoadBalancerServer socket
        try {
            messageManager.start(ipAddress, portNumber);
        } catch (IOException exception) {
            System.err.printf("LoadBalancerServer - ERROR: IOException when opening Datagram Channel on %s:%d\n", ipAddress.getHostAddress(), portNumber);
            System.exit(1);
        }
        
        while (!messageManager.isStopped()) {
            
            // Get the next Job from the Job Manager's queue (FIFO)
            Job job = jobManager.getNextQueuedJob();
            
            if (job != null) {
                // Allocate the Job to the next qualifying Node fetched using the specified Allocation Algorithm (NORMAL, WEIGHTED)
                Node node = nodeManager.getNextQualifyingNode(allocationAlgorithm);
                
                if (node != null) {
                    jobManager.allocateJob(job, node);
                    messageManager.sendMessage(new MessageOutbound(MessageOutboundType.NEW_JOB, String.valueOf(job.getIdNumber()), String.valueOf(job.getExecutionTime())), node.getIpAddress(), node.getPortNumber());
                }
            }
            
            // Get the next queued Message from the Message Manager (FIFO)
            MessageInbound message = messageManager.getNextQueuedMessage();
            
            if (message != null) {
                handleMessage(message);
            }
            
        }
        
        System.out.println("LoadBalancerServer - INFO: Stopped...");
    }
    
    private void handleMessage(MessageInbound message) throws IllegalArgumentException {
        switch (message.getType()) {
            case ACK_IS_ALIVE -> {
                
                // If an insufficient number of additional arguments have been provided (1 needed for ACK_IS_ALIVE), throw an IllegalArgumentException
                if (message.getArguments().length < 1) { throw new IllegalArgumentException("Insufficient number of Message arguments"); }
                
                int nodeIdNumber = parseIntegerArgument(message.getArgument(0));
                
                if (nodeIdNumber < 1) { throw new IllegalArgumentException("Illegal Message arguments provided"); }
                
                Node node = nodeManager.getNodeById(nodeIdNumber);
                
                if (node == null) {
                    System.err.printf("LoadBalancerServer - ERROR: Failed to handle ACK_IS_ALIVE Message (Node with ID %d is no longer registered)\n", nodeIdNumber);
                    break;
                }
                
                node.resetWarnings();
                        
                break;
                
            }
            case FIN_JOB -> {
                
                // If an insufficient number of additional arguments have been provided (1 needed for FIN_JOB), throw an IllegalArgumentException
                if (message.getArguments().length < 1) { throw new IllegalArgumentException("Insufficient number of Message arguments"); }
                
                int jobIdNumber = parseIntegerArgument(message.getArgument(0));
                
                if (jobIdNumber < 1) { throw new IllegalArgumentException("Illegal Message arguments provided"); }
                
                Job job = jobManager.getAllocatedJobById(jobIdNumber);
                
                if (job == null) {
                    System.err.printf("Allocated Job with ID Number %d does not exist\n", jobIdNumber);
                    break;
                }
                
                jobManager.deallocateJob(job);
                
                System.out.printf("LoadBalancerServer - INFO: Job %d has finished\n", jobIdNumber);
                
                break;
                
            }
            case NEW_JOB_FAILURE -> {
                
                // If an insufficient number of additional arguments have been provided (1 needed for NEW_JOB_FAILURE), throw an IllegalArgumentException
                if (message.getArguments().length < 1) { throw new IllegalArgumentException("Insufficient number of Message arguments"); }
                
                int jobIdNumber = parseIntegerArgument(message.getArgument(0));
                
                if (jobIdNumber < 1) { throw new IllegalArgumentException("Illegal Message arguments provided"); }
                
                jobManager.deallocateJob(jobManager.getAllocatedJobById(jobIdNumber));
                
                System.err.printf("LoadBalancerServer - ERROR: Allocation of Job %d was unsuccessful\n", jobIdNumber);
                
                break;
                
            }
            case NEW_JOB_SUCCESS -> {
                
                // If an insufficient number of additional arguments have been provided (1 needed for NEW_JOB_SUCCESS), throw an IllegalArgumentException
                if (message.getArguments().length < 1) { throw new IllegalArgumentException("Insufficient number of Message arguments"); }
                
                int jobIdNumber = parseIntegerArgument(message.getArgument(0));
                
                if (jobIdNumber < 1) { throw new IllegalArgumentException("Illegal Message arguments provided"); }
                
                System.out.printf("LoadBalancerServer - INFO: Allocation of Job %d was successful\n", jobIdNumber);
                
                break;
                
            }
            case REG_NODE -> {

                // If an insufficient number of additional arguments have been provided (3 needed for REG_NODE), throw an IllegalArgumentException
                if (message.getArguments().length < 3) { throw new IllegalArgumentException("Insufficient number of Message arguments"); }
                
                InetAddress ipAddress = parseIpAddressArgument(message.getArgument(0));
                
                int portNumber = parseIntegerArgument(message.getArgument(1));
                
                int maximumCapacity = parseIntegerArgument(message.getArgument(2));
                
                if (ipAddress == null || portNumber * maximumCapacity < 0) { throw new IllegalArgumentException("Illegal Message arguments provided"); }
                
                Node node = nodeManager.registerNode(ipAddress, portNumber, maximumCapacity);
                
                messageManager.sendMessage(new MessageOutbound(MessageOutboundType.REG_NODE_SUCCESS, String.valueOf(node.getIdNumber())), node.getIpAddress(), node.getPortNumber());
                
                break;
                
            }
            default -> {
                throw new IllegalArgumentException("Unknown Message type");
            }
        }
    }
    
    private int parseIntegerArgument(String value) {
        // Attempt to parse the provided "value" String to an Integer
        try {
            return Integer.parseInt(value);
        } catch (NumberFormatException exception) { // Handle a NumberFormatException and return -1 (invalid Integer
            return -1;
        }
    }
    
    private InetAddress parseIpAddressArgument(String value) {
        try {
            return InetAddress.getByName(value);
        } catch (UnknownHostException exception) {
            return null;
        }
    }
    
}
