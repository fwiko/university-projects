package loadbalancer.node;

import java.net.InetAddress;
import java.util.Timer;
import java.util.TimerTask;
import loadbalancer.managers.JobManager;

public class Node {
    // Node details (socket, capacity, id)
    private final int idNumber;
    private final int maxCapacity;
    private final InetAddress ipAddress;
    private final int portNumber;
    
    // Warnings for no response to IS_ALIVE Messages
    private int warnings = 0;
    
    private Timer warningTimer = null;

    public Node(int idNum, InetAddress ipAddress, int portNumber, int maxCapacity) {
        this.idNumber = idNum;
        this.maxCapacity = maxCapacity;
        this.ipAddress = ipAddress;
        this.portNumber = portNumber;
        
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
                throw new UnsupportedOperationException("Not supported yet.");
            }
        }, 20, 20);
    }
}
