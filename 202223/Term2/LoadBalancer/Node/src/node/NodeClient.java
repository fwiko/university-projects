package node;

import java.io.IOException;
import java.net.InetAddress;
import node.managers.MessageManager;
import node.messages.MessageInbound;
import node.messages.MessageOutbound;
import node.messages.types.MessageOutboundType;


public class NodeClient {
    private static NodeClient instance = null;
    
    // Server switch used to stop operation loop when a STOP_SYSTEM Message is received
    private boolean running = true;
    private int nodeIdNumber = -1;
    
    // Load-Balancer Details
    private InetAddress loadBalancerIpAddress = null;
    private int loadBalancerPortNumber = -1;
    
    MessageManager messageManager = null;
    
    public static NodeClient getInstance() {
        // If the singleton instance already exists - return it
        if (instance != null) {
            return instance;
        }
        // Create a new instance and return it
        instance = new NodeClient();
        return instance;
    }
    
    public void start(int capacity, InetAddress nodeIpAddress, int nodePortNumber, InetAddress loadBalancerIpAddress, int loadBalancerPortNumber) throws IllegalArgumentException {
        // Validate Node and Load-Balancer Port Numbers
        if (nodePortNumber < 1 || nodePortNumber >= 65535) {
            throw new IllegalArgumentException(String.format(
                    "Node Port Number %d is outside of the assignable Port range",
                    nodePortNumber
            ));
        } else if (loadBalancerPortNumber < 1 || loadBalancerPortNumber >= 65535) {
            throw new IllegalArgumentException(String.format(
                    "Load-Balancer Port Number %d is outside of the assignable Port range",
                    nodePortNumber
            ));
        }
        
        this.loadBalancerIpAddress = loadBalancerIpAddress;
        this.loadBalancerPortNumber = loadBalancerPortNumber;
        
        messageManager = MessageManager.getInstance();
        
        try {
            messageManager.start(nodeIpAddress, nodePortNumber);
        } catch (IOException e) {
            System.out.println(e);
        }
        
        // Send REG_NODE Message to the Load-Balancer Socket to register with the Load-Balancer
        MessageOutbound registrationMessage = new MessageOutbound(MessageOutboundType.REG_NODE, nodeIpAddress.getHostAddress(), String.valueOf(nodePortNumber), String.valueOf(capacity));
        messageManager.sendMessage(registrationMessage, loadBalancerIpAddress, loadBalancerPortNumber);
        
        while (running) {
            // Retreive the next Message - from the Message Manager's Message queue
            MessageInbound nextMessage = messageManager.getNextMessage();
            
            if (nextMessage != null) {
                System.out.printf("Node Client (Info): Handling %s Message\n", nextMessage.getType().toString());
                
                try {
                    handleMessage(nextMessage);
                } catch (IllegalArgumentException e) {
                    System.err.printf("Node Client (Error): Failed to handle %s Message (%s)", nextMessage.getType().toString(), e.getMessage());
                }
            }
            
        }
    }
    
    private void handleMessage(MessageInbound message) throws IllegalArgumentException {
        switch (message.getType()) {
            case NEW_JOB -> {
                if (message.getParameters().length < 2) { throw new IllegalArgumentException("Insufficient Message parameters"); }
                break;
            }
            case REG_NODE_SUCCESS -> {
                if (message.getParameters().length < 1) { throw new IllegalArgumentException("Insufficient Message parameters"); }
                
                try {
                    nodeIdNumber = Integer.parseInt(message.getParameter(0));
                } catch (NumberFormatException e) { throw new IllegalArgumentException("Node ID Number is not an Integer"); }
                
                System.out.printf("Node Client (Info): Set Node ID Number to %d\n", nodeIdNumber);
                
                break;
            }
            case REG_NODE_FAILURE -> {
                break;
            }
            case IS_ALIVE -> {
                MessageOutbound isAliveConfirmationMessage = new MessageOutbound(MessageOutboundType.ACK_IS_ALIVE);
                messageManager.sendMessage(isAliveConfirmationMessage, loadBalancerIpAddress, loadBalancerPortNumber);
                
                break;
            }
            default -> throw new AssertionError();
        }
    
    }
}
