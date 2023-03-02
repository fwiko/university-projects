package loadbalancer.managers;

import java.net.InetAddress;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import loadbalancer.node.Node;

public class NodeManager {
    private static NodeManager instance;
    
    private final ArrayList<Node> registeredNodes;
    private final HashMap<Node, Integer> nodeWarnings;
    
    private final Object registeredNodesLock = new Object();
    
    private int nextNodeId = 1;
    
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
    
    public Node registerNode(InetAddress ipAddress, int portNumber, int maxCapacity) {
        // Attempt to create a new Node object with the given IP Address, Port Number, and Maximum Capacity
        Node newNode = null;
        newNode = new Node(nextNodeId, ipAddress, portNumber, maxCapacity);
        
        // Add the new Node to the list of Nodes and increment the next Node ID value
        registeredNodes.add(newNode);
        nextNodeId += 1;
        nodeWarnings.put(newNode, 0);
        
        System.out.println(String.format("Node Manager (Info): Successfully registered Node %d on socket %s:%d", newNode.getIdNumber(), newNode.getIpAddr(), newNode.getPortNum()));
        
        return newNode;
    }
    
    public void removeNode(int idNumber) {
        synchronized (registeredNodesLock) {
            // Iterate through the list of registered Nodes
            for (Node node : registeredNodes) {
                // if the Node object's ID matches the specified idNum - remove it from the list
                if (node.getIdNumber() == idNumber) {
                    // Remove the node with the specified ID number from the list of registered Nodes
                    registeredNodes.remove(node);
                    // Remove the node with the specified ID number from the Node warnings HashMap
                    nodeWarnings.remove(node);
                }
            }
        }
    }
    
    public Node getNextNode() {
        // If the list of registered Nodes is not empty
        if (!registeredNodes.isEmpty()) {
            synchronized (registeredNodesLock) {
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
        synchronized (registeredNodesLock) {
            // Iterate through the list of registered Nodes
            for (Node node : registeredNodes) {
                // if the Node object's ID matches the specified idNum - return the Node
                if (node.getIdNumber() == idNumber) {
                    return node;
                }
            }
        }
        // If no node has the specified ID - return null
        return null;
    }
    
    private void sortNodes() {
        // Sort the list of registered Nodes based on the usage metric
        Collections.sort(registeredNodes, (Node n1, Node n2) -> {
            if (n1.getUsage() != n2.getUsage()) {
                // Usage metrics are Floats and cannot be returned from Collections.sort - must return 1 or -1 flag instead
                return n1.getUsage() > n2.getUsage() ? 1 : -1; 
            }
            // If the usage is identical - sort based on Maximum Capacity of the Nodes
            return n1.getMaxCapacity() - n2.getMaxCapacity();
        });
    }
    
    public int getNodeWarnings(Node node) {
        // Return the number of warnings a Node has been given
        return nodeWarnings.getOrDefault(node, 0);
    }
    
    public void resetNodeWarnings(Node node) {
        // Reset a Node's warnings to zero (0)
        nodeWarnings.put(node, 0);
    }
    
    public void incrementNodeWarnings(Node node) {
        // Increment a Node's warnings by one (1)
        nodeWarnings.put(node, getNodeWarnings(node) + 1);
    }
    
}
