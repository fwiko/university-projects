package loadbalancer.node;

import java.net.InetAddress;
import java.util.Timer;
import java.util.TimerTask;
import loadbalancer.managers.JobManager;
import loadbalancer.managers.MessageManager;
import loadbalancer.managers.NodeManager;
import loadbalancer.messages.MessageOutbound;
import loadbalancer.messages.types.MessageOutboundType;

public class Node {
    // Node details (socket, capacity, id)
    private final int idNumber;
    private final int maxCapacity;
    private final InetAddress ipAddress;
    private final int portNumber;
    
    private NodeManager nodeManager = null;
    private MessageManager messageManager = null;
    
    // Warnings for no response to IS_ALIVE Messages
    private int warnings = 0;
    
    private Timer warningTimer = null;

    public Node(int idNum, InetAddress ipAddress, int portNumber, int maxCapacity) {
        this.idNumber = idNum;
        this.maxCapacity = maxCapacity;
        this.ipAddress = ipAddress;
        this.portNumber = portNumber;
        
        nodeManager = NodeManager.getInstance();
        messageManager = MessageManager.getInstance();
    }
    
    public int getIdNumber() {
        // return the idNumber property
        return this.idNumber;
    }
    
    public InetAddress getIpAddr() {
        // return the ipAddress property
        return ipAddress;
    }
    
    public int getPortNum() {
        // return the portNumber property
        return portNumber;
    }
    
    public int getMaxCapacity() {
        // return the maxCapacity property
        return maxCapacity;
    }
    
    public float getUsage() {
        // Calculate and return the current usage of the Node
        return (JobManager.getInstance().getNumberOfNodeJobs(this) / maxCapacity) * 100;
    }

    public void keepAlive() {
        warningTimer = new Timer();
        
        warningTimer.schedule(new TimerTask() {
            @Override
            public void run() {
                if (warnings >= 3) {
                    System.out.printf("Node %d - INFO: Unregistering Node (Failed to respond to 3 IS_ALIVE Messages)\n", idNumber);
                    
                    // Leave timer instance and unregister Node from the NodeManager
                    unregisterSelf();
                    
                    // Cancel the keepAlive Timer loop
                    warningTimer.cancel();
                    warningTimer.purge();
                    return;
                }
                
                // Send an IS_ALIVE Message to the corresponding Node socket
                MessageOutbound isAliveMessage = new MessageOutbound(MessageOutboundType.IS_ALIVE);
                messageManager.sendMessage(isAliveMessage, ipAddress, portNumber);
                
                // Pre-emptively increment the Node warnings (will be reset upon receipt of an ACK_IS_ALIVE Message)
                warnings += 1;
            }
        }, 10000, 10000);
    }
    
    private void unregisterSelf() {
        // Unregister (remove) Node from the NodeManager
        nodeManager.unregisterNode(this);
    }
    
    public void resetWarnings() {
        // Reset Node's warnings to zero (0)
        warnings = 0;
        
    }
}
