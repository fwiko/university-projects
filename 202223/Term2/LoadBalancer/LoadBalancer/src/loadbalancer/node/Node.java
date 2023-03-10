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
    private final int idNumber;
    private final int maximumCapacity;
    private final InetAddress ipAddress;
    private final int portNumber;
    
    private MessageManager messageManager = null;
    private JobManager jobManager = null;
    private NodeManager nodeManager = null;
    
    private int warnings = 0;
    
    private Timer keepAliveTimer = null;
    
    public Node(int idNumber, InetAddress ipAddress, int portNumber, int maximumCapacity) {
        this.idNumber = idNumber;
        this.ipAddress = ipAddress;
        this.portNumber = portNumber;
        this.maximumCapacity = maximumCapacity;
        
        messageManager = MessageManager.getInstance();
        nodeManager = NodeManager.getInstance();
        // jobManager = JobManager.getInstance();
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
        return ((float) JobManager.getInstance().getNodeJobs(this).size() / maximumCapacity) * 100;
    }
    
    public void resetWarnings() {
        warnings = 0;
    }
    
    public void startKeepAlive() {
        keepAliveTimer = new Timer();
        
        keepAliveTimer.schedule(new TimerTask() {
            @Override
            public void run() {
                if (warnings >= 3) {
                    System.out.printf("Node %d - INFO: Failed to respond to 3 IS_ALIVE Messages - Unregistering", idNumber);
                    
                    unregister();
                    
                    stopKeepAlive();
                    
                    return;
                }
                
                messageManager.sendMessage(new MessageOutbound(MessageOutboundType.IS_ALIVE), ipAddress, portNumber);
                warnings += 1;
            }
        }, 30000, 30000);
    }
    
    public void stopKeepAlive() {
        keepAliveTimer.cancel();
        keepAliveTimer.purge();
    }
    
    private void unregister() {
        nodeManager.unregisterNode(this);
    }
}
