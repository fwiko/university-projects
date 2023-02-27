package loadbalancer.managers;

import java.util.ArrayList;
import java.util.HashMap;
import loadbalancer.node.Node;

public class NodeManager {
    private static NodeManager instance;
    
    private final ArrayList<Node> registeredNodes;
    private final HashMap<Node, Integer> nodeWarnings;
    
    private int nextNodeId = 1;
    
    private final Object mutexLock = new Object();
    
    private NodeManager() {
        this.registeredNodes = new ArrayList<>();
        this.nodeWarnings = new HashMap<>();
    }
    
    public static NodeManager getInstance() {
        if (instance != null) {
            return instance;
        }
        instance = new NodeManager();
        return instance;
    }
    
    public void registerNode(String ipAddress, int portNumber, int maxCapacity) {
        // Attempt to create a new Node object with the given IP Address, Port Number, and Maximum Capacity
        Node newNode = null;
        try {
            newNode = new Node(nextNodeId, ipAddress, portNumber, maxCapacity);
        } catch (IllegalArgumentException e) {
            System.out.println(String.format("Node Manager (Error): Failed to register new Node (%s)", e.getMessage()));
            return;
        }
        
        // Add the new Node to the list of Nodes and increment the next Node ID value
        registeredNodes.add(newNode);
        nextNodeId += 1;
        nodeWarnings.put(newNode, 0);
        
        System.out.println(String.format("Node Manager (Info): Registered Node %d from %s:%d", newNode.getIdNum(), newNode.getIpAddr(), newNode.getPortNum()));
    }
    
    public void removeNode(int idNumber) {
        synchronized (mutexLock) {
            // Iterate through the list of registered Nodes
            for (Node node : registeredNodes) {
                // if the Node object's ID matches the specified idNum - remove it from the list
                if (node.getIdNum() == idNumber) {
                    registeredNodes.remove(node);
                    nodeWarnings.remove(node);
                }
            }
        }
    }
    
    public Node getNextNode() {
        // If the list of registered Nodes is not empty
        if (!registeredNodes.isEmpty()) {
            synchronized (mutexLock) {
                // Sort the list of nodes by usage in ascending order
                sortNodes();
                // If the first element in the sorted list is at under 100% usage - return it
                if (registeredNodes.get(0).getUsage() < 100) {
                    return registeredNodes.get(0);
                }
            }
        }
        // If all Nodes are at 100% usage - return null
        return null;
    }
    
    public Node getNodeById(int idNumber) {
        synchronized (mutexLock) {
            // Iterate through the list of registered Nodes
            for (Node node : registeredNodes) {
                // if the Node object's ID matches the specified idNum - return the Node
                if (node.getIdNum() == idNumber) {
                    return node;
                }
            }
        }
        return null;
    }
    
    private void sortNodes() {
        registeredNodes.sort((n1, n2) -> Float.compare(n1.getUsage(), n2.getUsage()));
    }
    
    public void resetWarnings(Node node) {
        nodeWarnings.put(node, 0);
    }
    
    public void incrementWarnings(Node node) {
        nodeWarnings.put(node, nodeWarnings.getOrDefault(node, 0) + 1);
    }
}
