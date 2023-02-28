/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package loadbalancer;

import java.net.DatagramSocket;
import java.net.InetAddress;
import java.net.SocketException;
import java.net.UnknownHostException;
import loadbalancer.job.Job;
import loadbalancer.managers.JobManager;
import loadbalancer.managers.MessageManager;
import loadbalancer.managers.NodeManager;
import loadbalancer.message.MessageInbound;
import loadbalancer.message.MessageOutbound;
import loadbalancer.message.types.MessageTypeOutbound;
import loadbalancer.node.Node;

public class Server {
    // Server Details
    private int portNumber = 0;
    private InetAddress ipAddress = null;
    private DatagramSocket socket = null;
    private boolean running = true;
    
    // Manager singleton class instances
    private MessageManager messageManager;
    private JobManager jobManager;
    private NodeManager nodeManager;
    
    // Initiator Details
    private InetAddress initiatorIpAddress;
    private int initiatorPortNumber = 0;
    private boolean initiatorRegistered = false;
    
    
    public Server(String ipAddress, int portNumber) {
        setIpAddress(ipAddress);
        setPortNumber(portNumber);
    }
        
    public void start() {
        try {
            socket = new DatagramSocket(portNumber, ipAddress);
            socket.setSoTimeout(0);
        } catch (SocketException e) {
            System.err.println("Error: Failed to create new Socket.");
            System.exit(0);
        }
        
        // Get instances of singleton manager classes
        messageManager = MessageManager.getInstance();
        jobManager = JobManager.getInstance();
        nodeManager = NodeManager.getInstance();
        
        // Start listening for incoming Messages
        messageManager.listen(socket);
        
        while (running) {
            // Retreive and Handle the next Message - using FIFO approach to get next Message
            MessageInbound nextMessage = messageManager.getNextMessage();
            if (nextMessage != null) {
                System.out.println(String.format("Server (Info): Received %s Message", nextMessage.getType().toString()));
                handleMessage(nextMessage);
                
            }
            
            if (!running) { break; }
            
            // Retreive the next Job - using FIFO approach to get next Job from the Job queue
            Job nextJob = jobManager.getNextJob();
            if (nextJob == null) {
                continue;
            }
            
            // Retreive the next Node - using the WRR Load-Balancing algorithm 
            Node nextNode = null;
            nextNode = nodeManager.getNextNode();
            if (nextNode != null) {
                // Allocate the new Job  to the next Node on the Job Manager
                jobManager.allocateJob(nextJob, nextNode);
                
                // Send the Job allocation Message to the Node
                MessageOutbound newJobMessage = new MessageOutbound(MessageTypeOutbound.NEW_JOB, ",", String.valueOf(nextJob.getIdNumber()), String.valueOf(nextJob.getExecutionTime()));
                messageManager.sendMessage(newJobMessage, nextNode.getIpAddr(), nextNode.getPortNum());
            }
        }
    }
    
