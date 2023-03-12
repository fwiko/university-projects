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
    // Unique ID Number of the Node used to identify it
    private final int idNumber;
    
    // Maximum capacity of the Node - used to control possible Job allocations and calculate usage
    private final int maximumCapacity;
    
    // Node socket details
    private final InetAddress ipAddress;
    private final int portNumber;
    
    // Message and Node Manager singletons
    private MessageManager messageManager = null;
    private NodeManager nodeManager = null;
    
    // Integer value used to track the Node's warnings (maximum 3)
    private int warnings = 0;
    
    // Timer used to send a IS_ALIVE Message to the Node socket every 30 seconds
    private Timer keepAliveTimer = null;
    
    public Node(int idNumber, InetAddress ipAddress, int portNumber, int maximumCapacity) {
        this.idNumber = idNumber;
        this.ipAddress = ipAddress;
        this.portNumber = portNumber;
        this.maximumCapacity = maximumCapacity;
        
        messageManager = MessageManager.getInstance();
        nodeManager = NodeManager.getInstance();
    }
    
    public int getIdNumber() {
        return idNumber;
    }
    
    public InetAddress getIpAddress() {
        return ipAddress;
    }
    
    public int getPortNumber() {
        return portNumber;
    }
    
    public int getMaximumCapacity() {
        return maximumCapacity;
    }
    
    public float getCurrentUsage() {
        // Current Capacity / Maximum Capacity * 100
        return ((float) JobManager.getInstance().getNodeJobs(this).size() / maximumCapacity) * 100;
    }
    
    public void resetWarnings() {
        warnings = 0;
    }
    
    public void startKeepAlive() {
        // Create a new Timer object
        keepAliveTimer = new Timer();
        
        // Schedule the Timer to send a IS_ALIVE Message to the Node socket every 30000 milliseconds (30 seconds)
        keepAliveTimer.schedule(new TimerTask() {
            @Override
            public void run() {
                if (warnings >= 3) { // If the "warnings" value is greater than or equal to 3
                    System.out.printf("Node %d - INFO: Failed to respond to 3 IS_ALIVE Messages - Unregistering", idNumber);
                    
                    // Unregister the Node (remove from Node Manager)
                    unregister();
                    
                    // Stop (this) keep alive timer
                    stopKeepAlive();
                    
                    return;
                }
                
                messageManager.sendMessage(new MessageOutbound(MessageOutboundType.IS_ALIVE), ipAddress, portNumber);
                
                // Increment the "warnings" value by 1
                warnings += 1;
            }
        }, 30000, 30000);
    }
    
    public void stopKeepAlive() {
        // Cancel and clear the "keepAliveTimer" Timer
        keepAliveTimer.cancel();
        keepAliveTimer.purge();
    }
    
    private void unregister() {
        // Unregister the Node from the Node Manager
        nodeManager.unregisterNode(this);
    }
}
