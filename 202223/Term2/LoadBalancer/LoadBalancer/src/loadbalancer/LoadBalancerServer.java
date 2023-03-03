/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package loadbalancer;

import java.io.IOException;
import java.net.InetAddress;
import java.net.UnknownHostException;
import java.util.ArrayList;
import loadbalancer.job.Job;
import loadbalancer.managers.JobManager;
import loadbalancer.managers.MessageManager;
import loadbalancer.managers.NodeManager;
import loadbalancer.messages.MessageInbound;
import loadbalancer.messages.MessageOutbound;
import static loadbalancer.messages.types.MessageInboundType.NEW_JOB_FAILURE;
import loadbalancer.messages.types.MessageOutboundType;
import loadbalancer.node.Node;

public class LoadBalancerServer {
    private static LoadBalancerServer instance = null;
    
    // Server switch used to stop operation loop when a STOP_SYSTEM Message is received
    private boolean running = true;
    
    // Singleton Message, Job, and Node Manager classes
    private MessageManager messageManager;
    private JobManager jobManager;
    private NodeManager nodeManager;
    
    // Details relating to the Initiator client including IP Address, Port Number, and Registration Status
    private InetAddress initiatorIpAddress;
    private int initiatorPortNumber = -1;
    private boolean initiatorRegistered = false;

    public static LoadBalancerServer getInstance() {
        // If the singleton instance already exists - return it
        if (instance != null) {
            return instance;
        }
        
        // Create a new instance and return it
        instance = new LoadBalancerServer();
        return instance;
    }
        
    public void start(InetAddress ipAddress, int portNumber, AllocationMethod allocationMethod) throws IllegalArgumentException {
        // If the specified Port Number is outside the valid Port range - throw an IllegalArgumentException
        if (portNumber < 1 || portNumber >= 65535) {
            throw new IllegalArgumentException(String.format(
                    "%d is outside of the assignable Port range",
                    portNumber
            ));
        }

        // Get the instances of the singleton Message, Job, and Node Manager classes
        messageManager = MessageManager.getInstance();
        jobManager = JobManager.getInstance();
        nodeManager = NodeManager.getInstance();

        // Attempt to start the Message Manager's Message listener
        try {
            messageManager.start(ipAddress, portNumber);
        } catch (IOException e) {
            System.out.println(e);
        }
        
        while (running) {
            // Retreive the next Message - from the Message Manager's Message queue
            MessageInbound nextMessage = messageManager.getNextMessage();
            
            // If the next Message was successfully retreived from the Node Manager
            if (nextMessage != null) {
                try {
                    handleMessage(nextMessage);
                } catch (IllegalArgumentException e) {
                    System.err.printf(" LoadBalancerServer - ERROR: Failed to handle %s Message (%s)\n", nextMessage.getType().toString(), e.getMessage());
                }
            }
            
            // If the system is no longer running (being shut down) - break out of the loop
            if (!running) { break; }
            
            // Retreive the next queued Job - from the Job Manager's Job queue - this does not remove the element so that if a Node isn't available the Job will remain (Atomic)
            Job nextJob = jobManager.getNextJob();
            
            // If the Job Manager's Job queue was empty (no pending Jobs) - reset to the top of the loop
            if (nextJob == null) { continue; }
            
            // Retreive the next Node - using the Load-Balancing algorithm 
            Node nextNode = null;
            nextNode = nodeManager.getNextNode(allocationMethod);
            
            // If a Node was successfully retreived from the Node Manager
            if (nextNode != null) {
                
                // Register the Node as the new Job's "handler" with the Job Manager
                jobManager.allocateJob(nextJob, nextNode);
                
                // Attempt to create and send a NEW_JOB Message to the next free Node - allocating the Job to the remote Node
                MessageOutbound newJobMessage = new MessageOutbound(MessageOutboundType.NEW_JOB, String.valueOf(nextJob.getIdNumber()), String.valueOf(nextJob.getExecutionTime()));
                messageManager.sendMessage(newJobMessage, nextNode.getIpAddr(), nextNode.getPortNum());
            }
        }
        
        // When the system is no longer running - output a message to the terminal
        System.out.println(" LoadBalancerServer - INFO: Stopped");
    }
    
