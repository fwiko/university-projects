package loadbalancer.managers;

import java.net.InetAddress;
import java.util.ArrayList;
import java.util.Collections;
import loadbalancer.node.Node;

public class NodeManager {
    private static NodeManager instance;
    
    private final ArrayList<Node> registeredNodes;
    
    private final Object registeredNodesLock = new Object();
    
    private int nextNodeId = 1;
    
    private NodeManager() {
        this.registeredNodes = new ArrayList<>();
    }
    
    public static NodeManager getInstance() {
        if (instance != null) {
            return instance;
        }
        instance = new NodeManager();
        return instance;
    }
    
    public Node registerNode(InetAddress ipAddress, int portNumber, int maxCapacity) {
        // Create a new Node object with the given IP Address, Port Number, and Maximum Capacity
        Node newNode = new Node(nextNodeId, ipAddress, portNumber, maxCapacity);
        // Add the new Node to the list of registered Nodes
        registeredNodes.add(newNode);
        // Increment the nextNodeID value preparing for the next Node registration
        nextNodeId += 1;
        // Start the keep alive Timer loop for the new Node to send IS_ALIVE Messages
        newNode.keepAlive();
        
        System.out.printf("NodeManager - INFO: Registered Node %d on socket %s:%d\n", newNode.getIdNumber(), newNode.getIpAddr().getHostAddress(), newNode.getPortNum());
        return newNode;
    }
    
    public void unregisterNode(Node node) {
        synchronized (registeredNodesLock) {
            // Remove the specified Node object from the list of registered Nodes
            registeredNodes.remove(node);
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
    
    public void resetNodeWarnings(Node node) {
        // Reset a Node's warnings to zero (0)
        node.resetWarnings();
    }
    
    public ArrayList<Node> getNodes() {
        return registeredNodes;
    }
}
