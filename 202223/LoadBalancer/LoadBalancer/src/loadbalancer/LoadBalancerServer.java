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
    
    // Controller socket details
    private InetAddress controllerIpAddress = null;
    private int controllerPortNumber = -1;
    
    // Flag used to check whether the Controller is registered
    private boolean controllerRegistered = false;
    
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
                
                // Parse the first additional argument (Node ID Number) as an Integer
                int nodeIdNumber = parseIntegerArgument(message.getArgument(0));
                
                // If the given Node ID Number is not a valid Integer or is negative, throw an IllegalArgumentException
                if (nodeIdNumber < 1) { throw new IllegalArgumentException("Illegal Message arguments provided"); }
                
                // Fetch the Node object with hthe given ID Number
                Node node = nodeManager.getNodeById(nodeIdNumber);
                
                // If no Node with the given ID Number exists - output an error Message
                if (node == null) {
                    System.err.printf("LoadBalancerServer - ERROR: Failed to handle ACK_IS_ALIVE Message (Node with ID %d is no longer registered)\n", nodeIdNumber);
                    break;
                }
                
                // Reset the given Node's warnings to zero (0)
                node.resetWarnings();
                        
                break;
                
            }
            case FIN_JOB -> {
                
                // If an insufficient number of additional arguments have been provided (1 needed for FIN_JOB), throw an IllegalArgumentException
                if (message.getArguments().length < 1) { throw new IllegalArgumentException("Insufficient number of Message arguments"); }
                
                // Parse the first additional argument (Job ID Number) as an Integer
                int jobIdNumber = parseIntegerArgument(message.getArgument(0));
                
                // If the given Job ID Number is not a valid Integer or is negative, throw an IllegalArgumentException
                if (jobIdNumber < 1) { throw new IllegalArgumentException("Illegal Message arguments provided"); }
                
                // Fetch the Job object with the given ID Number
                Job job = jobManager.getAllocatedJobById(jobIdNumber);
                
                // If no Job with the given ID Number exists - output an error Message
                if (job == null) {
                    System.err.printf("Allocated Job with ID Number %d does not exist\n", jobIdNumber);
                    break;
                }
                
                // Remove the Job allocation record from the Job Manager
                jobManager.deallocateJob(job);
                
                // If an controller is registered with the Load-Balancer - send a FIN_JOB Message to the Controller socket
                if (controllerRegistered) { messageManager.sendMessage(new MessageOutbound(MessageOutboundType.FIN_JOB, String.valueOf(job.getIdNumber())), controllerIpAddress, controllerPortNumber); }
                
                System.out.printf("LoadBalancerServer - INFO: Job %d has finished\n", jobIdNumber);
                
                break;
                
            }
            case NEW_JOB_FAILURE -> {
                
                // If an insufficient number of additional arguments have been provided (1 needed for NEW_JOB_FAILURE), throw an IllegalArgumentException
                if (message.getArguments().length < 1) { throw new IllegalArgumentException("Insufficient number of Message arguments"); }
                
                // Parse the first additional argument (Job ID Number) as an Integer
                int jobIdNumber = parseIntegerArgument(message.getArgument(0));
                
                // If the given Job ID Number is not a valid Integer or is negative, throw an IllegalArgumentException
                if (jobIdNumber < 1) { throw new IllegalArgumentException("Illegal Message arguments provided"); }
                
                // Remove the Job allocation record from the Job Manager
                jobManager.deallocateJob(jobManager.getAllocatedJobById(jobIdNumber));
                
                System.err.printf("LoadBalancerServer - ERROR: Allocation of Job %d was unsuccessful\n", jobIdNumber);
                
                break;
                
            }
            case NEW_JOB_SUCCESS -> {
                
                // If an insufficient number of additional arguments have been provided (1 needed for NEW_JOB_SUCCESS), throw an IllegalArgumentException
                if (message.getArguments().length < 1) { throw new IllegalArgumentException("Insufficient number of Message arguments"); }
                
                // Parse the first additional argument (Job ID Number) as an Integer
                int jobIdNumber = parseIntegerArgument(message.getArgument(0));
                
                // If the given Job ID Number is not a valid Integer or is negative, throw an IllegalArgumentException
                if (jobIdNumber < 1) { throw new IllegalArgumentException("Illegal Message arguments provided"); }
                
                System.out.printf("LoadBalancerServer - INFO: Allocation of Job %d was successful\n", jobIdNumber);
                
                break;
                
            }
            case REG_NODE -> {

                // If an insufficient number of additional arguments have been provided (3 needed for REG_NODE), throw an IllegalArgumentException
                if (message.getArguments().length < 3) { throw new IllegalArgumentException("Insufficient number of Message arguments"); }
                
                // Parse the first additional argument (Node IP Address) as an InetAddress
                InetAddress nodeIpAddress = parseIpAddressArgument(message.getArgument(0));
                
                // Parse the second additional argument (Node Port Number) as an Integer
                int nodePortNumber = parseIntegerArgument(message.getArgument(1));
                
                // Parse the third additional argument (Maxmimum Capacity) as an Integer
                int maximumCapacity = parseIntegerArgument(message.getArgument(2));
                
                // If any of the provided arguments are invalid, throw an IllegalArgumentException
                if (nodeIpAddress == null || nodePortNumber * maximumCapacity < 0) { throw new IllegalArgumentException("Illegal Message arguments provided"); }
                
                // Register the Node with the Node Manager
                Node node = nodeManager.registerNode(nodeIpAddress, nodePortNumber, maximumCapacity);
                
                // Send a REG_SUCCESS Message to the Node
                messageManager.sendMessage(new MessageOutbound(MessageOutboundType.REG_SUCCESS, String.valueOf(node.getIdNumber())), node.getIpAddress(), node.getPortNumber());
                
                break;
                
            }
            case REG_CONTROLLER -> {
            
                // If an insufficient number of additional arguments have been provided (2 needed for REG_CONTROLLER), throw an IllegalArgumentException
                if (message.getArguments().length < 2) { throw new IllegalArgumentException("Insufficient number of Message arguments"); }
                
                // Parse the first additional argument (Controller IP Address) as an InetAddress
                InetAddress tempControllerIpAddress = parseIpAddressArgument(message.getArgument(0));
                
                // Parse the second additional argument (Controller Port Number) as an Integer
                int tempControllerPortNumber = parseIntegerArgument(message.getArgument(1));
                
                // If either provided argument is invalid, throw an IllegalArgumentException
                if (tempControllerIpAddress == null || (tempControllerPortNumber < 1 || tempControllerPortNumber > 65534)) { throw new IllegalArgumentException("Illegal Message arguments provided"); }
                
                // If an Controller has already registered - replace it
                if (controllerRegistered) {
                    
                    controllerRegistered = false;
                    
                    // Send a STOP_CONTROLLER Message to the old registered Controller
                    messageManager.sendMessage(new MessageOutbound(MessageOutboundType.STOP_CONTROLLER), controllerIpAddress, controllerPortNumber);
                    
                    System.out.printf("LoadBalancerServer - INFO: A new Controller has requested to register, the old Controller has been stopped\n", tempControllerIpAddress.getHostAddress(), tempControllerPortNumber);
                    
                    break;
                }
                
                // Set the (permanent) Controller IP Address and Port Number values to the ones given
                controllerIpAddress = tempControllerIpAddress;
                controllerPortNumber = tempControllerPortNumber;
                
                // Set the "controllerRegistered" flag to true for line 215 in future
                controllerRegistered = true;
                
                // Send a REG_SUCCESS Message to the Controller
                messageManager.sendMessage(new MessageOutbound(MessageOutboundType.REG_SUCCESS), controllerIpAddress, controllerPortNumber);
                
                System.out.printf("LoadBalancerServer - INFO: Controller registered on socket %s:%d\n", controllerIpAddress.getHostAddress(), controllerPortNumber);
                
                break;
            
            }
            case NEW_JOB -> {
                
                // If an insufficient number of additional arguments have been provided (1 needed for NEW_JOB), throw an IllegalArgumentException
                if (message.getArguments().length < 1) { throw new IllegalArgumentException("Insufficient number of Message arguments"); }
                
                // Parse the first additional argument (Execution Time) as an Integer
                int executionTime = parseIntegerArgument(message.getArgument(0));
                
                // If the Execution Time argument is an invalid Integer or is negative, send a NEW_JOB_FAILURE Message to the controller and throw an IllegalArgumentException
                if (executionTime < 1) {
                    messageManager.sendMessage(new MessageOutbound(MessageOutboundType.NEW_JOB_FAILURE), controllerIpAddress, controllerPortNumber);
                    throw new IllegalArgumentException("Illegal Message arguments provided");
                }
                
                // Tell the Job Manager to queue a new Job with the given Execution Time
                Job job = jobManager.addNewJob(executionTime);
                
                // Send a NEW_JOB_SUCCESS Message to the Controller
                messageManager.sendMessage(new MessageOutbound(MessageOutboundType.NEW_JOB_SUCCESS, String.valueOf(job.getIdNumber())), controllerIpAddress, controllerPortNumber);
                
                break;
                
            }
            case GET_INFO -> {
                
                // FORMAT: registered_nodes, queued_jobs, allocated_jobs, node_summaries[node_id_number, node_allocated_jobs, node_current_usage] ...
                
                // Collect a summary of all registered Nodes from the Node Manager
                String[] nodeSummaries = nodeManager.getNodeSummaries();
                
                // Create a string containing information about the Load-Balancer and status of all registered Nodes
                String informationString = String.format("%d,%d,%d", nodeSummaries.length, jobManager.getJobQueue().size(), jobManager.getAllocatedJobs().size());
                
                // If Nodes are connected, add their summaries to the information String
                if (nodeSummaries.length > 0) { informationString += String.format(",%s", String.join(",", nodeSummaries)); }
                
                // Send the String of information to the Controller with the INFO Message type
                messageManager.sendMessage(new MessageOutbound(MessageOutboundType.INFO, informationString), controllerIpAddress, controllerPortNumber);
                
                break;
                
            }
            case STOP_SYSTEM -> {
                
                // Stop the Message Manager's Message receiver Thread
                messageManager.stop();
                
                MessageOutbound stopNodeMessage = new MessageOutbound(MessageOutboundType.STOP_NODE);
                
                // Iterate through the list of registered Nodes
                for (Node node : nodeManager.getNodes()) {
                    // Stop the Keep Alive timer of the Node
                    node.stopKeepAlive();
                    
                    // Send a STOP_NODE Message to the Node
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
        } catch (NumberFormatException exception) { // Handle a NumberFormatException and return -1 (invalid Integer)
            return -1;
        }
    }
    
    private InetAddress parseIpAddressArgument(String value) {
        // Attempt to parse the provided "value" String to an InetAddress
        try {
            return InetAddress.getByName(value);
        } catch (UnknownHostException exception) { // Handle an UnknownHostException and return null (invalid IP Address)
            return null;
        }
    }
    
}
