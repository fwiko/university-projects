package loadbalancer.managers;

import java.net.InetAddress;
import java.util.Collections;
import java.util.LinkedList;
import loadbalancer.AllocationAlgorithm;
import loadbalancer.job.Job;
import loadbalancer.node.Node;

public class NodeManager {
    // Value holding the singleton instacne of the Node Manager
    private static NodeManager instance = null;
    
    // LinkedList storing all Nodes that are registered with the Load-Balancer
    private LinkedList<Node> registeredNodes = null;
    
    // Next Job ID Number to assign to a Job when one is registered
    private int nextNodeIdNumber = 1;
    
    // Pointer value used for the Round-Robin allocation algorithm
    private int nextNodePointer = 0;
    
    // Mutex object to allow exclusive access to the "registeredNodes" LinkedList
    private static final Object registeredNodesMutex = new Object();
    
    // 
    private JobManager jobManager = null;
    
    private NodeManager() {
        this.registeredNodes = new LinkedList<>();
        this.jobManager = JobManager.getInstance();
    }
    
    public static NodeManager getInstance() {
        // If there is no current instance of the Node Manager, create a new Instance
        if (instance == null) {
            instance = new NodeManager();
        }
        
        return instance;
    }
    
    public Node registerNode(InetAddress ipAddress, int portNumber, int maximumCapacity) {
        // Create a new Node object with the given details and next ID Number
        Node node = new Node(nextNodeIdNumber, ipAddress, portNumber, maximumCapacity);
        
        // Add the new Node object to the "registeredNodes" LinkedList
        registeredNodes.add(node);
        
        // Start the "Keep Alive" Timer/loop for the new Node
        node.startKeepAlive();
        
        System.out.printf("NodeManager - INFO: Registered Node %d with a maximum capacity of %d on socket %s:%d\n", 
                node.getIdNumber(), node.getMaximumCapacity(), node.getIpAddress().getHostAddress(), node.getPortNumber());
        
        // Increment the next Node ID Number value by 1
        nextNodeIdNumber += 1;
        
        return node;
    }
    
    public void unregisterNode(Node node) {
        // Aquire the "registeredNodesMutex" Mutex
        synchronized (registeredNodesMutex) {
            // Remove the given Node from the "registeredNodes" LinkedList
            registeredNodes.remove(node);
        }
        
        System.out.printf("NodeManager - INFO: Un-registered Node %d\n", node.getIdNumber());
        
        // Get all Jobs allocated to the given Node
        LinkedList<Job> allocatedJobs = jobManager.getNodeJobs(node);
        
        // De-allocate and requeue all Jobs allocated to the given Node
        for (Job job : allocatedJobs) {
            jobManager.deallocateJob(job);
            jobManager.queueJob(job);
        }
        
    }
    
    public Node getNextQualifyingNode(AllocationAlgorithm allocationAlgorithm) {
        // Return null if the "registeredNodes" LinkedList is empty
        if (registeredNodes.isEmpty()) { return null; }
        
        Node node = null;
        
        // Aquire the "registeredNodesMutex" Mutex
        synchronized (registeredNodesMutex) {
            switch (allocationAlgorithm) {
                case NORMAL -> { // If the specified Allocation Algorithm is NORMAL
                    
                    // Loop registeredNodes length times
                    for (int i = 0; i < registeredNodes.size(); i++) {
                        
                        // If the Node at position "nextNodePointer" has a usage below 100%
                        if (registeredNodes.get(nextNodePointer).getCurrentUsage() < 100) {
                            // Set the "node" value to the Node object at the current position
                            node = registeredNodes.get(nextNodePointer);
                            
                            // Increment the "nextNodePointer" value using modulo to reset to zero in "cyclic" fashion
                            nextNodePointer = (nextNodePointer + 1) % registeredNodes.size();
                            break;
                        }
                        
                        // Increment the "nextNodePointer" value using modulo to reset to zero in "cyclic" fashion
                        nextNodePointer = (nextNodePointer + 1) % registeredNodes.size();
                    }
                    
                    break;
                    
                }
                case WEIGHTED -> { // If the specified Allocation Algorithm is WEIGHTED
                    
                    // Sort the "registeredNodes" LinkedList in ascending order based on current usage
                    sortNodes();
                    
                    // If the Node object at position zero has a usage below 100%
                    if (registeredNodes.get(0).getCurrentUsage() < 100) {
                        // set the "node" value to the Node object at position zero
                        node = registeredNodes.get(0);
                    }
                    
                    break;
                    
                }
                default -> { // If an "illegal" or invalid Allocation Algorithm has been specified
                    throw new IllegalArgumentException("Unknown Allocation Algorithm type");
                }
            }
        }
        
        return node;
    }
    
    public Node getNodeById(int idNumber) {
        // Aquire the "registeredNodesMutex" Mutex
        synchronized (registeredNodesMutex) {
            // Iterate through the "registeredNodes" LinkedList
            for (Node node : registeredNodes) {
                // If the current Node object's ID Number equals the one specified, return the Node object
                if (node.getIdNumber() == idNumber) {
                    return node;
                }
            }
        }
        
        // Return null if no match was found
        return null;
    }
    
    public LinkedList<Node> getNodes() {
        return registeredNodes;
    }
    
    public String[] getNodeSummaries() {
        // Create a String-array with the same length of the list of registered Nodes
        String[] nodeSummaries = new String[registeredNodes.size()];
        
        // Add a string detailing the ID Number, Allocated Jobs, and Usage of each Node to the above array
        for (int i = 0; i < registeredNodes.size(); i++) {
            Node node = registeredNodes.get(i);
            nodeSummaries[i] = String.format(
                    "%d,%d,%f", 
                    node.getIdNumber(), 
                    jobManager.getNodeJobs(node).size(),
                    node.getCurrentUsage());
        }
        
        return nodeSummaries;
    }
    
    private void sortNodes() {
        // Use Collections to compare each Node object in the "registeredNodes" LinkedList
        Collections.sort(registeredNodes, (Node n1, Node n2) -> {
            // If "Node A" has a different usage to "Node B"
            if (n1.getCurrentUsage() != n2.getCurrentUsage()) {
                // Return 1 if "Node A" has a usage greater than "Node B" else return -1 (positive or negative integers to define sorting positions - usage is a float an cannot be used)
                return n1.getCurrentUsage() > n2.getCurrentUsage() ? 1 : -1;
            }
            
            // If the usage of "Node A" and "Node B" is the same, sort based on the maximum capacity of the Nodes
            return n2.getMaximumCapacity() - n1.getMaximumCapacity();
        });
    }
    
    
}
