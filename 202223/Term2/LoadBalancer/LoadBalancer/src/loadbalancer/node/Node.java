package loadbalancer.node;

import java.net.InetAddress;
import java.net.UnknownHostException;
import loadbalancer.managers.JobManager;

public class Node {
    
    // Node infomation properties
    private final int idNum;
    private final int maxCapacity;
    private InetAddress ipAddress;
    private int portNumber;

    public Node(int idNum, InetAddress ipAddress, int portNumber, int maxCapacity) {
        this.idNum = idNum;
        this.maxCapacity = maxCapacity;
        
        this.ipAddress = ipAddress;
        this.portNumber = portNumber;
    }
    
    public int getIdNum() {
        return this.idNum;
    }
    
    public InetAddress getIpAddr() {
        return ipAddress;
    }
    
    public int getPortNum() {
        return portNumber;
    }
    
    public int getMaxCapacity() {
        return maxCapacity;
    }
    
    public float getUsage() {
        // Calculate and return active Jobs / maximum Capacity * 100
        return (JobManager.getInstance().getNumberOfNodeJobs(this) / maxCapacity) * 100;
    }
    
    private void setIpAddress(String ipAddress) throws IllegalArgumentException {
        try {
            this.ipAddress = InetAddress.getByName(ipAddress);
        } catch (UnknownHostException e) {
            throw new IllegalArgumentException(String.format(
                    "IP Address \"%s\" is not recognised.",
                    ipAddress
            ));
        }
    }
    
    private void setPortNumber(int portNumber) throws IllegalArgumentException {
        if (portNumber < 1 || portNumber >= 65535) {
            throw new IllegalArgumentException(String.format(
                    "Port \"%s\" is outside of the valid range.", 
                    portNumber
            ));
        } else {
            this.portNumber = portNumber;
        }
    }
}
