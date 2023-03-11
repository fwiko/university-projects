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
    
    // Load-Balancer server details
    private InetAddress ipAddress = null;
    private int portNumber = 0;
    private AllocationAlgorithm allocationAlgorithm = null;
    
    // Initiator socket details
    private InetAddress initiatorIpAddress = null;
    private int initiatorPortNumber = -1;
    
    private boolean initiatorRegistered = false;
    
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
        jobManager = JobManager.getInstance();
        nodeManager = NodeManager.getInstance();
        
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
                
                if (initiatorRegistered) { messageManager.sendMessage(new MessageOutbound(MessageOutboundType.FIN_JOB, String.valueOf(job.getIdNumber())), initiatorIpAddress, initiatorPortNumber); }
                
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
                
                InetAddress nodeIpAddress = parseIpAddressArgument(message.getArgument(0));
                
                int nodePortNumber = parseIntegerArgument(message.getArgument(1));
                
                int maximumCapacity = parseIntegerArgument(message.getArgument(2));
                
                if (nodeIpAddress == null || nodePortNumber * maximumCapacity < 0) { throw new IllegalArgumentException("Illegal Message arguments provided"); }
                
                Node node = nodeManager.registerNode(nodeIpAddress, nodePortNumber, maximumCapacity);
                
                messageManager.sendMessage(new MessageOutbound(MessageOutboundType.REG_SUCCESS, String.valueOf(node.getIdNumber())), node.getIpAddress(), node.getPortNumber());
                
                break;
                
            }
            case REG_INITIATOR -> {
            
                // If an insufficient number of additional arguments have been provided (2 needed for REG_INITIATOR), throw an IllegalArgumentException
                if (message.getArguments().length < 2) { throw new IllegalArgumentException("Insufficient number of Message arguments"); }
                
                InetAddress tempInitiatorIpAddress = parseIpAddressArgument(message.getArgument(0));
                
                int tempInitiatorPortNumber = parseIntegerArgument(message.getArgument(1));
                
                if (tempInitiatorIpAddress == null || (tempInitiatorPortNumber < 1 || tempInitiatorPortNumber > 65534)) { throw new IllegalArgumentException("Illegal Message arguments provided"); }
                
                if (initiatorRegistered) {
                    //
                    messageManager.sendMessage(new MessageOutbound(MessageOutboundType.REG_FAILURE), tempInitiatorIpAddress, tempInitiatorPortNumber);
                    
                    System.out.printf("LoadBalancerServer - INFO: An Initiator tried to register on socket %s:%d but an Initiator is already registered\n", tempInitiatorIpAddress.getHostAddress(), tempInitiatorPortNumber);
                    break;
                }
                
                //
                initiatorIpAddress = tempInitiatorIpAddress;
                initiatorPortNumber = tempInitiatorPortNumber;
                
                //
                initiatorRegistered = true;
                
                //
                messageManager.sendMessage(new MessageOutbound(MessageOutboundType.REG_SUCCESS), initiatorIpAddress, initiatorPortNumber);
                
                //
                System.out.printf("LoadBalancerServer - INFO: An Initiator has registered on socket %s:%d\n", initiatorIpAddress.getHostAddress(), initiatorPortNumber);
                
                break;
            
            }
            case NEW_JOB -> {
                
                // If an insufficient number of additional arguments have been provided (1 needed for NEW_JOB), throw an IllegalArgumentException
                if (message.getArguments().length < 1) { throw new IllegalArgumentException("Insufficient number of Message arguments"); }
                
                int executionTime = parseIntegerArgument(message.getArgument(0));
                
                if (executionTime < 1) {
                    messageManager.sendMessage(new MessageOutbound(MessageOutboundType.NEW_JOB_FAILURE), initiatorIpAddress, initiatorPortNumber);
                    throw new IllegalArgumentException("Illegal Message arguments provided");
                }
                
                Job job = jobManager.addNewJob(executionTime);
                
                messageManager.sendMessage(new MessageOutbound(MessageOutboundType.NEW_JOB_SUCCESS, String.valueOf(job.getIdNumber())), initiatorIpAddress, initiatorPortNumber);
                
                break;
                
            }
            case GET_INFO -> {
                
                // FORMAT: registered_nodes, queued_jobs, allocated_jobs, node_summaries[node_id_number, node_allocated_jobs, node_current_usage] ...
                
                String[] nodeSummaries = nodeManager.getNodeSummaries();
                
                String informationString = String.format("%d,%d,%d", nodeSummaries.length, jobManager.getJobQueue().size(), jobManager.getAllocatedJobs().size());
                
                if (nodeSummaries.length > 0) { informationString += String.format(",%s", String.join(",", nodeSummaries)); }
                
                messageManager.sendMessage(new MessageOutbound(MessageOutboundType.INFO, informationString), initiatorIpAddress, initiatorPortNumber);
                
                break;
                
            }
            case STOP_SYSTEM -> {
                
                messageManager.stop();
                
                MessageOutbound stopNodeMessage = new MessageOutbound(MessageOutboundType.STOP_NODE);
                for (Node node : nodeManager.getNodes()) {
                    node.stopKeepAlive();
                    nodeManager.unregisterNode(node);
                    messageManager.sendMessage(stopNodeMessage, node.getIpAddress(), node.getPortNumber());
                }
                
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