    private void handleMessage(MessageInbound message) {
        switch (message.getType()) {
            case REG_INITIATOR -> {
                if (message.getParameters().length < 2) {
                    System.err.println("Server (Error): Failed to register Initiator - Not enough parameters");
                    break;
                }
                
                // Attempt to set the Initiator IP Address from the first Message parameter
                InetAddress tempInitiatorIpAddress = null;
                try {
                    tempInitiatorIpAddress = InetAddress.getByName(message.getParameter(0));
                } catch (UnknownHostException e) {
                    System.err.println(String.format("Server (Error): Failed to register Initiator - IP Address \"%s\" is not recognised", message.getParameter(0)));
                    break;
                }
                
                // Attempt to set the Initiator Port Number from the second Message parameter
                int tempInitiatorPortNumber = 0;
                try {
                    tempInitiatorPortNumber = Integer.parseInt(message.getParameter(1));
                    if (tempInitiatorPortNumber < 1 || tempInitiatorPortNumber >= 65535) {
                        throw new NumberFormatException();
                    }
                } catch (NumberFormatException e) {
                    System.err.println(String.format("Server (Error): Failed to register Initiator - Port \"%s\" is invalid", message.getParameter(0)));
                    break;
                }

                // If an initiator has already been registered - send failure message and stop
                if (initiatorRegistered) {
                    MessageOutbound registerFailureMessage = new MessageOutbound(MessageTypeOutbound.REG_INITIATOR_FAILURE, ",");
                    messageManager.sendMessage(registerFailureMessage, tempInitiatorIpAddress, tempInitiatorPortNumber);
                    System.err.println("Server (Error): There is already a registered Initiator");
                    break;
                } 
                
                // Set initiator IP and Port values to registered parameters
                initiatorIpAddress = tempInitiatorIpAddress;
                initiatorPortNumber = tempInitiatorPortNumber;

                // Send a success message to the initiator
                MessageOutbound registerSuccessMessage = new MessageOutbound(MessageTypeOutbound.REG_INITIATOR_SUCCESS, ",");
                messageManager.sendMessage(registerSuccessMessage, initiatorIpAddress, initiatorPortNumber);

                // Set the initiator as registered
                initiatorRegistered = true;
                
                System.out.println("Server (Info): Initiator has sucessfully registered");
            }
            case REG_NODE -> {
                if (message.getParameters().length < 3) {
                    System.err.println("Server (Error): Failed to register Node (Not enough parameters)");
                    break;
                }
                
                // Attempt to convert the Port Number parameter of the REG_NODE Message to an Integer
                int port = 0;
                try {
                    portNumber = Short.parseShort(message.getParameter(1));
                } catch (NumberFormatException e) {
                    System.err.println(String.format("Server (Error): Failed to register Node (%s is not a valid Port Number)", message.getParameter(1)));
                }
                
                // Attempt to convert the Capacity parameter of the REG_NODE Message to an Integer
                int capacity = 0;
                try {
                    capacity = Integer.parseInt(message.getParameter(2));
                } catch (NumberFormatException e) {
                    System.err.println(String.format("Server (Error): Failed to register Node (Capacity \"%s\" is not a valid Integer)", message.getParameter(1)));
                }
                
                // Register the new Node with the Node Manager
                nodeManager.registerNode(message.getParameter(0), port, capacity);
            }
            case NEW_JOB -> {
                if (message.getParameters().length < 1) {
                    System.err.println("Server (Error): Failed to queue Job (Not enough parameters)");
                    break;
                }
                
                // Attempt to convert the Execution Time parameter of the NEW_JOB Message to an Integer
                int executionTime = 0;
                try {
                    executionTime = Integer.parseInt(message.getParameter(0));
                } catch (NumberFormatException e) {
                    System.err.println(String.format("Server (Error): Failed to queue Job (Execution time \"%s\" is not a valid Integer)", message.getParameter(0)));
                    break;
                }
                
                // Add the new Job to the Job Manager's queue
                jobManager.queueJob(executionTime);
            }
            case FIN_JOB -> {
                if (message.getParameters().length < 1) {
                    System.err.println("Server (Error): Failed to handle finished Job (Not enough parameters)");
                    break;
                }
                
                // Attempt to convert the Job ID parameter of the FIN_JOB Message to an Integer
                int jobId = 0;
                try {
                    jobId = Integer.parseInt(message.getParameter(0));
                } catch (NumberFormatException e) {
                    System.err.println("Server (Error): Failed to handle finished Job (Invalid Job ID)");
                    break;
                }
                
                // Get the Job object associated with the given Job ID from the Job Manager
                Job job = jobManager.getAllocatedJobById(jobId);
                if (job == null) {
                    System.err.println(String.format("Server (Error): Failed to handle finished Job (Allocated Job with ID %d does not exist)", jobId));
                    break;
                }
                
                // De-allocate the Job - removing it from the Job Manager
                jobManager.deallocateJob(job);
                
                // Send a FIN_JOB Message to the Initiator
                MessageOutbound jobFinishedMessage = new MessageOutbound(MessageTypeOutbound.FIN_JOB, ",", String.valueOf(jobId));
                messageManager.sendMessage(jobFinishedMessage, initiatorIpAddress, initiatorPortNumber);
            }
            case ACK_IS_ALIVE -> {
                if (message.getParameters().length < 1) {
                    System.err.println("Server (Error): Failed to handle alive acknowledgement (Not enough parameters)");
                    break;
                }
                
                // Attempt to convert the Node ID parameter of the ACK_IS_ALIVE Message to an Integer
                int nodeId = -1;
                try {
                    nodeId = Integer.parseInt(message.getParameter(0));
                } catch (NumberFormatException e) {
                    System.err.println("Server (Error): Failed to handle alive acknowledgement (Invalid Node ID)");
                    break;
                }
                
                // Get the Node object associated with the given Node ID from the Node Manager
                Node node = nodeManager.getNodeById(nodeId);
                if (node == null) {
                    System.err.println(String.format("Server (Error): Failed to handle alive acknowledgement (Node with ID %d no longer exists)", nodeId));
                    break;
                }
                
                // Reset the warnings (three warning system) of the Node that sent the ACK_IS_ALIVE Message
                nodeManager.resetWarnings(node);
            }
            case EXITED_NODE -> {
                if (message.getParameters().length < 1) {
                    System.err.println("Server (Error): Failed to remove Node - Not enough parameters");
                    break;
                }
                
                // Attempt to convert the Node ID parameter of the EXITED_NODE Message to an Integer
                int nodeId = 0;
                try {
                    nodeId = Integer.parseInt(message.getParameter(0));
                } catch (NumberFormatException e) {
                    System.err.println(String.format("Server (Error): Failed to remove Node - %s is not a valid integer", message.getParameter(0)));
                    break;
                }
                
                // Get the Node object associated with the given Node ID from the Node Manager
                Node stoppedNode = nodeManager.getNodeById(nodeId);
                if (stoppedNode == null) {
                    System.err.println(String.format("Server (Error): Failed to remove Node - Could not find Node with ID %d", nodeId));
                    return;
                }
                
                // Re-allocate any Jobs the Node was handling
                
                // Remove/unregister the Node from the Node Manager
                nodeManager.removeNode(nodeId);
            }
            case STOP_SYSTEM -> {
                System.out.println("stopping");
                messageManager.stop();
                running = false;
                break;
            }
            default -> throw new AssertionError();
        }
    }
    
    private void setIpAddress(String ipAddress) throws IllegalArgumentException {
        try {
            this.ipAddress = InetAddress.getByName(ipAddress);
        } catch (UnknownHostException e) {
            throw new IllegalArgumentException(String.format(
                    "Error: IP Address \"%s\" is not recognised.",
                    ipAddress
            ));
        }
    }
    
    private void setPortNumber(int portNumber) throws IllegalArgumentException {
        if (portNumber < 1 || portNumber >= 65535) {
            throw new IllegalArgumentException(String.format(
                    "Error: Port \"%s\" is outside of the valid range.", 
                    portNumber
            ));
        } else {
            this.portNumber = portNumber;
        }
    }
}