    private void handleMessage(MessageInbound message) throws IllegalArgumentException {
        switch (message.getType()) {
            case REG_INITIATOR -> { // ------------------------------------------------------------------------------------------------------------------------------------------------------------- REG_INITIATOR
                if (message.getParameters().length < 2) { throw new IllegalArgumentException("Insufficient Message parameters"); }
                
                // Set the Initiator IP Address value to the first REG_INITIATOR Message parameter
                InetAddress ipAddress = null;
                try {
                    ipAddress = InetAddress.getByName(message.getParameter(0));
                } catch (UnknownHostException e) {
                    throw new IllegalArgumentException(String.format("IP Address \"%s\" is not recognised", message.getParameter(0)));
                }
                
                // Set the Initiator Port Number value to the second REG_INITIATOR Message parameter;
                int portNumber = -1;
                try {
                    portNumber = Integer.parseInt(message.getParameter(1));
                    
                    // If the given Port Number is outside of the acceptable range
                    if (portNumber < 1 || portNumber >= 65535) {
                        throw new IllegalArgumentException(String.format("Port %d is outside of the assignable range", portNumber));
                    }
                } catch (NumberFormatException e) { 
                    throw new IllegalArgumentException(String.format("Provided Port is not an Integer"));
                }

                // If an Initiator is already registered
                if (initiatorRegistered) {
                    
                    // Respond with a REG_INITIATOR_FAILURE Message
                    MessageOutbound registerFailureMessage = new MessageOutbound(MessageOutboundType.REG_INITIATOR_FAILURE);
                    messageManager.sendMessage(registerFailureMessage, ipAddress, portNumber);
                    
                    break;
                }
                
                // Set the Initiator IP Address and Port values to the provided parameters
                this.initiatorIpAddress = ipAddress;
                this.initiatorPortNumber = portNumber;
                
                // Send a REG_INITIATOR_SUCCESS Message to the Initiator
                MessageOutbound registerSuccessMessage = new MessageOutbound(MessageOutboundType.REG_INITIATOR_SUCCESS);
                messageManager.sendMessage(registerSuccessMessage, initiatorIpAddress, initiatorPortNumber);
                
                // Set the initiatorRegistered flag to TRUE
                initiatorRegistered = true;

                System.out.printf(" LoadBalancerServer - INFO: Initiator successfully registered on socket %s:%d\n", initiatorIpAddress.getHostAddress(), initiatorPortNumber);
                
                break;
            }
            case REG_NODE -> { // ------------------------------------------------------------------------------------------------------------------------------------------------------------------ REG_NODE
                if (message.getParameters().length < 3) { throw new IllegalArgumentException("Insufficient Message parameters"); }

                // Set the Node IP Address value to the first REG_NODE Message parameter
                InetAddress nodeIpAddress = null;
                try {
                    nodeIpAddress = InetAddress.getByName(message.getParameter(0));
                } catch (UnknownHostException e) { throw new IllegalArgumentException("Provided IP Address is Unknown"); }
                
                // Set the Node Port Number value to the second REG_NODE Message parameter
                int nodePortNumber = -1;
                try {
                    nodePortNumber = Integer.parseInt(message.getParameter(1));
                    
                    // If the given Port Number is outside the acceptable port range
                    if (nodePortNumber < 1 || nodePortNumber >= 65535) {
                        throw new IllegalArgumentException(String.format("Port %d is outside of the assignable range", nodePortNumber));
                    }
                } catch (NumberFormatException e) { throw new IllegalArgumentException("Provided Port is not an Integer"); }
                
                // Set the Node Capacity value to the third REG_NODE Message parameter
                int nodeCapacity = -1;
                try {
                    nodeCapacity = Integer.parseInt(message.getParameter(2));
                    
                    // If the given Capacity is below 1
                    if (nodeCapacity < 1) {
                        
                        // Send a REG_NODE_FAILURE Message to the Node
                        MessageOutbound registerFailureMessage = new MessageOutbound(MessageOutboundType.REG_NODE_FAILURE);
                        messageManager.sendMessage(registerFailureMessage, nodeIpAddress, nodePortNumber);
                        throw new IllegalArgumentException("Provided Capacity is below 1");
                    }
                } catch (NumberFormatException e) {
                    
                    // Send a REG_NODE_FAILURE Message to the Node
                    MessageOutbound registerFailureMessage = new MessageOutbound(MessageOutboundType.REG_NODE_FAILURE);
                    messageManager.sendMessage(registerFailureMessage, nodeIpAddress, nodePortNumber);
                    throw new IllegalArgumentException("Provided Capacity is not an Integer");
                }
                
                // Register the new Node with the NodeManager
                Node node = nodeManager.registerNode(nodeIpAddress, nodePortNumber, nodeCapacity);
                
                // Send a REG_NODE_SUCCESS Message to the Node
                MessageOutbound registerSuccessMessage = new MessageOutbound(MessageOutboundType.REG_NODE_SUCCESS, String.valueOf(node.getIdNumber()));
                messageManager.sendMessage(registerSuccessMessage, nodeIpAddress, nodePortNumber);
                
                break;
            }
            case NEW_JOB -> { // ------------------------------------------------------------------------------------------------------------------------------------------------------------------- NEW_JOB
                if (message.getParameters().length < 1) { throw new IllegalArgumentException("Insufficient Message parameters"); }
                
                // Set the Job Execution Time value to the first NEW_JOB Message parameter
                int executionTime = -1;
                try {
                    executionTime = Integer.parseInt(message.getParameter(0));
                } catch (NumberFormatException e) {
                    throw new IllegalArgumentException("Provided Execution Time is not an Integer");
                }
                
                // Queue the new Job with the JobManager
                Job job = jobManager.createNewJob(executionTime);
                
                // Send a NEW_JOB_SUCCESS Message to the Initiator
                MessageOutbound newJobSuccessMessage = new MessageOutbound(MessageOutboundType.NEW_JOB_SUCCESS, String.valueOf(job.getIdNumber()));
                messageManager.sendMessage(newJobSuccessMessage, initiatorIpAddress, initiatorPortNumber);
                
                break;
            }
            case FIN_JOB -> { // ------------------------------------------------------------------------------------------------------------------------------------------------------------------- FIN_JOB
                if (message.getParameters().length < 1) { throw new IllegalArgumentException("Insufficient Message parameters"); }

                // Set the Job ID Number value to the first FIN_JOB Message parameter
                int jobId = -1;
                try {
                    jobId = Integer.parseInt(message.getParameter(0));
                } catch (NumberFormatException e) {
                    throw new IllegalArgumentException("Provided Job ID is not an Integer");
                }
                
                // Get the Job object associated with the given Job ID Number from the JobManager
                Job job = jobManager.getAllocatedJobById(jobId);
                if (job == null) {
                    throw new IllegalArgumentException(String.format("Allocated Job with ID %d does not exist", jobId));
                }
                
                // Deallocate the given Job from the JobManager (it is now finished)
                jobManager.deallocateJob(job);
                
                // Forward the FIN_JOB Message to the Initiator
                MessageOutbound finishedJobMessage = new MessageOutbound(MessageOutboundType.FIN_JOB, message.getParameter(0));
                messageManager.sendMessage(finishedJobMessage, initiatorIpAddress, initiatorPortNumber);
                
                break;
            }
            case ACK_IS_ALIVE -> { // ------------------------------------------------------------------------------------------------------------------------------------------------------------- ACK_IS_ALIVE
                if (message.getParameters().length < 1) { throw new IllegalArgumentException("Insufficient Message parameters"); }

                // Set the Node ID Number value to the first ACK_IS_ALIVE Message parameter
                int nodeId = -1;
                try {
                    nodeId = Integer.parseInt(message.getParameter(0));
                } catch (NumberFormatException e) {
                    throw new IllegalArgumentException("Node ID must be an Integer");
                }
                
                // Get the Node object associated with the given Node ID from the NodeManager
                Node node = nodeManager.getNodeById(nodeId);
                if (node == null) {
                    System.err.printf(" LoadBalancerServer - ERROR: Failed to handle ACK_IS_ALIVE Message (Node with ID %d is no longer registered)\n", nodeId);
                    break;
                }
                
                // Reset the warnings (three warning system) of the Node that sent the ACK_IS_ALIVE Message
                node.resetWarnings();
                
                break;
            }
            case STOP_SYSTEM -> { // --------------------------------------------------------------------------------------------------------------------------------------------------------------- STOP_SYSTEM
                // Interrupt (stop) the MessageManager Thread
                messageManager.stop();
                
                // Set the LoadBalancerServer running flag to false to stop the Message/Job handling loop
                running = false;
                
                // Get all registered Nodes
                ArrayList<Node> registeredNodes = nodeManager.getNodes();
                
                // Send STOP_NODE Messages to all registered Nodes
                MessageOutbound stopNodeMessage = new MessageOutbound(MessageOutboundType.STOP_NODE);
                for ( Node node : registeredNodes ) {
                    messageManager.sendMessage(stopNodeMessage, node.getIpAddr(), node.getPortNum());
                    
                    // Stop the Node's keep alive timer Thread
                    node.stopKeepAliveThread();
                }
                
                break;
            }
            case NEW_JOB_SUCCESS -> {
                if (message.getParameters().length < 1) { throw new IllegalArgumentException("Insufficient Message parameters"); }
                
                // Forward the NEW_JOB_SUCCESS Message to the Initiator
                MessageOutbound newJobSuccessMessage = new MessageOutbound(MessageOutboundType.NEW_JOB_SUCCESS, message.getParameter(0));
                messageManager.sendMessage(newJobSuccessMessage, initiatorIpAddress, initiatorPortNumber);
                
                System.out.printf(" LoadBalancerServer - INFO: Allocation of Job %s was Successful\n", message.getParameter(0));
                
                break;
            }
            case NEW_JOB_FAILURE -> {
                if (message.getParameters().length < 1) { throw new IllegalArgumentException("Insufficient Message parameters"); }
                
                // Set the failed Job ID value to the first NEW_JOB_FAILURE Parameter
                int failedJobId = -1;
                try {
                    failedJobId = Integer.parseInt(message.getParameter(0));
                } catch (NumberFormatException e) {
                    throw new IllegalArgumentException("Provided Job ID is not an Integer");
                }
                
                // Deallocate the Job from the JobManager
                jobManager.deallocateJob(jobManager.getAllocatedJobById(failedJobId));
                
                // Forward the NEW_JOB_FAILURE Message to the Initiator
                MessageOutbound newJobSuccessMessage = new MessageOutbound(MessageOutboundType.NEW_JOB_FAILURE, message.getParameter(0));
                messageManager.sendMessage(newJobSuccessMessage, initiatorIpAddress, initiatorPortNumber);
                
                System.err.printf(" LoadBalancerServer - ERROR: Failed to allocate Job %s ()\n", message.getParameter(0));
                
                break;
            }
            default -> throw new IllegalArgumentException(String.format("Unknown instruction"));
        }
    }
}
