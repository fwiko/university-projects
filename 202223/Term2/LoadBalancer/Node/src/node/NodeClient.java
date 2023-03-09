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
    int maximumCapacity = -1;
    
    InetAddress ipAddress = null;
    int portNumber = -1;
    
    InetAddress loadBalancerIpAddress = null;
    int loadBalancerPortNumber = -1;
    
    int nodeIdNumber = -1;
    
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
        messageManager = MessageManager.getInstance();
        jobManager = JobManager.getInstance();
        
        try {
            messageManager.start(ipAddress, portNumber);
        } catch (IOException exception) {
            System.err.printf("NodeClient - ERROR: IOException when opening Datagram Channel on %s:%d\n", ipAddress.getHostAddress(), portNumber);
            System.exit(1);
        }
        
        register();
        
        while (!messageManager.isStopped()) {
            for (Job job : jobManager.getAllFinishedJobs()) {
                messageManager.sendMessage(new MessageOutbound(MessageOutboundType.FIN_JOB, String.valueOf(job.getIdNumber())), loadBalancerIpAddress, loadBalancerPortNumber);
                System.out.printf("NodeClient - INFO: Job %d with %d second Execution Time has finished", job.getIdNumber(), job.getExecutionTime());
            }
            
            MessageInbound message = messageManager.getNextQueuedMessage();
            
            if (message == null) {
                continue;
            }
            
            try {
                handleMessage(message);
            } catch (IllegalArgumentException exception) {
                System.err.printf("NodeClient - ERROR: Could not handle %s Message (%s)", message.getType(), exception.getMessage());
            }
        }
        
        System.out.println("NodeClient - INFO: Stopped...");
    }
    
    private void register() {
        messageManager.sendMessage(new MessageOutbound(MessageOutboundType.REG_NODE, ipAddress.getHostAddress(), String.valueOf(portNumber), String.valueOf(maximumCapacity)), loadBalancerIpAddress, loadBalancerPortNumber);
    }
    
    private void handleMessage(MessageInbound message) throws IllegalArgumentException {
        switch (message.getType()) {
            case IS_ALIVE -> {
                messageManager.sendMessage(new MessageOutbound(MessageOutboundType.ACK_IS_ALIVE, String.valueOf(nodeIdNumber)), loadBalancerIpAddress, loadBalancerPortNumber);
                break;
            }
            case NEW_JOB -> {
                if (message.getParameters().length < 2) { throw new IllegalArgumentException("Insufficient number of Message arguments"); }
                
                int idNumber = parseIntegerArgument(message.getParameter(0));
                int executionTime = parseIntegerArgument(message.getParameter(1));
                
                if (idNumber * executionTime < 0) { throw new IllegalArgumentException("Illegal Message arguments provided"); }
                
                jobManager.startJob(idNumber, executionTime);
                
                messageManager.sendMessage(new MessageOutbound(MessageOutboundType.NEW_JOB_SUCCESS, String.valueOf(idNumber)), loadBalancerIpAddress, loadBalancerPortNumber);
                
                break;
            }
            case REG_FAILURE -> {
                messageManager.stop();
                break;
            }
            case REG_SUCCESS -> {
                if (message.getParameters().length < 1) { throw new IllegalArgumentException("Insufficient number of Message arguments"); }
                
                int idNumber = parseIntegerArgument(message.getParameter(0));
                
                if (idNumber < 1) {
                    throw new IllegalArgumentException("Illegal Message arguments provided");
                }
                
                nodeIdNumber = idNumber;
                
                break;
            }
            case STOP_NODE -> {
                messageManager.stop();
                jobManager.stopAllRunningJobs();
                break;
            }
        }
    }
    
    private int parseIntegerArgument(String value) {
        try {
            return Integer.parseInt(value);
        } catch (NumberFormatException exception) {
            return -1;
        }
    }
    
}
