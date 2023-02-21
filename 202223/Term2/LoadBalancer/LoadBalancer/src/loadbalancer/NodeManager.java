package loadbalancer;

import java.util.LinkedHashMap;

public class NodeManager {
    private LinkedHashMap<Node, Integer> nodes;
    
    public NodeManager() {
        this.nodes = new LinkedHashMap<>();
    }
    
}
