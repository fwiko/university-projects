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
    
    // Manager Instances
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
                handleMessage(nextMessage);
            }
            
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
                    MessageOutbound registerFailureMessage = new MessageOutbound(MessageTypeOutbound.UNKNOWN, ",");
                    messageManager.sendMessage(registerFailureMessage, tempInitiatorIpAddress, tempInitiatorPortNumber);
                    break;
                } 
                
                // Set initiator IP and Port values to registered parameters
                initiatorIpAddress = tempInitiatorIpAddress;
                initiatorPortNumber = tempInitiatorPortNumber;

                
                // Send a success message to the initiator
                MessageOutbound registerSuccessMessage = new MessageOutbound(MessageTypeOutbound.UNKNOWN, ",");
                messageManager.sendMessage(registerSuccessMessage, initiatorIpAddress, initiatorPortNumber);

                // Set the initiator as registered
                initiatorRegistered = true;
            }
            case REG_NODE -> {
                if (message.getParameters().length < 3) {
                    System.err.println("Server (Error): Failed to register Node - Not enough parameters");
                    break;
                }
                
                int port = 0;
                try {
                    portNumber = Short.parseShort(message.getParameter(1));
                } catch (NumberFormatException e) {
                    System.err.println(String.format("Server (Error): Failed to register Node - %s is not a valid port number", message.getParameter(1)));
                }
                
                int capacity = 0;
                try {
                    capacity = Integer.parseInt(message.getParameter(2));
                } catch (NumberFormatException e) {
                    System.err.println(String.format("Server (Error): Failed to register Node - %s is not a valid integer", message.getParameter(1)));
                }
                
                nodeManager.registerNode(message.getParameter(0), port, capacity);
            }
            case NEW_JOB -> {
                if (message.getParameters().length < 1) {
                    System.err.println("Server (Error): Failed to queue Job - Not enough parameters");
                    break;
                }
                
                int executionTime = 0;
                try {
                    executionTime = Integer.parseInt(message.getParameter(0));
                } catch (NumberFormatException e) {
                    System.err.println(String.format("Server (Error): Failed to queue Job - %s is not a valid integer", message.getParameter(0)));
                    break;
                }
                
                jobManager.queueJob(executionTime);
            }
            case FIN_JOB -> {
                if (message.getParameters().length < 1) {
                    System.err.println("Server (Error): Failed to handle finished Job - Not enough parameters");
                    break;
                }
                
                int jobId = 0;
                try {
                    jobId = Integer.parseInt(message.getParameter(0));
                } catch (NumberFormatException e) {
                    System.err.println("Server (Error): Failed to handle finished Job - Invalid Job ID");
                    break;
                }
                
                jobManager.deallocateJobById(jobId);
                
                // Send a Job finished message to the initiator
                MessageOutbound jobFinishedMessage = new MessageOutbound(MessageTypeOutbound.UNKNOWN, ",", String.valueOf(jobId));
                messageManager.sendMessage(jobFinishedMessage, initiatorIpAddress, initiatorPortNumber);
            }
            case ACK_IS_ALIVE -> {
                // Node Manager Add Strike
                // Node Manager Get Strikes
                // If Strikes hit threshold remove node
            }
            case STOPPED_NODE -> {
                if (message.getParameters().length < 1) {
                    System.err.println("Server (Error): Failed to remove Node - Not enough parameters");
                    break;
                }
                
                // Try to parse the nodeId parameter of the message
                int nodeId = 0;
                try {
                    nodeId = Integer.parseInt(message.getParameter(0));
                } catch (NumberFormatException e) {
                    System.err.println(String.format("Server (Error): Failed to remove Node - %s is not a valid integer", message.getParameter(0)));
                    break;
                }
                
                // Retreive the Node object associated with the specified Node ID
                Node stoppedNode = nodeManager.getNodeById(nodeId);
                if (stoppedNode == null) {
                    System.err.println(String.format("Server (Error): Failed to remove Node - Could not find Node with ID %d", nodeId));
                    return;
                }
                
                // If the Load-Balancer system is still running - re-allocate any Jobs the Node was handling
                if (running) {
                    // RE-ALLOCATE JOBS
                }
                
                // Remove/unregister the Node
                nodeManager.removeNode(nodeId);
            }
            case STOP_SYSTEM -> {
                running = false;
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
