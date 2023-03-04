package loadbalancer.managers;

import java.net.InetAddress;
import java.util.ArrayList;
import java.util.Collections;
import loadbalancer.AllocationMethod;
import loadbalancer.node.Node;

public class NodeManager {
    private static NodeManager instance;
    
    private final ArrayList<Node> registeredNodes;
    
    private final Object registeredNodesLock = new Object();
    
    private int nextNodeId = 1;
    
    // Pointer used for Round-Robin AllocationMethod
    private int roundRobinPointer = 0;
    
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
    
    public Node getNextNode(AllocationMethod allocationMethod) {
        // If the list of registered Nodes is not empty
        if (!registeredNodes.isEmpty()) {
            synchronized (registeredNodesLock) {
                Node node = null;
                switch (allocationMethod) {
                    case NORMAL -> {
                        // If the node at the last point of reference is available - return it
                        if (registeredNodes.get(roundRobinPointer).getUsage() < (float) 100) {
                            node = registeredNodes.get(roundRobinPointer);
                            
                            // Set roundRobinPointer to next position if circular loop
                            roundRobinPointer = (roundRobinPointer + 1) % registeredNodes.size();
                            break;
                        }
                        
                        // Do a full "circular" iteration of the registeredNodes list from the last point of reference
                        for (int i = 0; i < registeredNodes.size(); i++) {
                            // Use modulo to normalise the roundRobinPointer value (reset to 0 if hits list length) to get next roundRobinPointer position
                            roundRobinPointer = roundRobinPointer++ % registeredNodes.size();
                            
                            // If the current node is under 100% usage - return it
                            if (registeredNodes.get(roundRobinPointer).getUsage() < (float) 100) {
                                node = registeredNodes.get(roundRobinPointer);
                                
                                // Set roundRobinPointer to next position if circular loop
                                roundRobinPointer = (roundRobinPointer + 1) % registeredNodes.size();
                                break;
                            }
                        }
                        
                        break;
                    }
                    case WEIGHTED -> {
                        // Sort the list of nodes by usage in ascending order
                        sortNodes();
                        
                        // If the first element in the sorted list is at under 100% usage - return it
                        if (registeredNodes.get(0).getUsage() < 100) {
                            node = registeredNodes.get(0);
                        }
                        
                        break;
                    }
                }
                return node;
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
            return n2.getMaxCapacity() - n1.getMaxCapacity();
        });
    }
    
    public void resetNodeWarnings(Node node) {
        // Reset a Node's warnings to zero (0)
        node.resetWarnings();
    }
    
    public ArrayList<Node> getNodes() {
        return registeredNodes;
    }
    
    public String getNodeSummary() {
        String summaryString = "";
        
        synchronized (registeredNodes) {
            for ( Node node : registeredNodes ) {
                summaryString += String.format("Node %d: %f%% Usage\n", node.getIdNumber(), node.getUsage());
            }
        }
        
        return summaryString;
    }
}
