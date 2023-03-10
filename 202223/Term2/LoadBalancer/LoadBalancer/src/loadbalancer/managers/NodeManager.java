package loadbalancer.managers;

import java.net.InetAddress;
import java.util.Collections;
import java.util.LinkedList;
import loadbalancer.AllocationAlgorithm;
import loadbalancer.node.Node;

public class NodeManager {
    private static NodeManager instance;
    
    private LinkedList<Node> registeredNodes = null;
    
    private int nextNodeIdNumber = 1;
    
    private int nextNodePointer = 0;
    
    private NodeManager() {
        this.registeredNodes = new LinkedList<>();
    }
    
    public static NodeManager getInstance() {
        if (instance != null) {
            return instance;
        }
        instance = new NodeManager();
        return instance;
    }
    
    public Node registerNode(InetAddress ipAddress, int portNumber, int maximumCapacity) {
        return null;
    }
    
    public void unregisterNode(Node node) {
        //
    }
    
    public Node getNextQualifyingNode(AllocationAlgorithm allocationAlgorithm) {
        return null;
    }
    
    public Node getNodeById(int idNumber) {
        return null;
    }
    
    public void resetNodeWarnings(Node node) {
        node.resetWarnings();
    }
    
    public LinkedList<Node> getNodes() {
        return registeredNodes;
    }
    
    private void sortNodes() {
        Collections.sort(registeredNodes, (Node n1, Node n2) -> {
            if (n1.getCurrentUsage() != n2.getCurrentUsage()) {
                return n1.getCurrentUsage() > n2.getCurrentUsage() ? 1 : -1;
            }
            
            return n2.getMaximumCapacity() - n1.getMaximumCapacity();
        });
    }
    
    
}
