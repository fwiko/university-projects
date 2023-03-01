/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
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
        
    public void start(InetAddress ipAddress, int portNumber) throws IllegalArgumentException {
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
        
        jobManager.queueNewJob(10);
        jobManager.queueNewJob(10);
        jobManager.queueNewJob(10);
        
        while (running) {
            // Retreive the next Message - from the Message Manager's Message queue
            MessageInbound nextMessage = messageManager.getNextMessage();
            
            // If the next Message was successfully retreived from the Node Manager
            if (nextMessage != null) {
                System.out.printf("Load-Balancer Server (Info): Handling %s Message\n", nextMessage.getType().toString());
                
                try {
                    handleMessage(nextMessage);
                } catch (IllegalArgumentException e) {
                    System.err.printf("Load-Balanacer Server (Error): Failed to handle %s Message (%s)", nextMessage.getType().toString(), e.getMessage());
                }
            }
            
            // If the system is no longer running (being shut down) - break out of the loop
            if (!running) { break; }
            
            // Retreive the next queued Job - from the Job Manager's Job queue - this does not remove the element so that if a Node isn't available the Job will remain (Atomic)
            Job nextJob = jobManager.getNextJob();
            
            // If the Job Manager's Job queue was empty (no pending Jobs) - reset to the top of the loop
            if (nextJob == null) {
                continue;
            }
            
            // Retreive the next Node - using the Load-Balancing algorithm 
            Node nextNode = null;
            nextNode = nodeManager.getNextNode();
            
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
        System.out.println("Load-Balancer Server (Info): Server operation has stopped...");
    }
    
    private void handleMessage(MessageInbound message) throws IllegalArgumentException {
        switch (message.getType()) {
            case REG_INITIATOR -> {
                if (message.getParameters().length < 2) { throw new IllegalArgumentException("Insufficient Message parameters"); }
                
                // Set the Initiator IP Address value to the first REG_INITIATOR Message parameter
                InetAddress tempInitiatorIpAddress = null;
                try {
                    tempInitiatorIpAddress = InetAddress.getByName(message.getParameter(0));
                } catch (UnknownHostException e) { throw new IllegalArgumentException(String.format("IP Address \"%s\" is not recognised", message.getParameter(0))); }
                
                // Set the Initiator Port Number value to the second REG_INITIATOR Message parameter;
                int tempInitiatorPortNumber = -1;
                try {
                    tempInitiatorPortNumber = Integer.parseInt(message.getParameter(1));
                    if (tempInitiatorPortNumber < 1 || tempInitiatorPortNumber >= 65535) {
                        throw new IllegalArgumentException(String.format("Port %d is outside of the assignable range", tempInitiatorPortNumber));
                    }
                } catch (NumberFormatException e) { throw new IllegalArgumentException(String.format("Provided Port is not an Integer")); }

                // Check if an Initiator has already been registered
                if (initiatorRegistered) {
                    MessageOutbound registerFailureMessage = new MessageOutbound(MessageOutboundType.REG_INITIATOR_FAILURE);
                    messageManager.sendMessage(registerFailureMessage, tempInitiatorIpAddress, tempInitiatorPortNumber);
                    break;
                }
                
                // Set the Initiator IP Address and Port values to the provided parameters
                this.initiatorIpAddress = tempInitiatorIpAddress;
                this.initiatorPortNumber = tempInitiatorPortNumber;
                
                // Send a REG_INITIATOR_SUCCESS Message to the Initiator
                MessageOutbound registerSuccessMessage = new MessageOutbound(MessageOutboundType.REG_INITIATOR_SUCCESS);
                messageManager.sendMessage(registerSuccessMessage, initiatorIpAddress, initiatorPortNumber);
                
                // Set the initiatorRegistered flag to TRUE
                initiatorRegistered = true;

                System.out.printf("Load-Balancer Server (Info): Initiator successfully registered on socket %s:%d", initiatorIpAddress, initiatorPortNumber);
                
                break;
            }
            case REG_NODE -> {
                if (message.getParameters().length < 3) { throw new IllegalArgumentException("Insufficient Message parameters"); }

                // Attempt to conver the IP Address parameter to an InetAddress object
                InetAddress nodeIpAddress = null;
                try {
                    nodeIpAddress = InetAddress.getByName(message.getParameter(0));
                } catch (UnknownHostException e) { throw new IllegalArgumentException("Provided IP Address is Unknown"); }
                
                // Attempt to convert the Port Number parameter of the REG_NODE Message to an Integer
                int nodePortNumber = -1;
                try {
                    nodePortNumber = Integer.parseInt(message.getParameter(1));
                    if (nodePortNumber < 1 || nodePortNumber >= 65535) {
                        throw new IllegalArgumentException(String.format("Port %d is outside of the assignable range", nodePortNumber));
                    }
                } catch (NumberFormatException e) { throw new IllegalArgumentException("Provided Port is not an Integer"); }
                
                // Attempt to convert the Capacity parameter of the REG_NODE Message to an Integer
                int nodeCapacity = -1;
                try {
                    nodeCapacity = Integer.parseInt(message.getParameter(2));
                } catch (NumberFormatException e) {
                    MessageOutbound registerFailureMessage = new MessageOutbound(MessageOutboundType.REG_NODE_FAILURE);
                    messageManager.sendMessage(registerFailureMessage, nodeIpAddress, nodePortNumber);
                    throw new IllegalArgumentException("Provided Capacity is not an Integer");
                }
                
                // If the provided Capacity is below 1 - throw an error and send an error response
                if (nodeCapacity < 1) {
                    MessageOutbound registerFailureMessage = new MessageOutbound(MessageOutboundType.REG_NODE_FAILURE);
                    messageManager.sendMessage(registerFailureMessage, nodeIpAddress, nodePortNumber);
                    throw new IllegalArgumentException("Provided Capacity is below 1");
                }
                
                // Register the new Node with the Node Manager
                Node node = nodeManager.registerNode(nodeIpAddress, nodePortNumber, nodeCapacity);
                
                // Send a REG_NODE_SUCCESS Message to the Node
                MessageOutbound registerSuccessMessage = new MessageOutbound(MessageOutboundType.REG_NODE_SUCCESS, String.valueOf(node.getIdNum()));
                messageManager.sendMessage(registerSuccessMessage, nodeIpAddress, nodePortNumber);
                
                break;
            }
            case NEW_JOB -> {
                if (message.getParameters().length < 1) { throw new IllegalArgumentException("Insufficient Message parameters"); }
                
                // Attempt to convert the Execution Time parameter of the NEW_JOB Message to an Integer
                int executionTime = -1;
                try {
                    executionTime = Integer.parseInt(message.getParameter(0));
                } catch (NumberFormatException e) {
                    throw new IllegalArgumentException("Provided Execution Time is not an Integer");
                }
                
                // Add the new Job to the Job Manager's queue
                Job job = jobManager.queueNewJob(executionTime);
                
                // Send a NEW_JOB_SUCCESS Message to the Initiator
                MessageOutbound newJobSuccessMessage = new MessageOutbound(MessageOutboundType.NEW_JOB_SUCCESS, String.valueOf(job.getIdNumber()));
                messageManager.sendMessage(newJobSuccessMessage, initiatorIpAddress, initiatorPortNumber);
                
                break;
            }
            case FIN_JOB -> {
                if (message.getParameters().length < 1) { throw new IllegalArgumentException("Insufficient Message parameters"); }

                // Attempt to convert the Job ID parameter of the FIN_JOB Message to an integer
                int jobId = -1;
                try {
                    jobId = Integer.parseInt(message.getParameter(0));
                } catch (NumberFormatException e) {
                    throw new IllegalArgumentException("Provided Job ID is not an Integer");
                }
                
                // Get the Job object associated with the given Job ID from the Job Manager
                Job job = jobManager.getAllocatedJobById(jobId);
                if (job == null) {
                    throw new IllegalArgumentException(String.format("Allocated Job with ID %d does not exist", jobId));
                }
                
                // De-allocate the Job from the assigned Node with the Job Manager
                jobManager.deallocateJob(job);
                
                // Forward the FIN_JOB Message to the Initiator
                MessageOutbound finishedJobMessage = new MessageOutbound(MessageOutboundType.FIN_JOB, message.getParameter(0));
                messageManager.sendMessage(finishedJobMessage, initiatorIpAddress, initiatorPortNumber);
                
                break;
            }
            case ACK_IS_ALIVE -> {
                if (message.getParameters().length < 1) { throw new IllegalArgumentException("Insufficient Message parameters"); }
//                
//                // Attempt to convert the Node ID parameter of the ACK_IS_ALIVE Message to an Integer
//                int nodeId = -1;
//                try {
//                    nodeId = Integer.parseInt(message.getParameter(0));
//                } catch (NumberFormatException e) {
//                    System.err.println("Server (Error): Failed to handle alive acknowledgement (Invalid Node ID)");
//                    break;
//                }
//                
//                // Get the Node object associated with the given Node ID from the Node Manager
//                Node node = nodeManager.getNodeById(nodeId);
//                if (node == null) {
//                    System.err.println(String.format("Server (Error): Failed to handle alive acknowledgement (Node with ID %d no longer exists)", nodeId));
//                    break;
//                }
//                
//                // Reset the warnings (three warning system) of the Node that sent the ACK_IS_ALIVE Message
//                nodeManager.resetWarnings(node);
            }
            case EXITED_NODE -> {
                if (message.getParameters().length < 1) { throw new IllegalArgumentException("Insufficient Message parameters"); }
                
//                // Attempt to convert the Node ID parameter of the EXITED_NODE Message to an Integer
//                int nodeId = 0;
//                try {
//                    nodeId = Integer.parseInt(message.getParameter(0));
//                } catch (NumberFormatException e) {
//                    System.err.println(String.format("Server (Error): Failed to remove Node - %s is not a valid integer", message.getParameter(0)));
//                    break;
//                }
//                
//                // Get the Node object associated with the given Node ID from the Node Manager
//                Node stoppedNode = nodeManager.getNodeById(nodeId);
//                if (stoppedNode == null) {
//                    System.err.println(String.format("Server (Error): Failed to remove Node - Could not find Node with ID %d", nodeId));
//                    return;
//                }
//                
//                // Re-allocate any Jobs the Node was handling
//                
//                // Remove/unregister the Node from the Node Manager
//                nodeManager.removeNode(nodeId);
            }
            case STOP_SYSTEM -> {
                messageManager.stop();
                running = false;
                break;
            }
            default -> {
                //
            }
        }
    }
    
}
