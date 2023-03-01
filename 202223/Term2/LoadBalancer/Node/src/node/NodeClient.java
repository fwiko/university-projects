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
    //
    private static NodeClient instance = null;
    
    //
    private boolean running = true;
    
    // Node Client details
    private int nodeIdNumber = -1;
    private int nodePortNumber = -1;
    private int nodeCapacity = -1;
    private InetAddress nodeIpAddress = null;
    
    // Load-Balancer Server details
    private InetAddress loadBalancerIpAddress = null;
    private int loadBalancerPortNumber = -1;
    
    // 
    MessageManager messageManager = null;
    JobManager jobManager = null;
    
    
    public static NodeClient getInstance() {
        if (instance != null) {
            return instance;
        }
        instance = new NodeClient();
        return instance;
    }
    
    public void start(int capacity, InetAddress nodeIpAddress, int nodePortNumber, InetAddress loadBalancerIpAddress, int loadBalancerPortNumber) throws IllegalArgumentException {
        //
        this.nodeIpAddress = nodeIpAddress;
        this.nodePortNumber = nodePortNumber;
        this.nodeCapacity = capacity;
        
        //
        this.loadBalancerIpAddress = loadBalancerIpAddress;
        this.loadBalancerPortNumber = loadBalancerPortNumber;
        
        //
        messageManager = MessageManager.getInstance();
        jobManager = JobManager.getInstance();
        
        //
        try {
            messageManager.start(nodeIpAddress, nodePortNumber);
        } catch (IOException e) {
            System.out.println(e);
        }
        
        //
        register();
        
        //
        while (running) {
            //
            if (messageManager.isStopped()) {
                running = false;
            }
            
            //
            MessageInbound nextMessage = messageManager.getNextMessage();
            
            //
            if (nextMessage != null) {
                System.out.printf("NodeClient - INFO: Handling %s Message\n", nextMessage.getType().toString());
                
                //
                try {
                    handleMessage(nextMessage);
                } catch (IllegalArgumentException e) {
                    System.out.printf("NodeClient - ERROR: Failed to handle %s Message (%s)\n", nextMessage.getType().toString(), e.getMessage());
                }
            }
            
            //
            List<Job> finishedJobs = jobManager.getFinishedJobs();
            if (!finishedJobs.isEmpty()) {
                
                //
                for(Job job : finishedJobs) {
                    System.out.printf("NodeClient - INFO: Job %d with Execution Time %d has finished\n", job.getIdNumber(), job.getExecutionTime());
                    
                    //
                    MessageOutbound finishedJobMessage = new MessageOutbound(MessageOutboundType.FIN_JOB, String.valueOf(job.getIdNumber()));
                    messageManager.sendMessage(finishedJobMessage, loadBalancerIpAddress, this.loadBalancerPortNumber);
                }
            }
        }

        //
        if (!messageManager.isStopped()) {
            //
            messageManager.stop();
        }

        System.out.println("NodeClient - INFO: Stopped");
    }
    
    private void handleMessage(MessageInbound message) throws IllegalArgumentException {
        switch (message.getType()) {
            case NEW_JOB -> {
                if (message.getParameters().length < 2) { throw new IllegalArgumentException("Insufficient Message parameters"); }
                
                //
                int jobIdNumber = -1;
                try {
                    jobIdNumber = Integer.parseInt(message.getParameter(0));
                } catch (NumberFormatException e) {
                    //
                    MessageOutbound newJobFailureMessage = new MessageOutbound(MessageOutboundType.NEW_JOB_FAILURE, "Job ID Number is not an Integer");
                    messageManager.sendMessage(newJobFailureMessage, loadBalancerIpAddress, loadBalancerPortNumber);
                    
                    throw new IllegalArgumentException("Job ID Number is not an Integer");
                }
                
                //
                int jobExecutionTime = -1;
                try {
                    jobExecutionTime = Integer.parseInt(message.getParameter(1));
                } catch (NumberFormatException e) {
                    //
                    MessageOutbound newJobFailureMessage = new MessageOutbound(MessageOutboundType.NEW_JOB_FAILURE, "Job Execution Time is not an Integer");
                    messageManager.sendMessage(newJobFailureMessage, loadBalancerIpAddress, loadBalancerPortNumber);
                    
                    throw new IllegalArgumentException("Job Execution Time is not an Integer");
                }
                
                //
                jobManager.startJob(jobIdNumber, jobExecutionTime);
                
                //
                MessageOutbound newJobSuccessMessage = new MessageOutbound(MessageOutboundType.NEW_JOB_SUCCESS);
                messageManager.sendMessage(newJobSuccessMessage, loadBalancerIpAddress, loadBalancerPortNumber);
                
                break;
            }
            case REG_NODE_SUCCESS -> {
                if (message.getParameters().length < 1) { throw new IllegalArgumentException("Insufficient Message parameters"); }
                
                //
                try {
                    nodeIdNumber = Integer.parseInt(message.getParameter(0));
                } catch (NumberFormatException e) {
                    throw new IllegalArgumentException("Node ID Number is not an Integer");
                }
                
                System.out.printf("NodeClient - INFO: Node ID Number set to %d\n", nodeIdNumber);
                
                break;
            }
            case REG_NODE_FAILURE -> {
                //
                running = false;
                
                //
                messageManager.stop();
                
                System.err.println("NodeClient - ERROR: Failed to register with Load-Balancer");
                
                break;
            }
            case NOT_REGISTERED -> {
                //
                jobManager.stopAllJobs();
                
                //
                register();
                
                break;
            }
            case IS_ALIVE -> {
                //
                MessageOutbound isAliveConfirmationMessage = new MessageOutbound(MessageOutboundType.ACK_IS_ALIVE);
                messageManager.sendMessage(isAliveConfirmationMessage, loadBalancerIpAddress, loadBalancerPortNumber);
                
                break;
            }
            case STOP_NODE -> {
                
                //
                running = false;
                
                //
                messageManager.stop();
                
                // 
                jobManager.stopAllJobs();
                
                break;
            }
            default -> throw new AssertionError();
        }
    }
    
    private void register() {
        //
        MessageOutbound registrationMessage = new MessageOutbound(MessageOutboundType.REG_NODE, nodeIpAddress.getHostAddress(), String.valueOf(nodePortNumber), String.valueOf(nodeCapacity));
        messageManager.sendMessage(registrationMessage, loadBalancerIpAddress, loadBalancerPortNumber);
    }
}