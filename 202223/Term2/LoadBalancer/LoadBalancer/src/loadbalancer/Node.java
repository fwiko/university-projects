package loadbalancer;

import java.net.Inet4Address;

public class Node {
    private int idNum;
    private Inet4Address ipAddr;
    private short portNum;
    private int maximumJobs;

    public void Node(int idNum, Inet4Address ipAddr, short portNum, int maximumJobs) {
        this.idNum = idNum;
        this.ipAddr = ipAddr;
        this.portNum = portNum;
        this.maximumJobs = maximumJobs;
    }
    
    public int getIdNum() {
        return this.idNum;
    }
    
    public Inet4Address getIpAddr() {
        return this.ipAddr;
    }
    
    public int getPortNum() {
        return this.portNum;
    }
    
    public int getMaximumJobs() {
        return this.maximumJobs;
    }
    
    public float getUsage() {
        return 1 / this.maximumJobs * 100;
    }
}

